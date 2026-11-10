/**
 * errorHandler.js
 *
 * Diagnostic Error Formatter for API responses.
 * Differentiates network failures, 401, 403, 422, and 5xx responses
 * without leaking sensitive credentials or raw stack traces.
 */

export function formatApiError(err, fallbackMessage = "An unexpected error occurred.") {
  // If no response was received, this is an actual network or proxy failure
  if (!err?.response) {
    if (err?.code === "ECONNABORTED" || err?.message?.toLowerCase().includes("timeout")) {
      return "Request timed out. The backend server took too long to respond.";
    }
    return "Backend connection failed. Unable to reach the server. Please verify the backend is running.";
  }

  const { status, data } = err.response;

  // 401 Unauthorized
  if (status === 401) {
    return typeof data?.detail === "string"
      ? data.detail
      : "Your session has expired or you are unauthorized. Please sign in again.";
  }

  // 403 Forbidden
  if (status === 403) {
    return typeof data?.detail === "string"
      ? data.detail
      : "Access forbidden. You do not have permission to perform this action.";
  }

  // 422 Unprocessable Entity (FastAPI parameter validation errors)
  if (status === 422) {
    if (Array.isArray(data?.detail)) {
      const messages = data.detail.map((d) => d.msg || "Invalid input").join(", ");
      return `Validation error: ${messages}`;
    }
    return typeof data?.detail === "string" ? data.detail : "Validation error. Please verify your input parameters.";
  }

  // 5xx Server Errors
  if (status >= 500) {
    return "The backend server encountered an error processing your request. Please try again later.";
  }

  // Any explicit string detail returned by FastAPI
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  return fallbackMessage;
}

