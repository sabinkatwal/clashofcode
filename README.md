# Clash of Code: Multiplayer Coding Battle System

## 📌 1. Project Title

**Clash of Code** is a multiplayer coding battle platform where developers compete in real-time coding challenges. Users can create rooms, join battles, and climb the leaderboard in a competitive environment.

-----

## 📖 2. Overview

Clash of Code is a full-stack web application that lets developers battle each other by solving coding problems as fast as possible. It's a competitive coding game where speed and accuracy matter.

### What Users Can Do:
- **Login/Register**: Create an account or sign in to access the platform.
- **Create Room**: Start a new battle room and invite others.
- **Join Room**: Enter a room code to join an existing battle.
- **Matchmaking**: Find opponents through the matchmaking system.
- **Code Battles**: Compete in real-time coding challenges with live code execution.
- **View Profile**: Check personal stats like wins, losses, and ranking.
- **Leaderboard**: Climb the rankings and see your performance vs. other players.

This is a real-time multiplayer system, meaning multiple users can interact in the same room at the same time. The app is built to handle live updates and shared experiences using WebSockets for instant communication.

---

## 🛠️ 3. Tech Stack

### Frontend (React 18 with Vite):
- **React 18**: Modern JavaScript library for building dynamic user interfaces.
- **Vite**: Ultra-fast build tool for development and production.
- **React Router v6**: Client-side routing between pages.
- **Context API**: Global state management (Auth, Theme).
- **Axios**: HTTP client for backend API communication.
- **WebSocket**: Real-time bidirectional communication with the server.

### Backend (Python with FastAPI):
- **FastAPI**: Modern, fast Python web framework with automatic API documentation.
- **SQLAlchemy**: ORM for database operations.
- **Alembic**: Database migrations.
- **JWT (JSON Web Tokens)**: Secure authentication tokens.
- **WebSocket (Starlette)**: Real-time communication protocol.
- **SQLite/PostgreSQL**: Database storage.
- **Python Code Execution**: Safe sandbox environment for running user code.

### Styling:
- **CSS Modules**: Scoped component styling.
- **Dark/Light Mode System**: Theme switching with persistent storage.

---

## 📁 4. Project Structure

```
clashofcode/
├── frontend/                    # React Vite application
│   ├── src/
│   │   ├── api/
│   │   │   └── axios.js        # Centralized API client with interceptors
│   │   ├── components/
│   │   │   ├── Navbar.jsx      # Top navigation bar
│   │   │   ├── ProtectedRoute.jsx # Authentication guard
│   │   │   ├── ErrorBoundary.jsx  # Error handling wrapper
│   │   │   └── ui/             # Reusable UI components
│   │   ├── context/
│   │   │   ├── AuthContext.jsx # User login state management
│   │   │   └── ThemeContext.jsx # Dark/light theme management
│   │   ├── pages/
│   │   │   ├── Home.jsx        # Landing page
│   │   │   ├── Login.jsx       # Login form
│   │   │   ├── Register.jsx    # Sign-up form
│   │   │   ├── Dashboard.jsx   # Main user dashboard
│   │   │   ├── CreateRoom.jsx  # Create new battle room
│   │   │   ├── MatchmakingLobby.jsx # Matchmaking interface
│   │   │   ├── FindMatch.jsx   # Find match UI
│   │   │   ├── CodingInterface.jsx # Battle arena with code editor
│   │   │   ├── Profile.jsx     # User profile & stats
│   │   │   ├── Leaderboard.jsx # Global rankings
│   │   │   └── DeveloperQuestions.jsx # Question management
│   │   ├── layouts/
│   │   │   └── AppShell.jsx    # Main app layout wrapper
│   │   ├── styles/
│   │   │   ├── global.css      # Global styles
│   │   │   ├── theme.css       # Theme definitions
│   │   │   ├── dark.css        # Dark mode styles
│   │   │   └── light.css       # Light mode styles
│   │   ├── hooks/              # Custom React hooks
│   │   ├── utils/
│   │   │   └── socket.js       # WebSocket client setup
│   │   ├── App.jsx             # Root app component
│   │   └── main.jsx            # Entry point
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
├── backend/                     # FastAPI Python application
│   ├── app/
│   │   ├── main.py            # FastAPI app initialization & routes
│   │   ├── database.py        # Database connection & session management
│   │   ├── models/            # SQLAlchemy database models
│   │   │   ├── user.py        # User model
│   │   │   ├── room.py        # Battle room model
│   │   │   ├── question.py    # Coding questions model
│   │   │   └── execution.py   # Code execution results model
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # API route handlers
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── user.py        # User profile endpoints
│   │   │   ├── rooms.py       # Room management endpoints
│   │   │   ├── questions.py   # Questions endpoints
│   │   │   ├── execution.py   # Code execution endpoints
│   │   │   └── leaderboard.py # Leaderboard endpoints
│   │   ├── services/          # Business logic layer
│   │   ├── utils/
│   │   │   ├── auth.py        # JWT utilities
│   │   │   ├── code_runner.py # Safe code execution
│   │   │   └── validation.py  # Input validation
│   │   └── websocket_manager.py # WebSocket connection manager
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment variables template
│   └── README.md
│
└── README.md                  # This file
```

