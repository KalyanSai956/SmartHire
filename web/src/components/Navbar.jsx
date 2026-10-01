import { Link, NavLink, useNavigate } from "react-router-dom";
import { LogOut, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const name =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "User";

  const links = [
    ["Dashboard", "/dashboard"],
    ["Resume ATS", "/analyze"],
    ["Resources", "/resources"],
  ];

  async function logout() {
    try {
      await signOut();
      navigate("/", { replace: true });
    } catch (error) {
      console.error("Logout failed:", error);
    }
  }

  return (
    <header className="topbar">
      <div className="mx-auto max-w-4xl px-1 py-2 topbar-inner">
        {/* LEFT — LOGO */}
        <Link to="/dashboard" className="brand" aria-label="SmartHire home">
          <img
            src="/hi-logo-nav.svg"
            alt="SmartHire"
            className="brand-logo"
            width="34"
            height="28"
          />
        </Link>

        {/* CENTER — NAVIGATION */}
        <nav className="desktop-nav">
          {links.map(([label, to]) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `nav-link ${isActive ? "active" : ""}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="topbar-actions">
          <span className="user-name">{name}</span>

          <button type="button" className="signout-button" onClick={logout}>
            <LogOut size={15} />
            <span>Sign out</span>
          </button>
        </div>
      </div>
    </header>
  );
}
