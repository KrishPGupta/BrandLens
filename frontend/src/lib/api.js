import { useEffect, useState } from "react";
import { API_URL } from "../config/site";

/** GET a JSON endpoint. Returns { data, live }; `data` is the fallback until (or unless) the API answers. */
export function useApi(path, fallback, pick = (d) => d) {
  const [state, setState] = useState({ data: fallback, live: false });

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}${path}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => {
        const picked = pick(json);
        if (picked) setState({ data: picked, live: true });
      })
      .catch(() => {});
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);

  return state;
}

/** GET a JSON endpoint with loading and error states. Pass null to skip. */
export function useFetch(path) {
  const [state, setState] = useState({ data: null, error: null, loading: Boolean(path) });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!path) {
      setState({ data: null, error: null, loading: false });
      return undefined;
    }
    const controller = new AbortController();
    setState({ data: null, error: null, loading: true });
    fetch(`${API_URL}${path}`, { signal: controller.signal })
      .then(async (res) => {
        if (!res.ok) {
          let message = `The API answered with an error (${res.status}).`;
          try {
            message = (await res.json()).detail || message;
          } catch {
            /* keep the default message */
          }
          throw new Error(message);
        }
        return res.json();
      })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((err) => {
        if (err.name === "AbortError") return;
        const offline = err instanceof TypeError;
        setState({
          data: null,
          loading: false,
          error: offline ? `Cannot reach the API at ${API_URL}. Start it with: python -m uvicorn api.main:app --port 8000` : err.message,
        });
      });
    return () => controller.abort();
  }, [path, tick]);

  return { ...state, reload: () => setTick((t) => t + 1) };
}
