from fastapi import APIRouter, HTTPException, Depends
from database import get_user_by_id
from auth_utils import get_current_user

router = APIRouter()


@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
    }


@router.get("/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    games = user.get("gamesPlayed", 0)
    wins = user.get("wins", 0)
    losses = user.get("losses", 0)
    win_rate = round((wins / games) * 100) if games > 0 else 0

    return {
        "gamesPlayed": games,
        "wins": wins,
        "losses": losses,
        "winRate": win_rate,
        "avgTime": "—",
        "bestTime": "—",
    }
