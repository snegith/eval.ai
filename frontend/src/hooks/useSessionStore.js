import { createContext, createElement, startTransition, useContext, useEffect, useMemo, useState } from "react";
import { getSessionResults, listSessions, processUpload } from "../lib/api";
import { buildGeneratedSession, loadSessions, persistSessions } from "../lib/mockStore";
import { normalizeSessionBundle } from "../lib/sessionNormalizer";

const SessionStoreContext = createContext(null);

function sortSessions(items) {
  return [...items].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
}

function isScoredSession(session) {
  return Boolean(
    session.overallScore > 0 ||
    session.artifacts?.landmarks ||
    session.artifacts?.feedback ||
    session.status === "feedback_completed" ||
    session.status === "metrics_completed" ||
    session.status === "metrics_failed",
  );
}

async function loadSessionBundles(summaries) {
  const results = await Promise.allSettled(
    summaries.map((session) => getSessionResults(session.session_id)),
  );

  const bundles = results
    .filter((result) => result.status === "fulfilled")
    .map((result) => result.value);

  const failedCount = results.length - bundles.length;
  return { bundles, failedCount };
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
        const { bundles, failedCount } = await loadSessionBundles(summaries);
        const normalizedSessions = sortSessions(bundles.map(normalizeSessionBundle));
        if (cancelled) return;
        setMode("api");
        if (failedCount > 0) {
          setError(`${failedCount} session(s) could not be loaded and were skipped.`);
        }
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
        const { bundles, failedCount } = await loadSessionBundles(summaries);
        setSessions(sortSessions(bundles.map(normalizeSessionBundle)));
        setError(
          failedCount > 0 ? `${failedCount} session(s) could not be loaded and were skipped.` : "",
        );
      } catch (refreshError) {
        setError(refreshError.message);
      } finally {
        setLoading(false);
      }
    };

    const fetchSessionById = async (sessionId) => {
      if (!sessionId) return null;

      const cached = sessions.find((session) => session.id === sessionId);
      if (cached) return cached;

      if (mode !== "api") {
        return loadSessions().find((session) => session.id === sessionId) ?? null;
      }

      const bundle = await getSessionResults(sessionId);
      const normalizedSession = normalizeSessionBundle(bundle);
      setSessions((prev) => {
        const withoutCurrent = prev.filter((session) => session.id !== sessionId);
        return sortSessions([normalizedSession, ...withoutCurrent]);
      });
      return normalizedSession;
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
      fetchSessionById,
      getSessionById: (sessionId) => sessions.find((session) => session.id === sessionId) ?? null,
      stats: {
        totalSessions: sessions.length,
        averageScore: (() => {
          const scoredSessions = sessions.filter(isScoredSession);
          return scoredSessions.length
            ? Math.round(scoredSessions.reduce((sum, session) => sum + session.overallScore, 0) / scoredSessions.length)
            : 0;
        })(),
        bestScore: (() => {
          const scoredSessions = sessions.filter(isScoredSession);
          return scoredSessions.length ? Math.max(...scoredSessions.map((session) => session.overallScore)) : 0;
        })(),
        recentSession: sessions.find(isScoredSession) ?? sessions[0] ?? null,
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
