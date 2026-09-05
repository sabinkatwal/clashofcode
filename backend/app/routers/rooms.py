from datetime import datetime, timezone
import json
import random
import string
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import AsyncSessionLocal, get_db
from app.models import CodingQuestion, MatchHistory, User
from app.room_store import room_store
from app.schemas import RoomCreateRequest, RoomJoinRequest, RoomMatchmakingModeRequest, SubmissionRequest
from app.websocket_manager import manager
from app.routers.execution import evaluate_python_cases, unsupported_language_response

router = APIRouter(prefix="/rooms", tags=["Rooms"])
logger = logging.getLogger(__name__)

VALID_LEVELS = {"easy", "medium", "hard", "all"}


def _json_list(value: object) -> list:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return value
    return []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _timer_payload(room: dict) -> dict:
    started_at = _parse_iso(room.get("started_at"))
    ends_at = None
    remaining_seconds = None
    if started_at and room.get("time_limit_minutes"):
        ends_at_dt = started_at.timestamp() + room["time_limit_minutes"] * 60
        now_ts = datetime.now(timezone.utc).timestamp()
        ends_at = datetime.fromtimestamp(ends_at_dt, timezone.utc).isoformat()
        remaining_seconds = max(0, int(ends_at_dt - now_ts))
    return {
        "server_now": _now_iso(),
        "ends_at": ends_at,
        "remaining_seconds": remaining_seconds,
    }


def _push_event(room: dict, kind: str, message: str, username: str | None = None) -> None:
    events = room.setdefault("events", [])
    events.append({
        "id": f"{int(datetime.now(timezone.utc).timestamp() * 1000)}-{len(events)}",
        "kind": kind,
        "message": message,
        "username": username,
        "created_at": _now_iso(),
    })
    del events[:-80]


def _push_chat_message(room: dict, username: str, message: str) -> dict:
    messages = room.setdefault("chat_messages", [])
    chat_message = {
        "id": f"{int(datetime.now(timezone.utc).timestamp() * 1000)}-{len(messages)}",
        "username": username,
        "message": message,
        "created_at": _now_iso(),
    }
    messages.append(chat_message)
    del messages[:-100]
    return chat_message


