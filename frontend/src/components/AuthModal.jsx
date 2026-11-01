import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";

// ----------------------------------------------------------------
// AuthModal — two-mode (sign in / create account) auth modal.
// Follows the dark-theme design language of the app.
// ----------------------------------------------------------------
export default function AuthModal({ onClose }) {
  const { login, register } = useAuth();

  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  // Focus the first input when mode changes
  const firstInputRef = useRef(null);
  useEffect(() => {
    firstInputRef.current?.focus();
  }, [mode]);

  // Close on Escape key
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  // ---------------------------------------------------------------
  // Client-side validation
  // ---------------------------------------------------------------
  const validate = () => {
    if (!email.trim()) return "Email is required.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()))
      return "Enter a valid email address.";
    if (!password) return "Password is required.";
    if (mode === "register" && password.length < 8)
      return "Password must be at least 8 characters.";
    return null;
  };

  // ---------------------------------------------------------------
  // Submit handler
  // ---------------------------------------------------------------
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setPending(true);
    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(email.trim(), password, fullName.trim() || undefined);
      }
      onClose();
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;

      // Surface backend messages selectively; avoid leaking internals.
      if (status === 409) {
        setError("An account with this email already exists.");
      } else if (status === 401) {
        setError("Invalid email or password.");
      } else if (status === 422 && detail) {
        // Pydantic validation error — extract first message
        if (Array.isArray(detail)) {
          setError(detail[0]?.msg || "Invalid input.");
        } else {
          setError(typeof detail === "string" ? detail : "Invalid input.");
        }
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setPending(false);
    }
  };

  // ---------------------------------------------------------------
  // Switch mode and clear state
  // ---------------------------------------------------------------
  const switchMode = () => {
    setMode((m) => (m === "login" ? "register" : "login"));
    setError("");
    setEmail("");
    setPassword("");
    setFullName("");
  };

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
    >
      {/* Panel */}
      <div className="relative w-full max-w-md mx-4 bg-gray-800 rounded-2xl shadow-2xl border border-gray-700 p-8">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
          aria-label="Close authentication dialog"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* Title */}
        <h2
          id="auth-modal-title"
          className="text-2xl font-bold text-blue-400 mb-6 text-center"
        >
          {mode === "login" ? "Sign In" : "Create Account"}
        </h2>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
          {/* Full name — register only */}
          {mode === "register" && (
            <div>
              <label
                htmlFor="auth-fullname"
                className="block text-sm text-gray-300 mb-1"
              >
                Full Name <span className="text-gray-500">(optional)</span>
              </label>
              <input
                ref={firstInputRef}
                id="auth-fullname"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Smith"
                autoComplete="name"
                disabled={pending}
                className="w-full p-3 rounded-lg bg-gray-700 text-gray-100 border border-gray-600
                           focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              />
            </div>
          )}

          {/* Email */}
          <div>
            <label
              htmlFor="auth-email"
              className="block text-sm text-gray-300 mb-1"
            >
              Email
            </label>
            <input
              ref={mode === "login" ? firstInputRef : undefined}
              id="auth-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              disabled={pending}
              required
              className="w-full p-3 rounded-lg bg-gray-700 text-gray-100 border border-gray-600
                         focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="auth-password"
              className="block text-sm text-gray-300 mb-1"
            >
              Password
              {mode === "register" && (
                <span className="text-gray-500 ml-1">(min. 8 characters)</span>
              )}
            </label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={
                mode === "register" ? "At least 8 characters" : "Your password"
              }
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
              disabled={pending}
              required
              className="w-full p-3 rounded-lg bg-gray-700 text-gray-100 border border-gray-600
                         focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
          </div>

          {/* Error */}
          {error && (
            <p
              role="alert"
              className="text-sm text-red-400 bg-red-900/30 border border-red-800 rounded-lg px-3 py-2"
            >
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={pending}
            className="w-full py-3 rounded-lg font-semibold text-white
                       bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600
                       disabled:cursor-not-allowed transition-colors shadow-md"
          >
            {pending
              ? mode === "login"
                ? "Signing in…"
                : "Creating account…"
              : mode === "login"
              ? "Sign In"
              : "Create Account"}
          </button>
        </form>

        {/* Mode switcher */}
        <p className="mt-5 text-center text-sm text-gray-400">
          {mode === "login" ? (
            <>
              Don't have an account?{" "}
              <button
                onClick={switchMode}
                className="text-blue-400 hover:underline focus:outline-none"
              >
                Create one
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={switchMode}
                className="text-blue-400 hover:underline focus:outline-none"
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}

