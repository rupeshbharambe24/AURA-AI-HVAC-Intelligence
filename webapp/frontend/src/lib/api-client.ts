export const getBaseUrl = () => {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem("api_base_url");
    if (!saved || saved === "http://localhost:8000") {
      const migrated = "http://localhost:8001";
      localStorage.setItem("api_base_url", migrated);
      return migrated;
    }
    return saved;
  }
  return "http://localhost:8001";
};

export const isMockMode = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("mock_mode") === "true";
  }
  return false;
};

interface RequestOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, string>;
  headers?: Record<string, string>;
}

interface ApiCallLog {
  method: string;
  url: string;
  status: number;
  duration: number;
  timestamp: Date;
  error?: string;
  requestId?: string;
}

const apiCallLog: ApiCallLog[] = [];

export const getApiCallLog = () => [...apiCallLog];
export const clearApiCallLog = () => { apiCallLog.length = 0; };

export class ApiError extends Error {
  status: number;
  requestId?: string;
  details?: unknown;
  constructor(message: string, status: number, requestId?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
    this.details = details;
  }
}

async function parseJsonSafe(res: Response): Promise<any | null> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, params, headers } = options;
  const base = getBaseUrl();
  const url = new URL(`/api/v1${endpoint}`, base);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const start = performance.now();
  try {
    const res = await fetch(url.toString(), {
      method,
      headers: { "Content-Type": "application/json", ...(headers || {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    const duration = performance.now() - start;
    const responseData = await parseJsonSafe(res);
    const requestId = res.headers.get("x-request-id") || responseData?.request_id;
    apiCallLog.push({ method, url: url.toString(), status: res.status, duration, timestamp: new Date(), requestId });
    if (apiCallLog.length > 100) apiCallLog.shift();
    if (!res.ok) {
      const message = responseData?.message || responseData?.error || `API error: ${res.status}`;
      throw new ApiError(message, res.status, requestId, responseData);
    }
    return responseData as T;
  } catch (err) {
    const duration = performance.now() - start;
    const requestId = err instanceof ApiError ? err.requestId : undefined;
    apiCallLog.push({ method, url: url.toString(), status: 0, duration, timestamp: new Date(), error: String(err), requestId });
    throw err;
  }
}

export const apiGet = <T>(endpoint: string, params?: Record<string, string>) =>
  apiClient<T>(endpoint, { method: "GET", params });

export const apiPost = <T>(endpoint: string, body?: unknown) =>
  apiClient<T>(endpoint, { method: "POST", body });

export async function apiUpload<T>(endpoint: string, form: FormData): Promise<T> {
  const base = getBaseUrl();
  const url = new URL(`/api/v1${endpoint}`, base);
  const start = performance.now();
  try {
    const res = await fetch(url.toString(), {
      method: "POST",
      body: form,
    });
    const duration = performance.now() - start;
    const responseData = await parseJsonSafe(res);
    const requestId = res.headers.get("x-request-id") || responseData?.request_id;
    apiCallLog.push({ method: "POST", url: url.toString(), status: res.status, duration, timestamp: new Date(), requestId });
    if (!res.ok) {
      const message = responseData?.message || responseData?.error || `API error: ${res.status}`;
      throw new ApiError(message, res.status, requestId, responseData);
    }
    return responseData as T;
  } catch (err) {
    const duration = performance.now() - start;
    const requestId = err instanceof ApiError ? err.requestId : undefined;
    apiCallLog.push({ method: "POST", url: url.toString(), status: 0, duration, timestamp: new Date(), error: String(err), requestId });
    throw err;
  }
}
