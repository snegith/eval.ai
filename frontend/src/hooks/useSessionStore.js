import { createContext, createElement, startTransition, useContext, useEffect, useMemo, useState } from "react";
import { getSessionResults, listSessions, processUpload } from "../lib/api";
import { buildGeneratedSession, loadSessions, persistSessions } from "../lib/mockStore";
import { normalizeSessionBundle } from "../lib/sessionNormalizer";

const SessionStoreContext = createContext(null);

function sortSessions(items) {
  return [...items].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
}

export function SessionStoreProvider({ children }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState("api");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      setLoading(true);
      setError("");

      try {
        const summaries = await listSessions();
        const bundles = await Promise.all(summaries.map((session) => getSessionResults(session.session_id)));
        const normalizedSessions = sortSessions(bundles.map(normalizeSessionBundle));
        if (cancelled) return;
        setMode("api");
        startTransition(() => {
          setSessions(normalizedSessions);
        });
      } catch (apiError) {
        if (cancelled) return;
        setMode("mock");
        setError(apiError.message);
        startTransition(() => {
          setSessions(sortSessions(loadSessions()));
        });
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo(() => {
    const addGeneratedSession = (file) => {
      const session = buildGeneratedSession(file);
      setSessions((prev) => {
        const next = sortSessions([session, ...prev]);
        persistSessions(next);
        return next;
      });
      return session;
    };

    const refreshSessions = async () => {
      if (mode !== "api") {
        setSessions(sortSessions(loadSessions()));
        return;
      }

      setLoading(true);
      try {
        const summaries = await listSessions();
        const bundles = await Promise.all(summaries.map((session) => getSessionResults(session.session_id)));
        setSessions(sortSessions(bundles.map(normalizeSessionBundle)));
        setError("");
      } catch (refreshError) {
        setError(refreshError.message);
      } finally {
        setLoading(false);
      }
    };

    const createAndProcessSession = async (file, options = {}) => {
      if (mode !== "api") {
        return addGeneratedSession(file);
      }

      const response = await processUpload(file, options);
      const normalizedSession = normalizeSessionBundle(response.data.bundle);
      setSessions((prev) => sortSessions([normalizedSession, ...prev.filter((session) => session.id !== normalizedSession.id)]));
      setError("");
      return normalizedSession;
    };

    return {
      sessions,
      loading,
      error,
      mode,
      createAndProcessSession,
      refreshSessions,
      getSessionById: (sessionId) => sessions.find((session) => session.id === sessionId) ?? null,
      stats: {
        totalSessions: sessions.length,
        averageScore: sessions.length
          ? Math.round(sessions.reduce((sum, session) => sum + session.overallScore, 0) / sessions.length)
          : 0,
        bestScore: sessions.length ? Math.max(...sessions.map((session) => session.overallScore)) : 0,
        recentSession: sessions[0] ?? null,
      },
    };
  }, [error, loading, mode, sessions]);

  return createElement(SessionStoreContext.Provider, { value }, children);
}

export function useSessionStore() {
  const context = useContext(SessionStoreContext);
  if (!context) {
    throw new Error("useSessionStore must be used within SessionStoreProvider");
  }
  return context;
}
