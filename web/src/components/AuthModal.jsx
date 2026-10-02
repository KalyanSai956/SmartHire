import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ArrowRight, LockKeyhole, Mail, UserRound, X } from "lucide-react";

import { useAuth } from "../context/AuthContext";

function isValidGmail(email) {
  const value = email.trim().toLowerCase();

  return /^[a-z0-9._%+-]+@gmail\.com$/.test(value);
}

function getAuthErrorMessage(error, isLogin) {
  const message = error?.message?.toLowerCase() || "";

  if (
    message.includes("invalid login credentials") ||
    message.includes("invalid credentials")
  ) {
    return "Email or password is incorrect.";
  }

  if (
    message.includes("user already registered") ||
    message.includes("already registered")
  ) {
    return "An account with this email already exists. Please sign in.";
  }

  if (
    message.includes("email not confirmed") ||
    message.includes("email confirmation")
  ) {
    return "Email confirmation is enabled in Supabase. Please disable it to use instant sign up.";
  }

  if (message.includes("password")) {
    return "Please use a valid password with at least 6 characters.";
  }

  if (message.includes("rate limit")) {
    return "Too many attempts. Please wait a moment and try again.";
  }

  if (
    message.includes("network") ||
    message.includes("fetch") ||
    message.includes("failed to fetch")
  ) {
    return "Network error. Please check your internet connection and try again.";
  }

  if (isLogin) {
    return "Unable to sign in. Please check your details and try again.";
  }

  return "Unable to create your account. Please try again.";
}