### Folder Explanations:
- **api/**: Centralized API client with JWT token injection and error handling.
- **components/**: Reusable UI parts (buttons, modals, cards, etc.).
- **context/**: React Context for global state (user data, theme).
- **pages/**: Full-page components for each route.
- **routers/**: FastAPI route handlers organized by feature.
- **models/**: Database ORM definitions (SQLAlchemy).
- **schemas/**: Request/response validation (Pydantic).
- **utils/**: Helper utilities (JWT, code execution, validation).

---

## 🔐 5. Authentication Flow (Very Important)

Authentication ensures users are who they claim to be.

### Login Process:
1. **User Submission**: User enters email and password in the login form.
2. **Frontend Request**: Axios sends credentials to `/auth/login`.
3. **Backend Validation**: FastAPI checks credentials against the database.
4. **Token Generation**: If valid, backend generates a JWT token.
5. **Response**: Backend returns JWT token + user data.
6. **Token Storage**: Frontend stores token in localStorage.
7. **Context Update**: AuthContext updates global user state.
8. **UI Update**: App displays user as logged in (dashboard, profile link, etc.).

### Session Persistence:
- On page refresh, the app checks localStorage for the token.
- If valid, it automatically restores the user session.
- If expired, the user is redirected to login.

### Simple Diagram:
```
User Input → Frontend Form → Axios API Call → FastAPI Backend
→ Database Lookup → JWT Generation → Response
→ localStorage Storage → AuthContext Update → UI Render
```

---

## 🛡️ 6. Authorization (Protected Routes)

Protected routes ensure only authenticated users can access certain pages.

### Implementation:
- `ProtectedRoute` component wraps protected pages.
- It checks for a valid JWT token in localStorage.
- If token exists and is valid, the route renders normally.
- If no token or token expired, redirects to `/login`.

### Protected Pages:
- **/dashboard**: Main user hub
- **/create-room**: Start a new battle
- **/battle-room/:roomCode**: Active battle arena
- **/matchmaking**: Find opponents
- **/profile**: User stats and settings

---

## 🏠 7. Room & Matchmaking System (Core Features)

The room system enables peer-to-peer battles. Matchmaking helps players find opponents automatically.

### Create Room Flow:
1. User clicks "Create Room" on dashboard.
2. Frontend sends POST request to `/rooms/create`.
3. Backend generates unique room code (e.g., "ABC123").
4. Room stored in database with host info and empty players list.
5. Frontend redirects to `/battle-room/ABC123`.

### Join Room Flow:
1. User enters room code and clicks join.
2. Frontend sends POST to `/rooms/join` with room code.
3. Backend verifies room exists and has space.
4. User added to room's players list.
5. WebSocket broadcasts update to all room members.

### Matchmaking Flow:
1. User clicks "Find Match".
2. Frontend sends request to `/matchmaking/queue`.
3. Backend adds user to matchmaking queue.
4. When 2+ players are in queue, backend creates a room.
5. All matched players receive WebSocket notification.
6. Frontend redirects to battle room.

