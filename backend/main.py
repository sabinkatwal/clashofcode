from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, rooms, users, leaderboard

app = FastAPI(
    title="Clash of Code API",
    description="Backend API for the Clash of Code multiplayer coding battle platform.",
    version="1.0.0"
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
app.include_router(users.router, prefix="/user", tags=["Users"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Clash of Code API is running 🚀"}
