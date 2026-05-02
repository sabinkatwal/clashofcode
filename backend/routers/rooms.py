import random
import string
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from database import get_room, create_room, add_player_to_room, update_room
from auth_utils import get_current_user

router = APIRouter()


def generate_room_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


class JoinRoomRequest(BaseModel):
    roomCode: str


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_battle_room(current_user: dict = Depends(get_current_user)):
    # Generate unique code
    code = generate_room_code()
    while get_room(code):
        code = generate_room_code()

    room = {
        "roomCode": code,
        "host": {"username": current_user["username"], "id": current_user["sub"]},
        "players": [{"username": current_user["username"], "id": current_user["sub"], "status": "waiting"}],
        "status": "waiting",
    }
    create_room(room)
    return room


@router.post("/join")
def join_battle_room(body: JoinRoomRequest, current_user: dict = Depends(get_current_user)):
    room = get_room(body.roomCode.upper())
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    if room["status"] != "waiting":
        raise HTTPException(status_code=400, detail="Room is no longer accepting players.")
    if len(room["players"]) >= 2:
        raise HTTPException(status_code=400, detail="Room is full.")
    if any(p["username"] == current_user["username"] for p in room["players"]):
        return room  # Already in room

    updated = add_player_to_room(body.roomCode.upper(), {
        "username": current_user["username"],
        "id": current_user["sub"],
        "status": "waiting"
    })
    return updated


@router.get("/{room_code}")
def get_battle_room(room_code: str, current_user: dict = Depends(get_current_user)):
    room = get_room(room_code.upper())
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    # Only members can view
    if not any(p["username"] == current_user["username"] for p in room["players"]):
        raise HTTPException(status_code=403, detail="You are not a member of this room.")
    return room


@router.patch("/{room_code}/ready")
def mark_ready(room_code: str, current_user: dict = Depends(get_current_user)):
    room = get_room(room_code.upper())
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")

    for player in room["players"]:
        if player["username"] == current_user["username"]:
            player["status"] = "ready"

    update_room(room_code.upper(), {"players": room["players"]})
    return room
