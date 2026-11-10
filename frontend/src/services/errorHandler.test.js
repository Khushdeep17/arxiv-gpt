import { formatApiError } from "./errorHandler";

describe("formatApiError", () => {
  test("handles undefined response as network error", () => {
    const error = new Error("Network Error");
    const result = formatApiError(error);
    expect(result).toBe(
      "Backend connection failed. Unable to reach the server. Please verify the backend is running."
    );
  });

  test("handles timeout error specifically", () => {
    const error = { code: "ECONNABORTED", message: "timeout of 5000ms exceeded" };
    const result = formatApiError(error);
    expect(result).toBe("Request timed out. The backend server took too long to respond.");
  });

  test("handles 401 with string detail", () => {
    const error = {
      response: {
        status: 401,
        data: { detail: "Invalid email or password" },
      },
    };
    expect(formatApiError(error)).toBe("Invalid email or password");
  });

  test("handles 401 with default message when detail is missing", () => {
    const error = {
      response: {
        status: 401,
        data: {},
      },
    };
    expect(formatApiError(error)).toBe(
      "Your session has expired or you are unauthorized. Please sign in again."
    );
  });

  test("handles 403 forbidden", () => {
    const error = {
      response: {
        status: 403,
        data: { detail: "Access forbidden. User not permitted." },
      },
    };
    expect(formatApiError(error)).toBe("Access forbidden. User not permitted.");
  });

  test("handles 422 with FastAPI validation array", () => {
    const error = {
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ["body", "query"], msg: "Query too short", type: "value_error" },
            { loc: ["body", "max_results"], msg: "Must be greater than 0", type: "value_error" },
          ],
        },
      },
    };
    expect(formatApiError(error)).toBe(
      "Validation error: Query too short, Must be greater than 0"
    );
  });

  test("handles 422 with string detail", () => {
    const error = {
      response: {
        status: 422,
        data: { detail: "Query length must be at least 3 characters" },
      },
    };
    expect(formatApiError(error)).toBe("Query length must be at least 3 characters");
  });

  test("handles 500 internal server error cleanly", () => {
    const error = {
      response: {
        status: 500,
        data: { detail: "Database connection failed secretly" },
      },
    };
    expect(formatApiError(error)).toBe(
      "The backend server encountered an error processing your request. Please try again later."
    );
  });

  test("handles 400 Bad Request with detail", () => {
    const error = {
      response: {
        status: 400,
        data: { detail: "Query too short" },
      },
    };
    expect(formatApiError(error)).toBe("Query too short");
  });

  test("uses fallback message when no specific detail is available", () => {
    const error = {
      response: {
        status: 418,
        data: null,
      },
    };
    expect(formatApiError(error, "Custom fallback")).toBe("Custom fallback");
  });
});

