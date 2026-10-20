import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import ErrorBoundary from "./components/ErrorBoundary";
import AppShell from "./layouts/AppShell";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import Home from "./pages/Home";
import Login from "./pages/Login";
import GoogleCallback from "./pages/GoogleCallback";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import CreateRoom from "./pages/CreateRoom";
import CodingInterface from "./pages/CodingInterface";
import MatchmakingLobby from "./pages/MatchmakingLobby";
import FindMatch from "./pages/FindMatch";
import Profile from "./pages/Profile";
import Leaderboard from "./pages/Leaderboard";
import DeveloperQuestions from "./pages/DeveloperQuestions";
import Chat from "./pages/Chat";
import AIChatWidget from "./components/AIChatWidget";

function AuthenticatedExtras() {
  const { user } = useAuth();
  return user ? <AIChatWidget /> : null;
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <div className="app-frame">
            <Navbar />
            <AppShell>
              <div className="app-page-offset">
                <ErrorBoundary>
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/auth/callback" element={<GoogleCallback />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/leaderboard" element={<Leaderboard />} />
                    <Route element={<ProtectedRoute />}>
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/matchmaking" element={<MatchmakingLobby />} />
                      <Route path="/find-match" element={<FindMatch />} />
                      <Route path="/create-room" element={<CreateRoom />} />
                      <Route path="/battle-room/:roomCode" element={<CodingInterface />} />
                      <Route path="/coding-interface" element={<Navigate to="/dashboard" replace />} />
                      <Route path="/profile" element={<Profile />} />
                      <Route path="/developer/questions" element={<DeveloperQuestions />} />
                      <Route path="/chat" element={<Chat />} />
                    </Route>
                  </Routes>
                </ErrorBoundary>
              </div>
            </AppShell>
            <AuthenticatedExtras />
          </div>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;