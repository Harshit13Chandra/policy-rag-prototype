export const API_BASE_URL = "http://localhost:8000/api/v1";

let accessToken = null;

export function setAccessToken(token) {
    accessToken = token;
}

export function getAccessToken() {
    return accessToken;
}

export async function apiFetch(path, options = {}) {
    const url = API_BASE_URL + path;
    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };

    if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const fetchOptions = {
        ...options,
        headers,
        credentials: "include"
    };

    let response = await fetch(url, fetchOptions);

    // Handle 401 Unauthorized by attempting a silent refresh
    if (response.status === 401 && !options._isRetry && path !== "/auth/login" && path !== "/auth/refresh") {
        try {
            const refreshResponse = await fetch(API_BASE_URL + "/auth/refresh", {
                method: "POST",
                credentials: "include"
            });

            if (refreshResponse.ok) {
                const refreshData = await refreshResponse.json();
                setAccessToken(refreshData.access_token);
                
                // Retry the original request with the new token
                return await apiFetch(path, { ...options, _isRetry: true });
            } else {
                throw new Error("Refresh failed");
            }
        } catch (error) {
            // Refresh failed, redirect to login
            window.location.href = "login.html";
            throw new Error("Session expired. Please log in again.");
        }
    }

    if (!response.ok) {
        let errorMessage = `HTTP Error ${response.status}`;
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
        } catch (e) {
            // Ignore JSON parse errors for non-JSON responses
        }
        throw new Error(errorMessage);
    }

    if (response.status === 204) {
        return null;
    }

    return await response.json();
}
