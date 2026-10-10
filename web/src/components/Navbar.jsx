import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { LogOut, Menu, X } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import "../CSS/Navbar.css";

export default function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const name =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "User";

  /* Shown in the desktop top bar and the mobile menu */
  const mainLinks = [
    ["Dashboard", "/dashboard"],
    ["Resume ATS", "/analyze"],
    ["Resources", "/resources"],
  ];

  /* Shown in the mobile menu only (desktop has these in the sidebar) */
  const extraLinks = [
    ["ATS Scores", "/history"],
    ["Jobs", "/jobs"],
    ["Interview Prep", "/interview-prep"],
    ["AI Settings", "/settings"],
  ];

  const mobileLinks = [...mainLinks, ...extraLinks];

  async function logout() {
    try {
      await signOut();
      setOpen(false);
      navigate("/", { replace: true });
    } catch (error) {
      console.error("Logout failed:", error);
    }
  }

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <Link to="/dashboard" className="brand" aria-label="SmartHire home">
          <img
            src="/hi-logo-nav.svg"
            alt="SmartHire"
            className="brand-logo"
            width="34"
            height="28"
          />
        </Link>

        {/* DESKTOP NAV */}
        <nav className="desktop-nav">
          {mainLinks.map(([label, to]) => (
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

          {/* MOBILE TOGGLE */}
          <button
            type="button"
            className="mobile-menu"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* MOBILE NAV */}
      {open && (
        <nav className="mobile-nav">
          {mobileLinks.map(([label, to]) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `mobile-nav-link ${isActive ? "active" : ""}`
              }
            >
              {label}
            </NavLink>
          ))}

          <button
            type="button"
            className="mobile-nav-link mobile-signout"
            onClick={logout}
          >
            <LogOut size={16} />
            Sign out
          </button>
        </nav>
      )}
    </header>
  );
}
