// 简单 fetch 封装，日志可追踪，后续对接 Phase2 OpenAPI。
const API_BASE = "/orica/api";

export async function apiGet<T>(path: string): Promise<T | null> {
  const url = `${API_BASE}${path}`;
  console.log("[apiGet]", url);
  try {
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) {
      console.log("[apiGet] non-200", res.status);
      return null;
    }
    return (await res.json()) as T;
  } catch (err) {
    console.log("[apiGet] error", err);
    return null;
  }
}

export async function apiPost<T>(path: string, body: Record<string, unknown>): Promise<T | null> {
  const url = `${API_BASE}${path}`;
  console.log("[apiPost]", url, body);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      console.log("[apiPost] non-200", res.status);
      return null;
    }
    return (await res.json()) as T;
  } catch (err) {
    console.log("[apiPost] error", err);
    return null;
  }
}
