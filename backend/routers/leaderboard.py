from fastapi import APIRouter
from database import users_db

router = APIRouter()


@router.get("")
def get_leaderboard():
    players = [
        {
            "username": u["username"],
            "wins": u.get("wins", 0),
            "losses": u.get("losses", 0),
            "gamesPlayed": u.get("gamesPlayed", 0),
            "winRate": round((u.get("wins", 0) / u.get("gamesPlayed", 1)) * 100) if u.get("gamesPlayed", 0) > 0 else 0,
        }
        for u in users_db.values()
    ]
    # Sort by wins desc, then winRate desc
    players.sort(key=lambda x: (-x["wins"], -x["winRate"]))
    return players[:50]  # Top 50