### Room Data Structure:
```javascript
{
  roomCode: "ABC123",
  host: {
    userId: 1,
    username: "Coder1",
  },
  players: [
    { userId: 1, username: "Coder1", status: "ready", score: 0 },
    { userId: 2, username: "Coder2", status: "waiting", score: 0 }
  ],
  status: "waiting",  // "waiting" | "active" | "finished"
  question: { ... },
  createdAt: "2026-05-21T12:00:00Z",
  updatedAt: "2026-05-21T12:05:00Z"
}
```

---

## 🔄 8. Real-Time Battle System (WebSocket)

The system uses WebSockets for live, instant communication during battles.

### WebSocket Events:
- **`join_room`**: User joins a room
- **`player_joined`**: Broadcast to others when someone joins
- **`player_left`**: Broadcast when someone leaves
- **`start_game`**: Host initiates the battle
- **`code_update`**: Broadcast code changes in real-time
- **`submit_code`**: Player submits solution
- **`game_finished`**: Battle ends, results sent
- **`state_update`**: Sync room state across clients

### Connection Manager:
- `websocket_manager.py` tracks active WebSocket connections.
- Associates connections with room codes and user IDs.
- Broadcasts messages to all clients in a room.
- Handles disconnections gracefully.

---

## 💻 9. Code Execution (Safe Sandbox)

The backend safely executes user code in isolated environments.

### Execution Flow:
1. User submits code from the coding interface.
2. Frontend sends code to `/execution/run` endpoint.
3. Backend validates code syntax.
4. Code runs in a timeout-limited sandbox.
5. Output/errors returned to frontend.
6. Results displayed to user in real-time.

### Safety Features:
- **Timeout Limits**: Code execution limited to 5-10 seconds.
- **Resource Restrictions**: Memory and CPU limits enforced.
- **Restricted Imports**: Dangerous modules are blocked.
- **Isolated Environment**: Each execution is sandboxed.

---

## 🌍 10. Global State Management

Global state is shared across the entire app using React Context.

### AuthContext:
- **Stores**: Current user info, JWT token, authentication status
- **Methods**: `login()`, `logout()`, `refreshToken()`
- **Persistence**: Syncs with localStorage

### ThemeContext:
- **Stores**: Current theme ("dark" or "light")
- **Methods**: `toggleTheme()`
- **Persistence**: Syncs with localStorage

---

## 🌐 11. API Integration (Axios)

Axios handles all HTTP communication with centralized configuration.

### Key Features:
- **Base URL**: Configured from environment variables
- **JWT Interceptor**: Automatically adds `Authorization: Bearer <token>` to every request
- **Error Handling**: Centralized error responses and retry logic
- **CORS Configuration**: Handles cross-origin requests

### Example Request:
```javascript
// Frontend code
const response = await api.post('/rooms/create', { maxPlayers: 2 });

// What Axios sends:
POST /rooms/create
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

---

## 👤 12. Profile & Statistics System

Users can view their battle history and performance metrics.

### Features:
- **Profile Info**: Username, email, join date
- **Stats**: Games played, wins, losses, win rate, ranking
- **Battle History**: List of recent battles with results
- **Achievements**: Badges and milestones

### Backend Endpoints:
- `GET /user/profile`: User information
- `GET /user/stats`: Aggregate statistics
- `GET /user/battle-history`: Past battles

---

## 🌙 13. Dark/Light Mode System

Users can switch themes with persistent storage.

### How It Works:
- **Toggle**: Button in Navbar switches mode
- **Storage**: Theme preference saved in localStorage
- **CSS Modules**: Dark/light CSS automatically applied
- **Persistence**: Theme persists across sessions

---

## 🚀 14. How to Run the Project

### Prerequisites:
- **Node.js 18+** (for frontend)
- **Python 3.9+** (for backend)
- **npm** or **yarn** (for frontend package management)
- **pip** (for Python packages)

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` in your browser.

### Backend Setup:
```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```
Backend runs on `http://localhost:8000` (API) / `ws://localhost:8000` (WebSocket).

