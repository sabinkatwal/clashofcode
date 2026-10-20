import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function GoogleCallback() {
  const { completeLogin } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const values = new URLSearchParams(window.location.hash.slice(1));
    const accessToken = values.get("access_token");
    const userValue = values.get("user");

    if (!accessToken || !userValue) {
      navigate("/login?error=Google%20login%20could%20not%20be%20completed.", { replace: true });
      return;
    }

    try {
      completeLogin({
        access_token: accessToken,
        user: JSON.parse(userValue),
      });
      window.history.replaceState(null, "", window.location.pathname);
      navigate("/dashboard", { replace: true });
    } catch {
      navigate("/login?error=Google%20login%20could%20not%20be%20completed.", { replace: true });
    }
  }, [completeLogin, navigate]);

  return <section className="page-shell auth-page"><p>Completing Google sign-in...</p></section>;
}

export default GoogleCallback;
