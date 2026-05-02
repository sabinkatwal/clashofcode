"""
In-memory database for development.
Replace with a real database (PostgreSQL, MongoDB, etc.) for production.
"""

from typing import Dict, List, Optional

# Users: { email -> user_dict }
users_db: Dict[str, dict] = {}

# Rooms: { roomCode -> room_dict }
rooms_db: Dict[str, dict] = {}


# --- User helpers ---

def get_user_by_email(email: str) -> Optional[dict]:
    return users_db.get(email)


def get_user_by_username(username: str) -> Optional[dict]:
    for user in users_db.values():
        if user["username"].lower() == username.lower():
            return user
    return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    for user in users_db.values():
        if user["id"] == user_id:
            return user
    return None


def create_user(user_data: dict) -> dict:
    users_db[user_data["email"]] = user_data
    return user_data


# --- Room helpers ---

def get_room(room_code: str) -> Optional[dict]:
    return rooms_db.get(room_code.upper())


def create_room(room_data: dict) -> dict:
    rooms_db[room_data["roomCode"]] = room_data
    return room_data


def update_room(room_code: str, updates: dict) -> Optional[dict]:
    if room_code in rooms_db:
        rooms_db[room_code].update(updates)
        return rooms_db[room_code]
    return None


def add_player_to_room(room_code: str, player: dict) -> Optional[dict]:
    room = rooms_db.get(room_code)
    if room:
        # Avoid duplicate
        if not any(p["username"] == player["username"] for p in room["players"]):
            room["players"].append(player)
        return room
    return None


def get_all_rooms() -> List[dict]:
    return list(rooms_db.values())