export default function AuthModal({ mode = "login", onClose, onModeChange }) {
  const navigate = useNavigate();

  const { signIn, signUp, configured } = useAuth();

  const isLogin = mode === "login";

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  /*
   * Lock page scrolling while the authentication modal is open.
   */
  useEffect(() => {
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  /*
   * Clear messages when switching between Login and Signup.
   */
  useEffect(() => {
    setError("");
    setSuccess("");
  }, [mode]);

  /*
   * Update form fields.
   */
  function update(key, value) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));

    /*
     * Remove the previous error as soon as the user starts
     * correcting the form.
     */
    if (error) {
      setError("");
    }

    if (success) {
      setSuccess("");
    }
  }

  /*
   * Close modal when clicking the backdrop.
   *
   * Do not allow closing while an authentication request
   * is currently running.
   */
  function closeOnBackdrop(event) {
    if (event.target === event.currentTarget && !busy) {
      onClose();
    }
  }

  /*
   * Submit login/signup form.
   */
  async function submit(event) {
    event.preventDefault();

    /*
     * Always clear previous messages before starting
     * a new authentication attempt.
     */
    setError("");
    setSuccess("");

    /*
     * Authentication configuration check.
     */
    if (!configured) {
      setError(
        "SmartHire authentication is not configured. Please check your environment settings.",
      );
      return;
    }

    /*
     * Signup-only validation.
     */
    if (!isLogin) {
      const fullName = form.fullName.trim();

      if (!fullName) {
        setError("Please enter your full name.");
        return;
      }

      if (fullName.length < 2) {
        setError("Please enter your complete name.");
        return;
      }
    }

    /*
     * Common email validation.
     */
    const email = form.email.trim().toLowerCase();

    if (!email) {
      setError("Please enter your email address.");
      return;
    }

    if (!isValidGmail(email)) {
      setError("Please provide a valid Gmail address.");
      return;
    }

    /*
     * Common password validation.
     */
    if (!form.password) {
      setError("Please enter your password.");
      return;
    }

    if (form.password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }

    /*
     * Signup password confirmation.
     */
    if (!isLogin) {
      if (!form.confirmPassword) {
        setError("Please confirm your password.");
        return;
      }

      if (form.password !== form.confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
    }

    /*
     * Start authentication request.
     *
     * IMPORTANT:
     * We only use busy for the button state.
     *
     * There is NO full-screen HI logo anymore.
     */
    setBusy(true);

    try {
      /*
       * ==========================
       * LOGIN
       * ==========================
       */
      if (isLogin) {
        const { data } = await signIn(email, form.password);

        /*
         * Supabase should return a session after
         * successful password authentication.
         */
        if (!data?.session) {
          setBusy(false);
          setError("Unable to create a login session. Please try again.");
          return;
        }

        /*
         * Authentication succeeded.
         *
         * Close the modal first, then navigate immediately.
         *
         * There is intentionally NO artificial delay here.
         */
        onClose();

        navigate("/dashboard", {
          replace: true,
        });

        return;
      }

      /*
       * ==========================
       * SIGNUP
       * ==========================
       */
      const { data } = await signUp(email, form.password, form.fullName.trim());

      /*
       * Supabase signup without a session usually means
       * email confirmation is enabled.
       */
      if (!data?.session) {
        setBusy(false);

        setError(
          "Account created, but automatic sign in was not completed. Please disable email confirmation in Supabase and try again.",
        );

        return;
      }

      /*
       * Signup succeeded.
       *
       * Go directly to onboarding.
       */
      onClose();

      navigate("/onboarding", {
        replace: true,
      });
    } catch (authError) {
      /*
       * IMPORTANT:
       *
       * A failed login never navigates anywhere.
       * The modal stays open and the error is shown here.
       */
      console.error("Authentication error:", authError);

      setBusy(false);

      setError(getAuthErrorMessage(authError, isLogin));
    }
  }

  return (
    <div className="auth-modal-overlay" onMouseDown={closeOnBackdrop}>
      <div
        className="auth-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
      >
        {/* CLOSE */}

        <button
          type="button"
          className="auth-modal-close"
          onClick={onClose}
          disabled={busy}
          aria-label="Close"
        >
          <X size={18} />
        </button>

        {/* AUTH CONTENT */}

        <div className="auth-modal-content">
          {/* BRAND */}

          <div className="auth-modal-brand">
            <img
              src="/hi-logo-nav.svg"
              alt="SmartHire"
              width="160"
              height="26"
            />
          </div>

          {/* HEADER */}

          <div className="auth-modal-header">
            <h2 id="auth-modal-title">
              {isLogin ? "Sign in" : "Create your account"}
            </h2>

            <p className="auth-modal-subtitle">
              {isLogin
                ? "Welcome back! Enter your details to continue."
                : "Start analyzing your resume in seconds."}
            </p>
          </div>

          {/* FORM */}

          <form onSubmit={submit}>
            {/* FULL NAME — SIGNUP ONLY */}

            {!isLogin && (
              <label className="auth-modal-field">
                <span>Full name</span>

                <div>
                  <UserRound size={16} />

                  <input
                    type="text"
                    value={form.fullName}
                    onChange={(e) => update("fullName", e.target.value)}
                    placeholder="Your full name"
                    autoComplete="name"
                    required
                    disabled={busy}
                  />
                </div>
              </label>
            )}

            {/* EMAIL */}

            <label className="auth-modal-field">
              <span>Email</span>

              <div>
                <Mail size={16} />

                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => update("email", e.target.value)}
                  placeholder="you@gmail.com"
                  autoComplete="email"
                  required
                  disabled={busy}
                />
              </div>

              {!isLogin && (
                <small className="auth-modal-field-hint">
                  Please use a Gmail address.
                </small>
              )}
            </label>

            {/* PASSWORD */}

            <label className="auth-modal-field">
              <span>Password</span>

              <div>
                <LockKeyhole size={16} />

                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                  placeholder={
                    isLogin ? "Your password" : "At least 6 characters"
                  }
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  required
                  disabled={busy}
                />
              </div>
            </label>

            {/* CONFIRM PASSWORD — SIGNUP ONLY */}

            {!isLogin && (
              <label className="auth-modal-field">
                <span>Confirm password</span>

                <div>
                  <LockKeyhole size={16} />

                  <input
                    type="password"
                    value={form.confirmPassword}
                    onChange={(e) => update("confirmPassword", e.target.value)}
                    placeholder="Repeat your password"
                    autoComplete="new-password"
                    required
                    disabled={busy}
                  />
                </div>
              </label>
            )}

            {/* ERROR */}

            {error && (
              <div
                className="auth-modal-error"
                role="alert"
                aria-live="assertive"
              >
                {error}
              </div>
            )}

            {/* SUCCESS */}

            {success && (
              <div
                className="auth-modal-success"
                role="status"
                aria-live="polite"
              >
                {success}
              </div>
            )}

            {/* SUBMIT */}

            <button type="submit" className="auth-modal-submit" disabled={busy}>
              {busy
                ? isLogin
                  ? "Signing in..."
                  : "Creating account..."
                : isLogin
                  ? "Sign in"
                  : "Create account"}

              <ArrowRight size={16} />
            </button>
          </form>

          {/* SWITCH LOGIN / SIGNUP */}

          <div className="auth-modal-switch">
            {isLogin ? (
              <>
                Don't have an account?
                <button
                  type="button"
                  onClick={() => onModeChange("signup")}
                  disabled={busy}
                >
                  Create one
                </button>
              </>
            ) : (
              <>
                Already have an account?
                <button
                  type="button"
                  onClick={() => onModeChange("login")}
                  disabled={busy}
                >
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