### Environment Variables:

**Backend (.env file):**
```
DATABASE_URL=sqlite:///./clashofcode.db
SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
GOOGLE_CLIENT_ID=your_google_web_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://clashofcode-4cz0.onrender.com/auth/google/callback
FRONTEND_URL=https://clashofcode-three.vercel.app
LOG_LEVEL=INFO
```

**Frontend (.env file):**
```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### Google OAuth setup

Google sign-in uses the existing JWT authentication flow. The backend starts the
OAuth authorization request at `/auth/google/login`, validates the returned
state, nonce, and Google OIDC ID token at `/auth/google/callback`, then redirects
to the frontend callback route with the existing ClashOfCode token in the URL
fragment.

Create a Google OAuth 2.0 **Web application** client and add this exact
authorized redirect URI:

```
https://clashofcode-4cz0.onrender.com/auth/google/callback
```

Set these variables in the Render backend service:

- `GOOGLE_CLIENT_ID`: the Web application client ID.
- `GOOGLE_CLIENT_SECRET`: the client secret; keep it only in Render/local backend
  environment variables and never in the frontend.
- `GOOGLE_REDIRECT_URI`: exactly the callback URI above.
- `FRONTEND_URL`: `https://clashofcode-three.vercel.app` (the default is this
  value, but setting it explicitly is recommended).
- `CORS_ORIGINS`: include
  `https://clashofcode-three.vercel.app` and any local development origin.
- `SECRET_KEY` and `DATABASE_URL`: existing required backend settings.

For local testing, use the matching local callback URI
(`http://localhost:8000/auth/google/callback`) in Google Console and set
`GOOGLE_REDIRECT_URI` to that value, while setting `FRONTEND_URL` to
`http://localhost:5173`. Do not use the production client secret in frontend
environment variables. No Cloudflare OAuth configuration is required by this
repository; the Render service owns the OAuth callback.

---

## 📚 15. Learning Path (Beginner Friendly)

Start with foundational concepts and build up:

1. **Authentication**: Learn login/JWT token flow
2. **State Management**: Understand React Context
3. **Protected Routes**: Implement access control
4. **API Communication**: Master Axios patterns
5. **Room System**: Create and join rooms
6. **WebSocket Basics**: Real-time updates
7. **Code Execution**: Safe code sandbox
8. **Full Battle Flow**: Put it all together

---

## 🎯 16. Development Workflow

### Frontend Development:
1. Components live in `src/components/`
2. Pages in `src/pages/`
3. Use Context API for state
4. Axios for API calls
5. CSS Modules for styling

### Backend Development:
1. Routes in `app/routers/`
2. Models in `app/models/`
3. Business logic in `app/services/`
4. Database in `app/database.py`
5. WebSocket in `app/websocket_manager.py`

---

## 📝 17. Database Schema

### Key Tables:
- **users**: User accounts and authentication
- **rooms**: Battle room instances
- **questions**: Coding challenge questions
- **battle_results**: Fight outcomes and scores
- **leaderboard**: User rankings

---

## 🐛 18. Troubleshooting

### Common Issues:

**CORS Error:**
- Ensure frontend URL is in `CORS_ORIGINS` in backend .env
- Frontend and backend use correct URLs

**WebSocket Connection Failed:**
- Check backend is running with WebSocket support
- Verify WS URL in frontend .env is correct

**Code Execution Timeout:**
- Increase timeout in `execution.py` if needed
- Check for infinite loops in submitted code

---

## 🎯 19. Final Summary

**Clash of Code** is a production-ready, full-stack multiplayer coding platform built with:
- **React 18** for a modern frontend
- **FastAPI** for a high-performance backend
- **WebSockets** for real-time communication
- **SQLAlchemy** for robust data management
- **JWT** for secure authentication

The architecture is modular, scalable, and beginner-friendly. Perfect for learning full-stack development or competitive programming!

---

## 📄 License

Open source - feel free to fork and modify!

---

**Last Updated**: May 21, 2026
**Repository**: [sabinkatwal/clashofcode](https://github.com/sabinkatwal/clashofcode)
