import React, { useState, useEffect, useCallback, useRef } from "react";

import SearchBar from "./components/SearchBar";
import PaperList from "./components/PaperList";
import HistorySidebar from "./components/HistorySidebar";
import AuthModal from "./components/AuthModal";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { searchPapers, fetchHistory } from "./services/api";

// ----------------------------------------------------------------
// AppShell — the actual app rendered inside AuthProvider.
// Separated so useAuth() is available here.
// ----------------------------------------------------------------
function AppShell() {
  const { user, isAuthenticated, loading: authLoading, logout } = useAuth();

  const [query, setQuery] = useState("self-driving cars");
  const [papers, setPapers] = useState([]);
  const [pdfFilename, setPdfFilename] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);

  // Auth modal state
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  // ---------------------------------------------------------------
  // Server-side history fetch — only when authenticated.
  // Called on login and when user identity changes.
  // ---------------------------------------------------------------
  const loadServerHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const res = await fetchHistory();
      // Map server shape { id, query, timestamp, pdf_filename, papers }
      // to the local shape { id, query, timestamp, pdfFilename, papers }
      const entries = (res.data || []).map((entry) => ({
        id: entry.id,
        query: entry.query,
        timestamp: entry.timestamp,
        pdfFilename: entry.pdf_filename || null,
        papers: Array.isArray(entry.papers) ? entry.papers : [],
      }));
      setHistory(entries);
    } catch {
      // On failure keep existing history intact; don't clear it.
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // ---------------------------------------------------------------
  // Sync history on authentication state changes.
  // ---------------------------------------------------------------
  const prevAuthRef = useRef(isAuthenticated);
  useEffect(() => {
    // Skip the initial render while auth is still resolving
    if (authLoading) return;

    if (isAuthenticated) {
      // Logged in (either on first mount with a valid token, or just signed in)
      loadServerHistory();
    } else if (prevAuthRef.current === true) {
      // Just logged out — clear history so private data is not exposed
      setHistory([]);
    }
    prevAuthRef.current = isAuthenticated;
  }, [isAuthenticated, authLoading, loadServerHistory]);

  // ---------------------------------------------------------------
  // Search handler
  // ---------------------------------------------------------------
  const handleSearch = async ({ query: q, maxResults, generatePdf }) => {
    setSearchLoading(true);
    setError("");

    try {
      const res = await searchPapers({
        query: q,
        max_results: maxResults,
        generate_pdf: generatePdf,
      });

      const paperList = res.data.papers.map((p, idx) => ({
        id: idx + 1,
        ...p,
      }));

      setPapers(paperList);
      setPdfFilename(res.data.pdf_filename);

      if (isAuthenticated) {
        // Refresh from server so history is authoritative
        loadServerHistory();
      } else {
        // Guest: maintain in-session local history
        setHistory((prev) => [
          {
            query: q,
            papers: paperList,
            pdfFilename: res.data.pdf_filename,
            timestamp: new Date().toLocaleString(),
          },
          ...prev,
        ]);
      }
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Backend connection failed"
      );
    } finally {
      setSearchLoading(false);
    }
  };

  // ---------------------------------------------------------------
  // Logout handler — also clears all private UI state
  // ---------------------------------------------------------------
  const handleLogout = () => {
    setUserMenuOpen(false);
    logout();
    // history is cleared by the useEffect above watching isAuthenticated
  };

  // ---------------------------------------------------------------
  // Close user menu when clicking outside
  // ---------------------------------------------------------------
  useEffect(() => {
    if (!userMenuOpen) return;
    const handler = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [userMenuOpen]);

  // ---------------------------------------------------------------
  // Display name helper
  // ---------------------------------------------------------------
  const displayName = user?.full_name || user?.email || "Account";

  // ---------------------------------------------------------------
  // While the auth check is in progress, render a minimal shell
  // to avoid flickering between guest and authenticated UI.
  // ---------------------------------------------------------------
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <span className="text-gray-400 text-sm animate-pulse">Loading…</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">

      {/* ── Top Header ─────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-700 bg-gray-800 shrink-0">
        <span className="text-blue-400 font-bold text-lg tracking-wide">
          arXiv-GPT
        </span>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            /* ── Authenticated user area ── */
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen((o) => !o)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-700
                           hover:bg-gray-600 transition-colors text-sm text-gray-200"
                aria-haspopup="menu"
                aria-expanded={userMenuOpen}
              >
                {/* Avatar initials */}
                <span className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center
                                  text-xs font-bold text-white uppercase select-none">
                  {(user?.full_name || user?.email || "?")[0]}
                </span>
                <span className="max-w-[160px] truncate">{displayName}</span>
                <svg
                  className={`h-4 w-4 transition-transform ${userMenuOpen ? "rotate-180" : ""}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {userMenuOpen && (
                <div
                  role="menu"
                  className="absolute right-0 mt-2 w-48 bg-gray-700 border border-gray-600
                             rounded-xl shadow-xl z-40 overflow-hidden"
                >
                  <div className="px-4 py-3 border-b border-gray-600">
                    <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                  </div>
                  <button
                    role="menuitem"
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-3 text-sm text-gray-200
                               hover:bg-gray-600 transition-colors"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* ── Guest sign-in button ── */
            <button
              onClick={() => setShowAuthModal(true)}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700
                         transition-colors text-sm font-medium text-white shadow-md"
            >
              Sign In
            </button>
          )}
        </div>
      </header>

      {/* ── Body (sidebar + main) ───────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* Sidebar */}
        <div className="hidden md:flex flex-col w-72 border-r border-gray-700 bg-gray-800 overflow-hidden">
          <HistorySidebar
            history={history}
            setPapers={setPapers}
            setPdfFilename={setPdfFilename}
            setQuery={setQuery}
            loading={historyLoading}
          />
        </div>

        {/* Main */}
        <div className="flex-1 flex flex-col items-center p-6 overflow-y-auto">
          <h1 className="text-4xl font-bold text-blue-400 mb-10 mt-4">
            arXiv-GPT: Research Assistant
          </h1>

          {!isAuthenticated && (
            <p className="text-gray-400 text-sm mb-6 -mt-6">
              Search is available without an account.{" "}
              <button
                onClick={() => setShowAuthModal(true)}
                className="text-blue-400 hover:underline"
              >
                Sign in
              </button>{" "}
              to save your history.
            </p>
          )}

          <div className="w-full max-w-3xl bg-gray-800 p-6 rounded-xl shadow-lg">
            <SearchBar
              query={query}
              setQuery={setQuery}
              onSearch={handleSearch}
              loading={searchLoading}
            />
          </div>

          {error && (
            <div className="text-red-400 mt-4 bg-gray-800 px-4 py-2 rounded">
              {error}
            </div>
          )}

          <div className="w-full max-w-4xl mt-8">
            <PaperList papers={papers} pdfFilename={pdfFilename} />
          </div>
        </div>
      </div>

      {/* Auth Modal */}
      {showAuthModal && (
        <AuthModal onClose={() => setShowAuthModal(false)} />
      )}
    </div>
  );
}

// ----------------------------------------------------------------
// App root — wraps everything in AuthProvider.
// ----------------------------------------------------------------
export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
