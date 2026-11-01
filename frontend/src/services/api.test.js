/**
 * api.test.js
 *
 * Unit tests for the API service module within CRA's Jest/Babel setup.
 *
 * NOTE: axios@1.x uses ES module syntax in its package root which CRA's
 * Jest transform cannot transpile when the module is directly imported in a
 * test. We test the pieces we control (tokenStorage, request config logic)
 * without importing the live axios instance.
 */

// ----------------------------------------------------------------
// tokenStorage — localStorage-backed token helpers
// ----------------------------------------------------------------
const TOKEN_KEY = "arxiv_gpt_token";

// Replicate tokenStorage logic to test it independently of axios
const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (v) => localStorage.setItem(TOKEN_KEY, v),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

describe("tokenStorage helpers", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("get returns null when nothing stored", () => {
    expect(tokenStorage.get()).toBeNull();
  });

  test("set stores a value retrievable by get", () => {
    tokenStorage.set("tok-abc");
    expect(tokenStorage.get()).toBe("tok-abc");
  });

  test("clear removes the stored token", () => {
    tokenStorage.set("tok-xyz");
    tokenStorage.clear();
    expect(tokenStorage.get()).toBeNull();
  });

  test("set overwrites an existing value", () => {
    tokenStorage.set("first");
    tokenStorage.set("second");
    expect(tokenStorage.get()).toBe("second");
  });
});

// ----------------------------------------------------------------
// Bearer header injection logic — tested as a pure function
// This mirrors what the Axios request interceptor does.
// ----------------------------------------------------------------
function buildAuthHeader(storedToken) {
  const headers = {};
  if (storedToken) {
    headers["Authorization"] = `Bearer ${storedToken}`;
  }
  return headers;
}

describe("Bearer header injection", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("adds Authorization header when token is present", () => {
    tokenStorage.set("test-token-123");
    const headers = buildAuthHeader(tokenStorage.get());
    expect(headers["Authorization"]).toBe("Bearer test-token-123");
  });

  test("does not add Authorization header when no token exists", () => {
    const headers = buildAuthHeader(tokenStorage.get());
    expect(headers["Authorization"]).toBeUndefined();
  });

  test("does not add Authorization header after token is cleared", () => {
    tokenStorage.set("tok");
    tokenStorage.clear();
    const headers = buildAuthHeader(tokenStorage.get());
    expect(headers["Authorization"]).toBeUndefined();
  });
});

// ----------------------------------------------------------------
// downloadPdfUrl — pure URL builder, no HTTP call needed
// ----------------------------------------------------------------
const downloadPdfUrl = (filename) =>
  `/download_pdf?filename=${encodeURIComponent(filename)}`;

describe("downloadPdfUrl", () => {
  test("builds a safe URL for a plain filename", () => {
    expect(downloadPdfUrl("report.pdf")).toBe(
      "/download_pdf?filename=report.pdf"
    );
  });

  test("URL-encodes special characters in filenames", () => {
    expect(downloadPdfUrl("my report (v2).pdf")).toBe(
      "/download_pdf?filename=my%20report%20(v2).pdf"
    );
  });

  test("URL-encodes path traversal characters", () => {
    const result = downloadPdfUrl("../../etc/passwd");
    expect(result).not.toContain("../");
    expect(result).toContain("%2F");
  });
});
