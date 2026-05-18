import { useEffect, useState } from "react";

export function usePageLoadState(delay = 420) {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timeout = window.setTimeout(() => setLoading(false), delay);
    return () => window.clearTimeout(timeout);
  }, [delay]);

  return loading;
}
