# ⚔ Clash of Code

A multiplayer coding battle platform where developers compete in real-time coding challenges.

## Quick Start

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Backend
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:5000
```

## Project Structure
```
clash-of-code/
├── frontend/          # React + Vite app
│   └── src/
│       ├── api/       # Axios instance (JWT interceptor)
│       ├── components/# Navbar, ProtectedRoute, UI components
│       ├── context/   # AuthContext, ThemeContext
│       ├── hooks/     # useRoom
│       ├── pages/     # Home, Login, Register, Dashboard, etc.
│       ├── styles/    # Global CSS variables + dark/light theme
│       └── utils/     # WebSocket manager (future)
└── backend/           # FastAPI app
    ├── main.py        # App entry + CORS
    ├── auth_utils.py  # JWT + bcrypt utilities
    ├── database.py    # In-memory store (swap for real DB)
    └── routers/       # auth, rooms, users, leaderboard
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | ✗ | Register new user |
| POST | /auth/login | ✗ | Login, get JWT |
| POST | /rooms/create | ✓ | Create battle room |
| POST | /rooms/join | ✓ | Join a room by code |
| GET | /rooms/:code | ✓ | Get room details |
| PATCH | /rooms/:code/ready | ✓ | Mark player as ready |
| GET | /user/profile | ✓ | Get current user info |
| GET | /user/stats | ✓ | Get user stats |
| GET | /leaderboard | ✓ | Top 50 players |

## Tech Stack
- **Frontend**: React 18, Vite, React Router v6, Axios, Context API
- **Backend**: FastAPI, Python-Jose (JWT), Passlib (bcrypt)
- **Styling**: CSS Modules, CSS Variables, Dark/Light theme
- **Coming Soon**: WebSocket real-time battles