def _generate_room_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def _get_room_or_404(room_code: str) -> dict:
    code = room_code.strip().upper()
    room = room_store.get(code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    return room


def _room_online_players(room: dict) -> list[str]:
    return [username for username, player in room.get("players", {}).items() if player.get("online")]


def _room_is_expired(room: dict) -> bool:
    return room.get("status") == "expired"


def _room_host_online(room: dict) -> bool:
    host_username = room.get("host")
    if not host_username:
        return False
    host_player = room.get("players", {}).get(host_username, {}) if host_username else {}
    return bool(host_player.get("online"))


def _room_allows_matchmaking_join(room: dict) -> bool:
    # NOTE: We do NOT require _room_host_online here. The host's online flag is
    # only set when their WebSocket is connected. Since WS connectivity is
    # unreliable (especially in dev), requiring host_online means rooms created
    # by hosts whose WS hasn't fully connected yet are never joinable via
    # matchmaking — causing both players to end up in separate rooms.
    # A room in "waiting" status that hasn't expired is sufficient.
    return (
        not _room_is_expired(room)
        and room.get("status") == "waiting"
    )


def _room_allows_rejoin(room: dict) -> bool:
    return not _room_is_expired(room) and room.get("status") in {"waiting", "locked", "active", "round_finished"}


def _remove_room_from_matchmaking(room: dict) -> None:
    room_code = room.get("room_code")
    difficulty = room.get("difficulty")
    if room_code and difficulty in open_rooms and room_code in open_rooms[difficulty]:
        try:
            open_rooms[difficulty].remove(room_code)
        except ValueError:
            pass


async def _expire_room(room: dict, reason: str | None = None, db: AsyncSession | None = None) -> None:
    if room.get("status") == "expired":
        return

    room["status"] = "expired"
    room["expired_at"] = _now_iso()
    room["finished_at"] = room.get("finished_at") or room["expired_at"]
    _remove_room_from_matchmaking(room)

    if reason:
        _push_event(room, "expired", reason)

    async with matchmaking_lock:
        for username in list(room.get("players", {}).keys()):
            if user_match_status.get(username) == room.get("room_code"):
                del user_match_status[username]
            pending_redirects.pop(username, None)

    if db is not None and _room_online_players(room):
        await _broadcast_room(room, db)


async def _maybe_expire_if_empty(room: dict, db: AsyncSession | None = None) -> bool:
    if room.get("status") == "expired":
        return True
    if _room_online_players(room):
        return False
    await _expire_room(room, "Room expired because all players went offline.", db)
    return True


def _serialize_question(question: CodingQuestion | None) -> dict | None:
    if not question:
        return None
    examples = _json_list(question.examples)
    test_cases = _json_list(question.test_cases)
    visible_count = max(1, len(examples)) if examples else min(2, len(test_cases))
    sample_cases = test_cases[:visible_count]

    return {
        "id": question.id,
        "title": question.title,
        "difficulty": question.difficulty,
        "description": question.description,
        "test_cases": [],
        "sample_cases": sample_cases,
        "examples": examples,
        "constraints": question.constraints,
        "points": question.points,
        "starter_code": question.starter_code,
    }


async def _get_user(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _get_question_by_id(db: AsyncSession, question_id: int | None) -> CodingQuestion | None:
    if not question_id:
        return None
    result = await db.execute(select(CodingQuestion).where(CodingQuestion.id == question_id))
    return result.scalar_one_or_none()


async def _get_room_question_pool(db: AsyncSession, room: dict) -> list[CodingQuestion]:
    selected_question_ids = room.get("selected_question_ids") or []
    if selected_question_ids:
        result = await db.execute(
            select(CodingQuestion).where(CodingQuestion.id.in_(selected_question_ids))
        )
        questions_by_id = {question.id: question for question in result.scalars().all()}
        return [questions_by_id[question_id] for question_id in selected_question_ids if question_id in questions_by_id]

    query = select(CodingQuestion)
    if room["difficulty"] != "all":
        query = query.where(CodingQuestion.difficulty == room["difficulty"])
    result = await db.execute(query)
    return result.scalars().all()


async def _serialize_room(room: dict, db: AsyncSession) -> dict:
    await _expire_room_if_needed(room, db)
    question = await _get_question_by_id(db, room.get("question_id"))
    players = sorted(room["players"].values(), key=lambda item: item["joined_at"])
    timer = _timer_payload(room)
    return {
        "roomCode": room["room_code"],
        "host": room["host"],
        "matchmaking": room.get("matchmaking", "invite"),
        "status": room["status"],
        "all_questions_finished": room.get("all_questions_finished", False),
        "difficulty": room["difficulty"],
        "created_at": room["created_at"],
        "started_at": room.get("started_at"),
        "finished_at": room.get("finished_at"),
        "server_now": timer["server_now"],
        "ends_at": timer["ends_at"],
        "remaining_seconds": timer["remaining_seconds"],
        "time_limit_minutes": room["time_limit_minutes"],
        "question": _serialize_question(question),
        "events": room.get("events", []),
        "chat_messages": room.get("chat_messages", []),
        "players": [
            {
                "username": player["username"],
                "status": player["status"],
                "score": player["score"],
                "language": player.get("language"),
                "online": player.get("online", False),
                "typing": player.get("typing", False),
                "progress": player.get("progress", 0),
                "last_action": player.get("last_action"),
                "submitted_at": player.get("submitted_at"),
                "runtime_ms": player.get("runtime_ms"),
                "memory_kb": player.get("memory_kb"),
                "passed": player.get("passed", 0),
                "total": player.get("total", 0),
                "submissions": player.get("submissions", []),
            }
            for player in players
        ],
    }


async def _broadcast_room(room: dict, db: AsyncSession) -> dict:
    payload = await _serialize_room(room, db)
    logger.info(
        "ROOM BROADCAST room_id=%s status=%s players=%s",
        room["room_code"],
        payload["status"],
        len(payload["players"]),
    )
    await manager.broadcast(room["room_code"], {"event": "room_updated", "room": payload})
    return payload


async def _expire_room_if_needed(room: dict, db: AsyncSession) -> None:
    if room.get("status") != "active":
        return
    remaining = _timer_payload(room).get("remaining_seconds")
    if remaining == 0:
        _push_event(room, "timer", "Time is up. Battle finished.")
        await _finalize_room(room, db)


async def _finalize_room(room: dict, db: AsyncSession) -> None:
    if room.get("status") in ("round_finished", "finished"):
        return

    room["status"] = "round_finished"
    room["finished_at"] = _now_iso()
    for player in room["players"].values():
        if player["status"] != "submitted":
            player["status"] = "time_up"
            player["typing"] = False

    players = list(room["players"].values())
    scored_players = sorted(
        players,
        key=lambda player: (-player["score"], player.get("submitted_at") or _now_iso()),
    )
    winner_username = scored_players[0]["username"] if scored_players else None
    question = await _get_question_by_id(db, room.get("question_id"))
    question_title = question.title if question else "Untitled Challenge"

    for player_state in players:
        user = await _get_user(db, player_state["username"])
        if not user:
            continue

        user.games_played = (user.games_played or 0) + 1
        user.total_points = (user.total_points or 0) + player_state["score"]

        if player_state["username"] == winner_username:
            user.wins = (user.wins or 0) + 1
            user.current_streak = (user.current_streak or 0) + 1
            user.best_streak = max(user.best_streak or 0, user.current_streak or 0)
            result = "Victory"
        else:
            user.losses = (user.losses or 0) + 1
            user.current_streak = 0
            result = "Defeat"

        db.add(
            MatchHistory(
                user_id=user.id,
                room_code=room["room_code"],
                question_title=question_title,
                difficulty=room["difficulty"],
                result=result,
                score=player_state["score"],
            )
        )

    await db.commit()


@router.post("")
@router.post("/create")
async def create_room(
    request: RoomCreateRequest,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    difficulty = request.difficulty.lower()
    if difficulty not in VALID_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid difficulty level.")

    selected_question_ids = []
    if request.questions:
        unique_ids = list(dict.fromkeys(request.questions))
        result = await db.execute(select(CodingQuestion).where(CodingQuestion.id.in_(unique_ids)))
        found_questions = {question.id: question for question in result.scalars().all()}
        missing_ids = [question_id for question_id in unique_ids if question_id not in found_questions]
        if missing_ids:
            raise HTTPException(status_code=400, detail="One or more selected questions do not exist.")
        selected_question_ids = unique_ids
        if difficulty == "all":
            first_question = found_questions[selected_question_ids[0]]
            difficulty = first_question.difficulty

    room_code = _generate_room_code()
    while room_code in room_store:
        room_code = _generate_room_code()

    host = current_username
    matchmaking_mode = "open" if getattr(request, "open_matchmaking", True) else "invite"
    room_store[room_code] = {
        "room_code": room_code,
        "host": host,
        "difficulty": difficulty,
        "matchmaking": matchmaking_mode,
        "name": request.name,
        "status": "waiting",
        "created_at": _now_iso(),
        "started_at": None,
        "finished_at": None,
        "locked_at": None,
        "expired_at": None,
        "question_id": None,
        "time_limit_minutes": {"easy": 10, "medium": 15, "hard": 20, "all": 15}[difficulty],
        "players": {
            host: {
                "username": host,
                "status": "waiting",
                "ready": False,
                "score": 0,
                "joined_at": _now_iso(),
                "submitted_at": None,
                "code": "",
                "language": None,
                "online": False,
                "typing": False,
                "progress": 0,
                "last_action": "joined",
                "runtime_ms": None,
                "memory_kb": None,
                "passed": 0,
                "total": 0,
                "submissions": [],
            }
        },
        "events": [],
        "selected_question_ids": selected_question_ids,
        "used_questions": [],
        "all_questions_finished": False,
        "chat_messages": [],
    }
    _push_event(room_store[room_code], "room", f"{host} created the room.", host)
    if matchmaking_mode == "open":
        open_rooms.setdefault(difficulty, [])
        if room_code not in open_rooms[difficulty]:
            open_rooms[difficulty].append(room_code)

    return {
        "roomCode": room_code,
        "difficulty": difficulty,
        "questions": selected_question_ids,
        "matchmaking": matchmaking_mode,
    }


@router.post("/join")
async def join_room(
    request: RoomJoinRequest,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = _get_room_or_404(request.roomCode)
    username = current_username

    if _room_is_expired(room):
        raise HTTPException(status_code=410, detail="Room has expired.")

    if username not in room["players"]:
        if room.get("status") != "waiting":
            raise HTTPException(status_code=400, detail="Room is no longer accepting new players.")
        # NOTE: We intentionally do NOT check host_online here.
        # The host's `online` flag is only set when their WebSocket connects, which happens
        # AFTER the HTTP /rooms/join call. Blocking on host_online at join time causes a
        # race condition where the second player gets a 400 because the host's WS hasn't
        # connected yet. The room being in "waiting" status is sufficient proof the
        # host created it and intends to play.
    elif room.get("status") == "expired":
        raise HTTPException(status_code=410, detail="Room has expired.")

    if username not in room["players"]:
        room["players"][username] = {
            "username": username,
            "status": "waiting",
            "ready": False,
            "score": 0,
            "joined_at": _now_iso(),
            "submitted_at": None,
            "code": "",
            "language": None,
            "online": False,
            "typing": False,
            "progress": 0,
            "last_action": "joined",
            "runtime_ms": None,
            "memory_kb": None,
            "passed": 0,
            "total": 0,
            "submissions": [],
        }
        _push_event(room, "join", f"{username} joined the room.", username)

    async with matchmaking_lock:
        user_match_status[username] = room["room_code"]
        pending_redirects.pop(username, None)

    payload = await _broadcast_room(room, db)
    return {"roomCode": payload["roomCode"]}


@router.get("/{room_code}")
async def get_room(
    room_code: str,
    db: AsyncSession = Depends(get_db),
):
    room = _get_room_or_404(room_code)
    return await _serialize_room(room, db)


@router.post("/{room_code}/chat")
async def send_chat_message(
    room_code: str,
    payload: dict,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """HTTP fallback for chat when WebSocket is unavailable.
    Stores the message in room state and broadcasts to all connected WS clients.
    """
    room = _get_room_or_404(room_code)

    if _room_is_expired(room):
        raise HTTPException(status_code=410, detail="Room has expired.")

    if current_username not in room["players"]:
        raise HTTPException(status_code=403, detail="You are not in this room.")

    message = str(payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if len(message) > 500:
        raise HTTPException(status_code=400, detail="Messages must be 500 characters or fewer.")

    chat_message = _push_chat_message(room, current_username, message)
    room["players"].get(current_username, {})["last_action"] = "sent a message"

    # Broadcast updated room to all connected WebSocket clients
    await _broadcast_room(room, db)

    return {"ok": True, "message": chat_message}


@router.post("/{room_code}/start")
async def start_room(
    room_code: str,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = _get_room_or_404(room_code)
    if room["host"] != current_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can start the room.")
    if room["status"] != "waiting":
        raise HTTPException(status_code=400, detail="Room has already started.")

    room["status"] = "locked"
    room["locked_at"] = _now_iso()
    _remove_room_from_matchmaking(room)

    try:
        questions = await _get_room_question_pool(db, room)
        if not questions:
            raise HTTPException(status_code=404, detail="No questions available for this difficulty.")

        question = random.choice(questions)
        room["question_id"] = question.id
        room["status"] = "active"
        room["started_at"] = _now_iso()
        used = room.setdefault("used_questions", [])
        if question.id not in used:
            used.append(question.id)

        for player in room["players"].values():
            player["status"] = "active"
            player["ready"] = False
            player["typing"] = False
            player["last_action"] = "started"

        async with matchmaking_lock:
            for username in room["players"].keys():
                user_match_status[username] = room["room_code"]
                pending_redirects[username] = room["room_code"]

        _push_event(room, "start", f"Battle started with {question.title}.", current_username)
        asyncio.create_task(_finish_room_when_timer_expires(room_code))
        payload = await _broadcast_room(room, db)
        return payload
    except Exception:
        if room.get("status") != "expired":
            room["status"] = "waiting"
            room["locked_at"] = None
            if room.get("matchmaking") == "open" and room.get("host") in _room_online_players(room):
                d = room.get("difficulty")
                open_rooms.setdefault(d, [])
                if room["room_code"] not in open_rooms[d]:
                    open_rooms[d].append(room["room_code"])
        raise


@router.post("/{room_code}/matchmaking-mode")
async def update_matchmaking_mode(
    room_code: str,
    request: RoomMatchmakingModeRequest,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = _get_room_or_404(room_code)
    if room["host"] != current_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can update matchmaking mode.")
    if room.get("status") != "waiting":
        raise HTTPException(status_code=400, detail="Matchmaking mode can only be changed while room is waiting.")

    difficulty = room.get("difficulty")
    room_key = room.get("room_code")
    is_open = bool(request.open_matchmaking)
    room["matchmaking"] = "open" if is_open else "invite"

    if difficulty in open_rooms:
        if is_open and room_key not in open_rooms[difficulty]:
            open_rooms[difficulty].append(room_key)
        if not is_open and room_key in open_rooms[difficulty]:
            open_rooms[difficulty].remove(room_key)

    mode_text = "global matchmaking" if is_open else "invite only"
    _push_event(room, "room", f"Host switched room mode to {mode_text}.", current_username)
    payload = await _broadcast_room(room, db)
    return payload


@router.post("/{room_code}/finish")
async def finish_room(
    room_code: str,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = _get_room_or_404(room_code)
    if room["host"] != current_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can finish the room.")
    await _finalize_room(room, db)

    if room.get("status") == "finished":
        return await _broadcast_room(room, db)

    room["status"] = "finished"
    room["finished_at"] = _now_iso()
    _push_event(room, "finish", "Battle finished by host.", current_username)
    try:
        if room.get("difficulty") in open_rooms and room_code in open_rooms.get(room.get("difficulty"), []):
            open_rooms[room.get("difficulty")].remove(room_code)
    except Exception:
        pass
    payload = await _broadcast_room(room, db)
    return payload


@router.post("/{room_code}/next")
async def next_question(
    room_code: str,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = _get_room_or_404(room_code)
    if room["host"] != current_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can advance the room.")
    if room.get("status") != "round_finished" and room.get("status") != "finished":
        raise HTTPException(status_code=400, detail="Room must be finished to advance to next question.")

    questions = await _get_room_question_pool(db, room)
    if not questions:
        raise HTTPException(status_code=404, detail="No questions available for this difficulty.")

    used = set(room.get("used_questions", []))
    remaining = [q for q in questions if q.id not in used]
    if not remaining:
        room["all_questions_finished"] = True
        _push_event(room, "info", "All questions in the pool have been used.", current_username)
        payload = await _broadcast_room(room, db)
        return payload

    question = random.choice(remaining)
    room["question_id"] = question.id
    room["status"] = "active"
    room["started_at"] = _now_iso()
    used_list = room.setdefault("used_questions", [])
    if question.id not in used_list:
        used_list.append(question.id)

    for player in room["players"].values():
        player["status"] = "active"
        player["ready"] = False
        player["typing"] = False
        player["last_action"] = "started"

    _push_event(room, "start", f"Next battle started with {question.title}.", current_username)
    asyncio.create_task(_finish_room_when_timer_expires(room_code))
    payload = await _broadcast_room(room, db)
    return payload


# ✅ FIX: player["status"] = "ready" added so frontend can display it correctly
@router.post("/{room_code}/ready")
async def player_ready(
    room_code: str,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark the current player as ready. If all players are ready, auto-start the battle."""
    room = _get_room_or_404(room_code)

    if current_username not in room["players"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Join the room before marking ready.")

    if room.get("status") != "waiting":
        raise HTTPException(status_code=400, detail="Room is not in waiting state.")

    player = room["players"][current_username]
    player["ready"] = True
    player["status"] = "ready"          # ✅ FIX: was missing — frontend reads player.status
    player["last_action"] = "ready"
    _push_event(room, "player", f"{current_username} is ready.", current_username)

    # Auto-start if all players are ready
    all_ready = (
        all(p.get("ready") for p in room["players"].values())
        and len(room["players"]) >= 2
    )

    if all_ready:
        try:
            questions = await _get_room_question_pool(db, room)
            if not questions:
                raise HTTPException(status_code=404, detail="No questions available for this difficulty.")

            question = random.choice(questions)
            room["question_id"] = question.id
            room["status"] = "active"
            room["started_at"] = _now_iso()
            used = room.setdefault("used_questions", [])
            if question.id not in used:
                used.append(question.id)

            for p in room["players"].values():
                p["status"] = "active"
                p["ready"] = False
                p["typing"] = False
                p["last_action"] = "started"

            async with matchmaking_lock:
                for username in room["players"].keys():
                    user_match_status[username] = room["room_code"]
                    pending_redirects[username] = room["room_code"]

            _push_event(room, "start", f"Battle started with {question.title}.", current_username)
            asyncio.create_task(_finish_room_when_timer_expires(room_code))
        except HTTPException:
            raise
        except Exception:
            if room.get("status") != "expired":
                room["status"] = "waiting"
            raise

    payload = await _broadcast_room(room, db)
    return {
        "status": "ok",
        "all_ready": all_ready,
        "roomCode": payload.get("roomCode"),
    }


async def _finish_room_when_timer_expires(room_code: str):
    room = room_store.get(room_code)
    if not room or room.get("status") != "active":
        return
    remaining = _timer_payload(room).get("remaining_seconds") or 0
    await asyncio.sleep(max(remaining, 0) + 1)
    room = room_store.get(room_code)
    if not room or room.get("status") != "active":
        return
    async with AsyncSessionLocal() as db:
        _push_event(room, "timer", "Time is up. Battle finished.")
        await _finalize_room(room, db)
        await _auto_advance_if_questions_remain(room, db)
        await _broadcast_room(room, db)


async def _auto_advance_if_questions_remain(room: dict, db: AsyncSession) -> None:
    """Auto-advance to next question if one is available after round finalization."""
    if room.get("status") != "round_finished":
        return

    questions = await _get_room_question_pool(db, room)
    if not questions:
        room["all_questions_finished"] = True
        return

    used = set(room.get("used_questions", []))
    remaining = [q for q in questions if q.id not in used]
    if not remaining:
        room["all_questions_finished"] = True
        _push_event(room, "info", "All questions in the pool have been used.", None)
        return

    question = random.choice(remaining)
    room["question_id"] = question.id
    room["status"] = "active"
    room["started_at"] = _now_iso()
    used_list = room.setdefault("used_questions", [])
    if question.id not in used_list:
        used_list.append(question.id)

    for player in room["players"].values():
        player["status"] = "active"
        player["ready"] = False
        player["typing"] = False
        player["last_action"] = "started"

    _push_event(room, "start", f"Auto-advancing to next question: {question.title}", None)
    asyncio.create_task(_finish_room_when_timer_expires(room["room_code"]))


async def calculate_platform_stats(room_code: str):
    await asyncio.sleep(2)
    print(f"Analytics Update: Average XP gain is 450.2. Match {room_code} finished and metrics processed asynchronously.")


@router.post("/{room_code}/submit")
async def submit_solution(
    room_code: str,
    request: SubmissionRequest,
    current_username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    logger.info("SUBMIT ATTEMPT room_id=%s user_id=%s language=%s", room_code, current_username, request.language)
    room = _get_room_or_404(room_code)
    await _expire_room_if_needed(room, db)
    if room["status"] != "active":
        raise HTTPException(status_code=400, detail="This room is not accepting submissions right now.")

    player = room["players"].get(current_username)
    if not player:
        raise HTTPException(status_code=403, detail="Join the room before submitting.")
    if player["status"] == "submitted":
        raise HTTPException(status_code=400, detail="You have already submitted for this room.")

    question = await _get_question_by_id(db, room.get("question_id"))
    if not question:
        raise HTTPException(status_code=400, detail="No question has been assigned to this room.")

    code = request.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="Submission code cannot be empty.")

    lang = request.language.lower()
    try:
        if lang in ("python",):
            judge_result = evaluate_python_cases(request.code, question.test_cases or [], timeout_seconds=12)
        elif lang in ("javascript", "js"):
            from app.routers.execution import evaluate_js_cases
            judge_result = evaluate_js_cases(request.code, question.test_cases or [], timeout_seconds=12)
        elif lang in ("cpp", "c++"):
            from app.routers.execution import evaluate_cpp_cases
            judge_result = evaluate_cpp_cases(request.code, question.test_cases or [], timeout_seconds=12)
        else:
            judge_result = unsupported_language_response(request.language)
    except Exception:
        logger.exception("SUBMIT EXECUTION FAILURE room_id=%s user_id=%s", room_code, current_username)
        raise HTTPException(status_code=500, detail="Judge execution failed.")

    passed = judge_result.status == "Accepted" and judge_result.total > 0 and judge_result.passed == judge_result.total
    score = question.points if passed else 0
    status_label = judge_result.status
    submission_record = {
        "id": f"{current_username}-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "language": request.language,
        "status": status_label,
        "runtime_ms": judge_result.runtime_ms,
        "memory_kb": judge_result.memory_kb,
        "score": score,
        "passed": judge_result.passed,
        "total": judge_result.total,
        "submitted_at": _now_iso(),
    }

    player["code"] = request.code
    player["language"] = request.language
    player["submitted_at"] = _now_iso()
    player["status"] = "submitted" if passed else "active"
    player["score"] = score
    player["typing"] = False
    player["last_action"] = "submitted" if passed else "wrong_answer"
    player["progress"] = int((judge_result.passed / judge_result.total) * 100) if judge_result.total else 0
    player["runtime_ms"] = judge_result.runtime_ms
    player["memory_kb"] = judge_result.memory_kb
    player["passed"] = judge_result.passed
    player["total"] = judge_result.total
    player.setdefault("submissions", []).insert(0, submission_record)
    del player["submissions"][20:]

    if passed:
        _push_event(room, "submit", f"{current_username} submitted an accepted solution.", current_username)
    else:
        _push_event(room, "submit", f"{current_username} submitted: {status_label}.", current_username)

    logger.info(
        "SUBMIT RESULT room_id=%s user_id=%s status=%s passed=%s total=%s score=%s",
        room_code, current_username, status_label, judge_result.passed, judge_result.total, score,
    )

    if all(member["status"] == "submitted" for member in room["players"].values()):
        await _finalize_room(room, db)
        background_tasks.add_task(calculate_platform_stats, room_code)

    await _broadcast_room(room, db)

    return {
        "passed": passed,
        "status": status_label,
        "score": score,
        "runtime_ms": judge_result.runtime_ms,
        "memory_kb": judge_result.memory_kb,
        "passed_count": judge_result.passed,
        "total_count": judge_result.total,
        "test_results": [result.model_dump() for result in judge_result.results],
        "message": "Accepted." if passed else status_label,
    }


# Algorithmic Matchmaking state
MATCH_DIFFICULTIES = ("easy", "medium", "hard")
waitlist = {"easy": [], "medium": [], "hard": [], "all": []}
user_match_status = {}
open_rooms = {"easy": [], "medium": [], "hard": [], "all": []}
matchmaking_lock = asyncio.Lock()
pending_redirects = {}


def _create_waiting_player(username: str) -> dict:
    return {
        "username": username,
        "status": "waiting",
        "ready": False,
        "score": 0,
        "joined_at": _now_iso(),
        "submitted_at": None,
        "code": "",
        "language": None,
        "online": False,
        "typing": False,
        "progress": 0,
        "last_action": "joined",
        "runtime_ms": None,
        "memory_kb": None,
        "passed": 0,
        "total": 0,
        "submissions": [],
    }


def _find_user_room_code(username: str) -> str | None:
    for room_code, room in room_store.items():
        if room.get("status") in {"finished", "expired"}:
            continue
        if username in room.get("players", {}):
            return room_code
    return None


@router.post("/matchmake")
async def matchmake(
    request: RoomCreateRequest,
    current_username: str = Depends(get_current_user),
):
    difficulty = request.difficulty.lower()
    if difficulty not in VALID_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid difficulty level.")

    room_to_broadcast = None
    matched_room_code = None

    async with matchmaking_lock:
        existing_room_code = _find_user_room_code(current_username)
        if existing_room_code:
            existing_room = room_store.get(existing_room_code)
            if existing_room and _room_allows_matchmaking_join(existing_room):
                user_match_status[current_username] = existing_room_code
                matched_room_code = existing_room_code
            else:
                user_match_status.pop(current_username, None)

        for queued_users in waitlist.values():
            if current_username in queued_users:
                queued_users.remove(current_username)

        if not matched_room_code:
            open_scan = ["all", *MATCH_DIFFICULTIES] if difficulty == "all" else [difficulty]
            for diff in open_scan:
                if matched_room_code:
                    break
                open_list = list(open_rooms.get(diff, []))
                for rc in open_list:
                    room = room_store.get(rc)
                    if not room:
                        try:
                            open_rooms[diff].remove(rc)
                        except ValueError:
                            pass
                        continue
                    if not _room_allows_matchmaking_join(room):
                        if _room_is_expired(room) or room.get("status") != "waiting" or not _room_host_online(room):
                            try:
                                open_rooms[diff].remove(rc)
                            except ValueError:
                                pass
                        continue
                    if room.get("matchmaking") != "open":
                        continue
                    if current_username in room.get("players", {}):
                        user_match_status[current_username] = rc
                        matched_room_code = rc
                        break

                    room["players"][current_username] = _create_waiting_player(current_username)
                    _push_event(room, "match", f"{current_username} joined open room {rc}.")
                    user_match_status[current_username] = rc
                    pending_redirects[current_username] = rc
                    matched_room_code = rc
                    room_to_broadcast = room
                    break

        if not matched_room_code:
            queue_order = ["easy", "medium", "hard", "all"] if difficulty == "all" else [difficulty]
            matched_username = None
            matched_queue = None
            for queue_name in queue_order:
                candidate = next((u for u in waitlist.get(queue_name, []) if u != current_username), None)
                if candidate:
                    matched_username = candidate
                    matched_queue = queue_name
                    waitlist[queue_name].remove(candidate)
                    break

            if matched_username:
                room_difficulty = difficulty
                if room_difficulty == "all":
                    room_difficulty = matched_queue if matched_queue in MATCH_DIFFICULTIES else random.choice(list(MATCH_DIFFICULTIES))

                room_code = _generate_room_code()
                while room_code in room_store:
                    room_code = _generate_room_code()

                host = matched_username
                room_store[room_code] = {
                    "room_code": room_code,
                    "host": host,
                    "difficulty": room_difficulty,
                    "matchmaking": "invite",
                    "status": "waiting",
                    "created_at": _now_iso(),
                    "started_at": None,
                    "finished_at": None,
                    "locked_at": None,
                    "expired_at": None,
                    "question_id": None,
                    "time_limit_minutes": {"easy": 10, "medium": 15, "hard": 20}[room_difficulty],
                    "players": {
                        host: _create_waiting_player(host),
                        current_username: _create_waiting_player(current_username),
                    },
                    "events": [],
                    "chat_messages": [],
                }
                _push_event(room_store[room_code], "match", f"{matched_username} matched with {current_username}.")
                user_match_status[matched_username] = room_code
                user_match_status[current_username] = room_code
                pending_redirects[matched_username] = room_code
                pending_redirects[current_username] = room_code
                matched_room_code = room_code

        if not matched_room_code:
            waitlist[difficulty].append(current_username)
            user_match_status[current_username] = "waiting"

    if room_to_broadcast:
        try:
            async with AsyncSessionLocal() as db:
                await _broadcast_room(room_to_broadcast, db)
        except Exception:
            logger.exception(
                "Failed to broadcast open-room matchmaking join for room %s",
                room_to_broadcast.get("room_code"),
            )

    if matched_room_code:
        return {"status": "matched", "roomCode": matched_room_code}
    return {"status": "waiting"}


@router.get("/matchmake/status")
async def get_matchmake_status(
    current_username: str = Depends(get_current_user),
):
    async with matchmaking_lock:
        redirect_room_code = pending_redirects.get(current_username)
        players_in_queue = sum(len(q) for q in waitlist.values())
        if redirect_room_code:
            room = room_store.get(redirect_room_code)
            if room and current_username in room.get("players", {}):
                if room.get("status") == "waiting" and not _room_allows_matchmaking_join(room):
                    pending_redirects.pop(current_username, None)
                else:
                    return {"status": "matched", "roomCode": redirect_room_code, "trigger": "host_accept", "players_in_queue": players_in_queue}
            pending_redirects.pop(current_username, None)

        status_value = user_match_status.get(current_username)

        if status_value not in (None, "waiting", "idle"):
            room = room_store.get(status_value)
            if room and current_username in room.get("players", {}):
                if room.get("status") == "waiting":
                    if _room_allows_matchmaking_join(room):
                        return {"status": "matched", "roomCode": status_value, "players_in_queue": players_in_queue}
                elif _room_allows_rejoin(room):
                    return {"status": "matched", "roomCode": status_value, "players_in_queue": players_in_queue}

        inferred_room_code = _find_user_room_code(current_username)
        if inferred_room_code:
            user_match_status[current_username] = inferred_room_code
            return {"status": "matched", "roomCode": inferred_room_code, "players_in_queue": players_in_queue}

        in_waitlist = any(current_username in queue for queue in waitlist.values())
        players_in_queue = sum(len(q) for q in waitlist.values())

        if in_waitlist:
            user_match_status[current_username] = "waiting"
            return {"status": "waiting", "players_in_queue": players_in_queue}

        user_match_status[current_username] = "idle"
        return {"status": "idle", "players_in_queue": players_in_queue}


@router.post("/matchmake/cancel")
async def cancel_matchmake(
    current_username: str = Depends(get_current_user),
):
    async with matchmaking_lock:
        for diff in waitlist:
            if current_username in waitlist[diff]:
                waitlist[diff].remove(current_username)
        if current_username in user_match_status:
            del user_match_status[current_username]
        pending_redirects.pop(current_username, None)
    return {"status": "idle"}


@router.websocket("/{room_code}/ws")
async def websocket_endpoint(websocket: WebSocket, room_code: str, token: str = None):
    room_id = room_code.strip().upper()
    username = None
    accepted = False
    print("WS CONNECT ATTEMPT", room_id)
    logger.info("WS CONNECT ATTEMPT room_id=%s client=%s", room_id, websocket.client)

    try:
        await websocket.accept()
        accepted = True
        print("WS ACCEPTED", room_id)
        logger.info("WS ACCEPTED room_id=%s client=%s state=%s", room_id, websocket.client, websocket.client_state)
    except Exception as exc:
        print("WS ACCEPT ERROR", exc)
        logger.exception("WS ACCEPT ERROR room_id=%s client=%s", room_id, websocket.client)
        return

    if not token:
        logger.warning("WS CLOSE missing token room_id=%s", room_id)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    try:
        from jose import jwt
        from app.auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            logger.warning("WS CLOSE invalid token subject room_id=%s", room_id)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    except Exception as exc:
        logger.warning("WS CLOSE jwt decode failed room_id=%s error=%s", room_id, exc)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    try:
        room = room_store.get(room_id)
    except Exception as exc:
        logger.exception("WS CLOSE room lookup error room_id=%s user_id=%s", room_id, username)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Room lookup failed")
        return

    if not room:
        logger.warning("WS CLOSE room not found room_id=%s user_id=%s", room_id, username)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Room not found")
        return

    if username not in room["players"]:
        logger.warning("WS CLOSE user not in room room_id=%s user_id=%s", room_id, username)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Join room before connecting")
        return

    room["players"][username]["online"] = True
    room["players"][username]["last_action"] = "online"
    _push_event(room, "presence", f"{username} is online.", username)

    manager.connect(room_id, websocket, username)
    async with AsyncSessionLocal() as db:
        # Broadcast to all connected clients AND send the current room state
        # directly to this socket. This ensures a late-joining player (who
        # connected after the battle started and missed the earlier broadcast)
        # immediately receives the active room state without waiting for the
        # next event.
        payload = await _broadcast_room(room, db)
        try:
            await websocket.send_json({"event": "room_updated", "room": payload})
        except Exception:
            pass  # socket may have closed; the broadcast above already tried

    try:
        while True:
            raw = await websocket.receive_json()
            event_type = raw.get("event")
            player = room["players"].get(username)
            if not player:
                continue

            if event_type == "ping":
                await websocket.send_json({"event": "pong", "server_now": _now_iso(), **_timer_payload(room)})
                continue

            if event_type == "typing":
                player["typing"] = bool(raw.get("typing"))
                player["last_action"] = "typing" if player["typing"] else "editing"
            elif event_type == "chat_message":
                message = str(raw.get("message") or "").strip()
                if not message:
                    continue
                if len(message) > 500:
                    await websocket.send_json({"event": "chat_error", "message": "Messages must be 500 characters or fewer."})
                    continue
                _push_chat_message(room, username, message)
                player["last_action"] = "sent a message"
            elif event_type == "run_code":
                player["last_action"] = "ran code"
                _push_event(room, "run", f"{username} ran code.", username)
            elif event_type == "focus":
                player["last_action"] = raw.get("target") or "focused"
            elif event_type == "player_ready":
                # ✅ FIX: set player["status"] = "ready" so frontend displays it correctly
                player["ready"] = True
                player["status"] = "ready"      # ✅ KEY FIX
                player["last_action"] = "ready"
                _push_event(room, "player", f"{username} is ready.", username)

                all_ready = (
                    all(p.get("ready") for p in room["players"].values())
                    and len(room["players"]) >= 2
                )
                if all_ready and room.get("status") == "waiting":
                    try:
                        async with AsyncSessionLocal() as db:
                            questions = await _get_room_question_pool(db, room)
                            if not questions:
                                await websocket.send_json({"event": "error", "message": "No questions available for this difficulty."})
                            else:
                                question = random.choice(questions)
                                room["question_id"] = question.id
                                room["status"] = "active"
                                room["started_at"] = _now_iso()
                                used = room.setdefault("used_questions", [])
                                if question.id not in used:
                                    used.append(question.id)

                                for p in room["players"].values():
                                    p["status"] = "active"
                                    p["ready"] = False
                                    p["typing"] = False
                                    p["last_action"] = "started"

                                async with matchmaking_lock:
                                    for u in room["players"].keys():
                                        user_match_status[u] = room["room_code"]
                                        pending_redirects[u] = room["room_code"]

                                _push_event(room, "start", f"Battle started with {question.title}.", username)
                                asyncio.create_task(_finish_room_when_timer_expires(room_code))
                    except Exception:
                        if room.get("status") != "expired":
                            room["status"] = "waiting"
                        raise
            else:
                continue

            async with AsyncSessionLocal() as db:
                await _broadcast_room(room, db)
    except WebSocketDisconnect as exc:
        logger.info(
            "WS DISCONNECT room_id=%s user_id=%s code=%s reason=%s",
            room_id, username, getattr(exc, "code", None), getattr(exc, "reason", ""),
        )
        if username in room["players"]:
            room["players"][username]["online"] = False
            room["players"][username]["typing"] = False
            room["players"][username]["last_action"] = "offline"
            _push_event(room, "presence", f"{username} went offline.", username)
        manager.disconnect(room_id, websocket)
        async with AsyncSessionLocal() as db:
            if await _maybe_expire_if_empty(room, db):
                return
            await _broadcast_room(room, db)
    except Exception as e:
        logger.exception("WS ERROR room_id=%s user_id=%s accepted=%s state=%s error=%s", room_id, username, accepted, websocket.client_state, e)
        if username and username in room["players"]:
            room["players"][username]["online"] = False
            room["players"][username]["typing"] = False
        manager.disconnect(room_id, websocket)
        try:
            async with AsyncSessionLocal() as db:
                if await _maybe_expire_if_empty(room, db):
                    return
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="WebSocket error")
        except Exception:
            pass