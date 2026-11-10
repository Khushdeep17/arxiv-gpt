import React, { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { BookOpen, Eye, EyeOff, AlertCircle, ArrowRight, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const { register, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  // If already authenticated and not loading, redirect to research dashboard
  if (!authLoading && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const validate = () => {
    if (!email.trim()) return "Email address is required.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()))
      return "Please enter a valid email address.";
    if (!password) return "Password is required.";
    if (password.length < 8)
      return "Password must be at least 8 characters long.";
    if (password !== confirmPassword)
      return "Passwords do not match. Please re-enter.";
    return null;
  };

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
      await register(email.trim(), password, fullName.trim() || undefined);
      navigate("/");
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;

      if (status === 409) {
        setError("An account with this email address already exists.");
      } else if (status === 422 && detail) {
        if (Array.isArray(detail)) {
          setError(detail[0]?.msg || "Invalid input.");
        } else {
          setError(typeof detail === "string" ? detail : "Invalid input.");
        }
      } else {
        setError("Unable to complete registration. Please try again later.");
      }
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-canvas flex flex-col justify-center py-12 sm:px-6 lg:px-8 selection:bg-indigo-600/30">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link
          to="/"
          className="inline-flex items-center gap-2.5 text-dark-primary group focus:outline-none"
        >
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-950 group-hover:bg-indigo-500 transition-colors">
            <BookOpen className="w-5 h-5" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-dark-primary">
            arXiv<span className="text-indigo-400">-GPT</span>
          </span>
        </Link>
        <h2 className="mt-6 text-2xl sm:text-3xl font-extrabold text-dark-primary tracking-tight">
          Create an account
        </h2>
        <p className="mt-2 text-sm text-dark-secondary">
          Join arXiv-GPT to save research sessions and access server-persisted history.
        </p>
      </div>

      {/* Card Form */}
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-dark-card py-8 px-6 sm:px-10 rounded-2xl border border-dark-border shadow-2xl">
          {error && (
            <div
              role="alert"
              className="mb-6 p-4 rounded-xl bg-rose-950/30 border border-rose-900/50 text-rose-300 text-sm flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label
                htmlFor="fullName"
                className="block text-sm font-medium text-dark-secondary mb-1.5"
              >
                Full name <span className="text-dark-muted font-normal">(optional)</span>
              </label>
              <input
                id="fullName"
                type="text"
                name="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. Jane Doe"
                autoComplete="name"
                disabled={pending}
                className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-dark-inset text-dark-primary text-sm
                           placeholder:text-dark-muted focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20
                           disabled:opacity-50 transition-colors"
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-dark-secondary mb-1.5"
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
                disabled={pending}
                className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-dark-inset text-dark-primary text-sm
                           placeholder:text-dark-muted focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20
                           disabled:opacity-50 transition-colors"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-dark-secondary mb-1.5"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
                  required
                  disabled={pending}
                  className="w-full px-4 py-2.5 pr-11 rounded-xl border border-dark-border bg-dark-inset text-dark-primary text-sm
                             placeholder:text-dark-muted focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20
                             disabled:opacity-50 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-dark-muted hover:text-dark-secondary focus:outline-none"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              <p className="mt-1 text-[11px] text-dark-muted">
                Must be at least 8 characters long.
              </p>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-dark-secondary mb-1.5"
              >
                Confirm password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  name="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  autoComplete="new-password"
                  required
                  disabled={pending}
                  className="w-full px-4 py-2.5 pr-11 rounded-xl border border-dark-border bg-dark-inset text-dark-primary text-sm
                             placeholder:text-dark-muted focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20
                             disabled:opacity-50 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-dark-muted hover:text-dark-secondary focus:outline-none"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={pending}
              className="w-full mt-2 flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-semibold text-white
                         bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50
                         disabled:cursor-not-allowed shadow-md shadow-indigo-950/50 transition-colors text-sm"
            >
              {pending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Creating account…</span>
                </>
              ) : (
                <>
                  <span>Create account</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-dark-border-subtle text-center text-sm text-dark-secondary">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-medium text-indigo-400 hover:text-indigo-300 hover:underline"
            >
              Sign in
            </Link>
          </div>
        </div>

        <p className="mt-8 text-center text-xs text-dark-muted">
          <Link to="/" className="text-dark-muted hover:text-dark-secondary transition-colors">
            ← Continue as guest in Research Assistant
          </Link>
        </p>
      </div>
    </div>
  );
}
