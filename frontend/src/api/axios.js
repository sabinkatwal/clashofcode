import axios from "axios";

/**
 * ==============================
 * CONFIGURATION
 * ==============================
 */

const RENDER_API = "https://clashofcode-4cz0.onrender.com";

// Render is now the single main API for local dev, Vercel preview, and production.
export const API_BASE_URL = RENDER_API;

/**
 * All /rooms/*, matchmaking, and everything else live on Render.
 * Kept as a function for future extensibility (e.g. a forceLocal flag
 * if you ever want to spin up a local backend again).
 */
function chooseApiInstance() {
    return renderAPI;
}

/**
 * Central request handler. `options` may contain { method, data, config }.
 */
export async function requestAPI(url, options = {}) {
    const method = (options.method || "get").toLowerCase();
    const data = options.data;
    const config = options.config || {};

    const instance = chooseApiInstance();

    // Ensure Authorization header is set if token exists in localStorage.
    try {
        const stored = localStorage.getItem("clashofcode_token");
        const header = stored && stored !== "undefined" ? `Bearer ${stored}` : null;
        if (header && !instance.defaults.headers.common.Authorization) {
            instance.defaults.headers.common.Authorization = header;
        }
    } catch (e) {
        // ignore (e.g., non-browser env)
    }

    try {
        if (method === "get") {
            return await instance.get(url, { params: data, ...config });
        }
        // for post/put/patch/delete, axios expects (url, data, config)
        return await instance[method](url, data, config);
    } catch (err) {
        const httpStatus = err?.response?.status;
        const detail = err?.response?.data?.detail || err?.message || "Request failed";
        console.error(`❌ Render API request failed for ${url} [${httpStatus ?? "network"}]:`, detail);
        throw err;
    }
}

/**
 * ==============================
 * AXIOS INSTANCE
 * ==============================
 */
const renderAPI = axios.create({
    baseURL: RENDER_API,
    timeout: 8000,
});

// Attach auth token from localStorage
function attachAuthInterceptors(instance) {
    instance.interceptors.request.use(
        (config) => {
            try {
                const stored = localStorage.getItem("clashofcode_token");
                if (stored && stored !== "undefined") {
                    config.headers = config.headers || {};
                    config.headers.Authorization = `Bearer ${stored}`;
                }
            } catch (e) {
                // ignore
            }
            return config;
        },
        (err) => Promise.reject(err)
    );

    instance.interceptors.response.use(
        (res) => res,
        (err) => Promise.reject(err)
    );
}

attachAuthInterceptors(renderAPI);

/**
 * Keep the old smart fallback util for code that used it directly.
 */
export const apiRequest = async (config) => {
    try {
        const response = await renderAPI(config);
        return response.data;
    } catch (error) {
        console.warn("⚠ Render request failed:", error?.response?.data?.detail || error?.message);
        throw error;
    }
};

export const render = renderAPI;

/**
 * Set or remove Authorization header on the API instance.
 * @param {string|null} token
 */
export function setAuthToken(token) {
    if (token) {
        renderAPI.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
        delete renderAPI.defaults.headers.common.Authorization;
    }
}

/**
 * Backwards-compatible default API object that routes requests to Render.
 * It exposes `get`, `post`, `put`, `delete`, and `defaults` so existing code continues to work.
 */
const api = {
    defaults: renderAPI.defaults,
    get: (url, config = {}) => requestAPI(url, { method: "get", data: config.params, config }),
    post: (url, data, config = {}) => requestAPI(url, { method: "post", data, config }),
    put: (url, data, config = {}) => requestAPI(url, { method: "put", data, config }),
    patch: (url, data, config = {}) => requestAPI(url, { method: "patch", data, config }),
    delete: (url, data, config = {}) => requestAPI(url, { method: "delete", data, config }),
};

export default api;