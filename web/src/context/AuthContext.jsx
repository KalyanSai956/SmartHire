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

  const clearSessionExpiry = () => {
    localStorage.removeItem(SESSION_EXPIRY_KEY);
  };

  const setSessionExpiry = () => {
    const expiresAt = Date.now() + SESSION_DURATION;
    localStorage.setItem(SESSION_EXPIRY_KEY, String(expiresAt));
  };

  const isSessionExpired = () => {
    const expiresAt = Number(localStorage.getItem(SESSION_EXPIRY_KEY));

    if (!expiresAt) {
      return false;
    }

    return Date.now() >= expiresAt;
  };

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
      setLoading(false);
      return;
    }

    let mounted = true;

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

        if (!currentSession) {
          clearSessionExpiry();
          setSession(null);
          return;
        }

        if (isSessionExpired()) {
          await forceSignOut();

          if (mounted) {
            setSession(null);
          }

          return;
        }

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
          setLoading(false);
        }
      }
    }

    loadSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, nextSession) => {
      console.log("Auth event:", event);

      if (!mounted) return;

      if (event === "SIGNED_OUT") {
        clearSessionExpiry();
        setSession(null);
        setLoading(false);
        return;
      }

      if (event === "SIGNED_IN") {
        setSessionExpiry();
      }

      if (nextSession && isSessionExpired()) {
        forceSignOut();
        return;
      }

      setSession(nextSession ?? null);
      setLoading(false);
    });

    const interval = setInterval(async () => {
      if (!mounted) return;

      if (isSessionExpired()) {
        await forceSignOut();
      }
    }, 60 * 1000);

    const handleVisibilityChange = async () => {
      if (!document.hidden && isSessionExpired()) {
        await forceSignOut();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      mounted = false;
      subscription.unsubscribe();
      clearInterval(interval);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  const signIn = async (email, password) => {
    if (!supabase) {
      throw new Error("SmartHire authentication is not configured.");
    }

    const cleanEmail = email.trim().toLowerCase();

    const { data, error } = await supabase.auth.signInWithPassword({
      email: cleanEmail,
      password,
    });

    if (error) {
      throw error;
    }

    if (data?.session) {
      setSessionExpiry();
      setSession(data.session);
    }

    console.log("ACCESS TOKEN:", data?.session?.access_token);

    return {
      data,
      error: null,
    };
  };

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

    if (error) {
      throw error;
    }

    if (data?.session) {
      setSessionExpiry();
      setSession(data.session);
    }

    return {
      data,
      error: null,
    };
  };

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
