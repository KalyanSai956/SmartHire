import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const supabase =
  url && publishableKey ? createClient(url, publishableKey) : null;

const AuthContext = createContext(null);

const SESSION_DURATION = 6 * 60 * 60 * 1000;
const SESSION_EXPIRY_KEY = "smarthire_session_expires_at";

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  /*
   * Remove SmartHire's custom session expiry timestamp.
   */
  const clearSessionExpiry = () => {
    localStorage.removeItem(SESSION_EXPIRY_KEY);
  };

  /*
   * Create a SmartHire session expiry timestamp.
   */
  const setSessionExpiry = () => {
    const expiresAt = Date.now() + SESSION_DURATION;

    localStorage.setItem(SESSION_EXPIRY_KEY, String(expiresAt));
  };

  /*
   * Check SmartHire's custom session lifetime.
   */
  const isSessionExpired = () => {
    const expiresAt = Number(localStorage.getItem(SESSION_EXPIRY_KEY));

    if (!expiresAt) {
      return false;
    }

    return Date.now() >= expiresAt;
  };

  /*
   * Force logout when SmartHire's custom session
   * lifetime has expired.
   */
  const forceSignOut = async () => {
    clearSessionExpiry();

    try {
      if (supabase) {
        await supabase.auth.signOut();
      }
    } catch (error) {
      console.error("Automatic sign out error:", error);
    }

    setSession(null);
  };

  useEffect(() => {
    if (!supabase) {
      setSession(null);
      setLoading(false);
      return undefined;
    }

    let mounted = true;

    /*
     * Load the existing Supabase session exactly once
     * when the AuthProvider starts.
     */
    async function loadSession() {
      try {
        const { data, error } = await supabase.auth.getSession();

        if (!mounted) return;

        if (error) {
          console.error("Get session error:", error);

          clearSessionExpiry();
          setSession(null);

          return;
        }

        const currentSession = data?.session ?? null;

        /*
         * No existing Supabase session.
         */
        if (!currentSession) {
          clearSessionExpiry();
          setSession(null);

          return;
        }

        /*
         * Existing session has exceeded SmartHire's
         * custom session duration.
         */
        if (isSessionExpired()) {
          await forceSignOut();

          if (mounted) {
            setSession(null);
          }

          return;
        }

        /*
         * Existing Supabase session is valid.
         *
         * Create our custom expiry only if one doesn't
         * already exist.
         */
        if (!localStorage.getItem(SESSION_EXPIRY_KEY)) {
          setSessionExpiry();
        }

        setSession(currentSession);
      } catch (error) {
        console.error("Session loading error:", error);

        if (mounted) {
          clearSessionExpiry();
          setSession(null);
        }
      } finally {
        if (mounted) {
          /*
           * Authentication initialization is now complete.
           */
          setLoading(false);
        }
      }
    }

    /*
     * Start initial session loading.
     */
    loadSession();

    /*
     * Listen for future Supabase authentication events.
     */
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, nextSession) => {
      console.log("Auth event:", event);

      if (!mounted) return;

      /*
       * User explicitly signed out.
       */
      if (event === "SIGNED_OUT") {
        clearSessionExpiry();
        setSession(null);

        return;
      }

      /*
       * Successful authentication.
       *
       * IMPORTANT:
       * Update the session immediately.
       * Navigation is handled by AuthModal.
       */
      if (event === "SIGNED_IN" && nextSession) {
        setSessionExpiry();
        setSession(nextSession);

        return;
      }

      /*
       * Token/session refreshed.
       */
      if (event === "TOKEN_REFRESHED" && nextSession) {
        /*
         * If SmartHire's custom session lifetime has
         * expired, invalidate the session.
         */
        if (isSessionExpired()) {
          void forceSignOut();
          return;
        }

        setSession(nextSession);

        return;
      }

      /*
       * Other Supabase auth events with a session.
       */
      if (nextSession) {
        if (isSessionExpired()) {
          void forceSignOut();
          return;
        }

        setSession(nextSession);

        return;
      }

      /*
       * No session.
       */
      setSession(null);
    });

    /*
     * Periodically check SmartHire's custom session
     * expiration.
     */
    const interval = setInterval(async () => {
      if (!mounted) return;

      if (isSessionExpired()) {
        await forceSignOut();
      }
    }, 60 * 1000);

    /*
     * Re-check expiration when the browser tab becomes
     * visible again.
     */
    const handleVisibilityChange = async () => {
      if (!document.hidden && isSessionExpired()) {
        await forceSignOut();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    /*
     * Cleanup.
     */
    return () => {
      mounted = false;

      subscription.unsubscribe();

      clearInterval(interval);

      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  /*
   * ==========================
   * SIGN IN
   * ==========================
   */
  const signIn = async (email, password) => {
    if (!supabase) {
      throw new Error("SmartHire authentication is not configured.");
    }

    const cleanEmail = email.trim().toLowerCase();

    const { data, error } = await supabase.auth.signInWithPassword({
      email: cleanEmail,
      password,
    });

    /*
     * IMPORTANT:
     *
     * Do not modify local auth UI here when Supabase
     * rejects credentials.
     *
     * Throwing the error allows AuthModal to display
     * the error directly inside the login form.
     */
    if (error) {
      throw error;
    }

    /*
     * Successful login.
     */
    if (data?.session) {
      setSessionExpiry();
      setSession(data.session);
    }

    return {
      data,
      error: null,
    };
  };

  /*
   * ==========================
   * SIGN UP
   * ==========================
   */
  const signUp = async (email, password, fullName) => {
    if (!supabase) {
      throw new Error("SmartHire authentication is not configured.");
    }

    const cleanEmail = email.trim().toLowerCase();

    const cleanName = fullName.trim();

    const { data, error } = await supabase.auth.signUp({
      email: cleanEmail,
      password,
      options: {
        data: {
          full_name: cleanName,
        },
      },
    });

    /*
     * Signup failure stays inside AuthModal.
     */
    if (error) {
      throw error;
    }

    /*
     * Successful signup with an active session.
     */
    if (data?.session) {
      setSessionExpiry();
      setSession(data.session);
    }

    return {
      data,
      error: null,
    };
  };

  /*
   * ==========================
   * SIGN OUT
   * ==========================
   */
  const signOut = async () => {
    if (!supabase) {
      throw new Error("SmartHire authentication is not configured.");
    }

    clearSessionExpiry();

    const { error } = await supabase.auth.signOut();

    if (error) {
      console.error("Supabase sign out error:", error);

      throw error;
    }

    setSession(null);

    return true;
  };

  /*
   * Expose authentication state and methods.
   */
  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      accessToken: session?.access_token ?? null,
      loading,
      configured: Boolean(supabase),
      signIn,
      signUp,
      signOut,
    }),
    [session, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
