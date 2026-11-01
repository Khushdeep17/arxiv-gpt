/**
 * AuthContext.test.jsx
 *
 * Unit tests for the authentication context using
 * @testing-library/react. All network calls are mocked.
 */
import React from "react";
import { render, screen, act, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ── Mock the API module before importing AuthContext ──────────────
jest.mock("../services/api", () => ({
  tokenStorage: {
    _store: {},
    get() { return this._store["arxiv_gpt_token"] ?? null; },
    set(v) { this._store["arxiv_gpt_token"] = v; },
    clear() { delete this._store["arxiv_gpt_token"]; },
  },
  loginUser: jest.fn(),
  registerUser: jest.fn(),
  fetchCurrentUser: jest.fn(),
}));

import {
  tokenStorage,
  loginUser,
  registerUser,
  fetchCurrentUser,
} from "../services/api";

import { AuthProvider, useAuth } from "./AuthContext";

// Helper: renders a component that exposes auth context values.
function AuthConsumer({ onRender }) {
  const ctx = useAuth();
  onRender(ctx);
  return null;
}

function renderWithProvider(callback) {
  const captured = { current: null };
  const utils = render(
    <AuthProvider>
      <AuthConsumer onRender={(ctx) => { captured.current = ctx; }} />
    </AuthProvider>
  );
  return { ...utils, captured };
}

// ─────────────────────────────────────────────────────────────────
// 1. Initialization — no stored token
// ─────────────────────────────────────────────────────────────────
describe("AuthContext initialization", () => {
  beforeEach(() => {
    tokenStorage.clear();
    jest.clearAllMocks();
  });

  test("starts loading=true, resolves to guest when no token stored", async () => {
    const { captured } = renderWithProvider(() => {});

    // Initially loading
    // After effect: loading=false, user=null, isAuthenticated=false
    await waitFor(() => {
      expect(captured.current.loading).toBe(false);
    });
    expect(captured.current.isAuthenticated).toBe(false);
    expect(captured.current.user).toBeNull();
    expect(fetchCurrentUser).not.toHaveBeenCalled();
  });

  test("validates stored token on mount and hydrates user", async () => {
    const fakeUser = { id: "uuid-1", email: "a@b.com", full_name: "Alice", is_active: true };
    tokenStorage.set("valid-token");
    fetchCurrentUser.mockResolvedValueOnce({ data: fakeUser });

    const { captured } = renderWithProvider(() => {});

    await waitFor(() => {
      expect(captured.current.loading).toBe(false);
    });

    expect(captured.current.isAuthenticated).toBe(true);
    expect(captured.current.user).toEqual(fakeUser);
    expect(captured.current.token).toBe("valid-token");
  });

  test("clears credentials when stored token is expired/invalid", async () => {
    tokenStorage.set("expired-token");
    fetchCurrentUser.mockRejectedValueOnce({ response: { status: 401 } });

    const { captured } = renderWithProvider(() => {});

    await waitFor(() => {
      expect(captured.current.loading).toBe(false);
    });

    expect(captured.current.isAuthenticated).toBe(false);
    expect(captured.current.user).toBeNull();
    expect(tokenStorage.get()).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────
// 2. Login
// ─────────────────────────────────────────────────────────────────
describe("login()", () => {
  beforeEach(() => {
    tokenStorage.clear();
    jest.clearAllMocks();
    fetchCurrentUser.mockResolvedValue({ data: null }); // no stored token
  });

  test("sets token and user state on success", async () => {
    const fakeUser = { id: "uuid-2", email: "b@c.com", full_name: null, is_active: true };
    loginUser.mockResolvedValueOnce({
      data: { access_token: "tok-abc", token_type: "bearer", user: fakeUser },
    });

    const { captured } = renderWithProvider(() => {});
    await waitFor(() => expect(captured.current.loading).toBe(false));

    await act(async () => {
      await captured.current.login("b@c.com", "password1");
    });

    expect(captured.current.isAuthenticated).toBe(true);
    expect(captured.current.user).toEqual(fakeUser);
    expect(tokenStorage.get()).toBe("tok-abc");
  });

  test("propagates error on failed login", async () => {
    loginUser.mockRejectedValueOnce({ response: { status: 401, data: { detail: "Invalid email or password" } } });

    const { captured } = renderWithProvider(() => {});
    await waitFor(() => expect(captured.current.loading).toBe(false));

    await expect(
      act(async () => { await captured.current.login("x@y.com", "wrong"); })
    ).rejects.toBeTruthy();

    expect(captured.current.isAuthenticated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────
// 3. Register
// ─────────────────────────────────────────────────────────────────
describe("register()", () => {
  beforeEach(() => {
    tokenStorage.clear();
    jest.clearAllMocks();
    fetchCurrentUser.mockResolvedValue({ data: null });
  });

  test("sets token and user state after successful registration", async () => {
    const fakeUser = { id: "uuid-3", email: "c@d.com", full_name: "Carol", is_active: true };
    registerUser.mockResolvedValueOnce({
      data: { access_token: "tok-reg", token_type: "bearer", user: fakeUser },
    });

    const { captured } = renderWithProvider(() => {});
    await waitFor(() => expect(captured.current.loading).toBe(false));

    await act(async () => {
      await captured.current.register("c@d.com", "password1", "Carol");
    });

    expect(captured.current.isAuthenticated).toBe(true);
    expect(captured.current.user.email).toBe("c@d.com");
    expect(tokenStorage.get()).toBe("tok-reg");
  });
});

// ─────────────────────────────────────────────────────────────────
// 4. Logout
// ─────────────────────────────────────────────────────────────────
describe("logout()", () => {
  beforeEach(() => {
    tokenStorage.clear();
    jest.clearAllMocks();
  });

  test("clears token, user, and isAuthenticated", async () => {
    const fakeUser = { id: "uuid-4", email: "d@e.com", full_name: null, is_active: true };
    tokenStorage.set("tok-logout");
    fetchCurrentUser.mockResolvedValueOnce({ data: fakeUser });

    const { captured } = renderWithProvider(() => {});
    await waitFor(() => expect(captured.current.loading).toBe(false));
    expect(captured.current.isAuthenticated).toBe(true);

    act(() => { captured.current.logout(); });

    expect(captured.current.isAuthenticated).toBe(false);
    expect(captured.current.user).toBeNull();
    expect(tokenStorage.get()).toBeNull();
  });
});

