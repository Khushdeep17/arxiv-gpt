import React, { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen,
  Menu,
  X,
  LogOut,
  AlertCircle,
  ChevronDown,
  Sparkles,
} from "lucide-react";

import SearchBar from "../components/SearchBar";
import PaperList from "../components/PaperList";
import HistorySidebar from "../components/HistorySidebar";
import { useAuth } from "../context/AuthContext";
import { searchPapers, fetchHistory, formatApiError } from "../services/api";

// ----------------------------------------------------------------
// WorkspacePage — Main Research Assistant Dashboard
// ----------------------------------------------------------------
export default function WorkspacePage() {
  const { user, isAuthenticated, loading: authLoading, logout } = useAuth();

  const [query, setQuery] = useState("self-driving cars");
  const [papers, setPapers] = useState([]);
  const [pdfFilename, setPdfFilename] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);

  // Mobile drawer state
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  // User menu dropdown state
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  // ---------------------------------------------------------------
  // Server-side history fetch for authenticated users
  // ---------------------------------------------------------------
  const loadServerHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const res = await fetchHistory();
      const entries = (res.data || []).map((entry) => ({
        id: entry.id,
        query: entry.query,
        timestamp: entry.timestamp,
        pdfFilename: entry.pdf_filename || null,
        papers: Array.isArray(entry.papers) ? entry.papers : [],
      }));
      setHistory(entries);
    } catch {
      // Keep existing local state on network error
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Sync history on auth state change
  const prevAuthRef = useRef(isAuthenticated);
  useEffect(() => {
    if (authLoading) return;

    if (isAuthenticated) {
      loadServerHistory();
    } else if (prevAuthRef.current === true) {
      // Clear private history immediately on logout
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

      const paperList = (res.data?.papers || []).map((p, idx) => ({
        id: idx + 1,
        ...p,
      }));

      setPapers(paperList);
      setPdfFilename(res.data?.pdf_filename || null);

      if (isAuthenticated) {
        loadServerHistory();
      } else {
        setHistory((prev) => [
          {
            query: q,
            papers: paperList,
            pdfFilename: res.data?.pdf_filename || null,
            timestamp: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
          ...prev,
        ]);
      }
    } catch (err) {
      setError(formatApiError(err, "Failed to complete research search."));
    } finally {
      setSearchLoading(false);
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    if (!userMenuOpen) return;
    const handleClick = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [userMenuOpen]);

  const handleLogout = () => {
    setUserMenuOpen(false);
    logout();
  };

  const displayName = user?.full_name || user?.email?.split("@")[0] || "Researcher";
  const userInitials = (user?.full_name || user?.email || "R")
    .substring(0, 2)
    .toUpperCase();

  return (
    <div className="min-h-screen bg-dark-canvas text-dark-primary flex flex-col selection:bg-indigo-600/30">
      {/* ── Top Navigation Bar ────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-dark-sidebar/95 backdrop-blur-md border-b border-dark-border-subtle px-4 sm:px-6 py-3 shrink-0 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Left Brand Identity */}
          <div className="flex items-center gap-3">
            {/* Mobile History Drawer Toggle */}
            <button
              type="button"
              onClick={() => setMobileDrawerOpen(true)}
              className="md:hidden p-2 rounded-xl text-dark-secondary hover:text-dark-primary hover:bg-dark-card transition-colors"
              aria-label="Open history sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>

            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-950 group-hover:bg-indigo-500 transition-colors">
                <BookOpen className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold tracking-tight text-dark-primary leading-none">
                  arXiv<span className="text-indigo-400">-GPT</span>
                </span>
                <span className="text-[10px] font-medium text-dark-muted tracking-wide mt-0.5">
                  Scientific Literature Synthesis
                </span>
              </div>
            </Link>
          </div>

          {/* Right Profile / Auth Area */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <div className="relative" ref={userMenuRef}>
                <button
                  type="button"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-xl border border-dark-border hover:border-slate-700
                             bg-dark-card hover:bg-dark-card-hover transition-colors text-xs font-semibold text-dark-secondary hover:text-dark-primary shadow-xs"
                  aria-expanded={userMenuOpen}
                  aria-haspopup="menu"
                >
                  <span className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center text-xs font-bold">
                    {userInitials}
                  </span>
                  <span className="max-w-[130px] truncate hidden sm:inline text-dark-primary">
                    {displayName}
                  </span>
                  <ChevronDown className={`w-3.5 h-3.5 text-dark-muted transition-transform ${userMenuOpen ? "rotate-180" : ""}`} />
                </button>

                {userMenuOpen && (
                  <div
                    role="menu"
                    className="absolute right-0 mt-2 w-56 rounded-2xl bg-dark-card border border-dark-border shadow-2xl py-1.5 z-40 text-xs animate-fadeIn"
                  >
                    <div className="px-4 py-3 border-b border-dark-border-subtle">
                      <p className="font-semibold text-dark-primary truncate">
                        {user?.full_name || "Signed in"}
                      </p>
                      <p className="text-dark-muted truncate text-[11px] mt-0.5">
                        {user?.email}
                      </p>
                    </div>

                    <button
                      type="button"
                      role="menuitem"
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 text-dark-secondary hover:bg-dark-card-hover hover:text-rose-400 transition-colors font-medium text-left"
                    >
                      <LogOut className="w-4 h-4 text-dark-muted group-hover:text-rose-400" />
                      <span>Sign out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-dark-secondary hover:text-dark-primary hover:bg-dark-subtle transition-colors"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-sm shadow-indigo-950 transition-colors"
                >
                  Create account
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ── Main Workspace Layout ────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop History Sidebar */}
        <div className="hidden md:block w-72 lg:w-80 border-r border-dark-border-subtle bg-dark-sidebar shrink-0 overflow-hidden">
          <HistorySidebar
            history={history}
            setPapers={setPapers}
            setPdfFilename={setPdfFilename}
            setQuery={setQuery}
            loading={historyLoading}
          />
        </div>

        {/* Mobile History Drawer Overlay */}
        {mobileDrawerOpen && (
          <div className="fixed inset-0 z-50 md:hidden flex">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black/70 backdrop-blur-xs transition-opacity"
              onClick={() => setMobileDrawerOpen(false)}
            />

            {/* Slide-in Panel */}
            <div className="relative w-72 max-w-[80vw] bg-dark-sidebar h-full shadow-2xl flex flex-col z-10 border-r border-dark-border">
              <div className="p-3 border-b border-dark-border-subtle flex items-center justify-between">
                <span className="text-xs font-bold text-dark-primary">Research History</span>
                <button
                  type="button"
                  onClick={() => setMobileDrawerOpen(false)}
                  className="p-1 rounded-lg text-dark-muted hover:text-dark-primary hover:bg-dark-subtle"
                  aria-label="Close drawer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                <HistorySidebar
                  history={history}
                  setPapers={setPapers}
                  setPdfFilename={setPdfFilename}
                  setQuery={setQuery}
                  loading={historyLoading}
                  onItemClick={() => setMobileDrawerOpen(false)}
                />
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-8 sm:py-10">
          <div className="max-w-4xl mx-auto space-y-8">
            {/* Header Hero Section */}
            <div className="text-center sm:text-left space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/60 border border-indigo-800/40 text-indigo-300 text-xs font-medium">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Autonomous Literature Intelligence</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-dark-primary tracking-tight">
                Explore & Synthesize arXiv Research
              </h1>
              <p className="text-sm sm:text-base text-dark-secondary max-w-2xl">
                Search current scientific papers, extract structured TL;DR summaries, key contributions, and download complete executive PDF dossiers.
              </p>
            </div>

            {/* Guest Session Notice */}
            {!isAuthenticated && (
              <div className="p-4 rounded-xl bg-dark-card/70 border border-dark-border text-xs text-dark-secondary flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
                <p>
                  You are currently searching in <strong className="text-dark-primary">guest mode</strong>. Your queries are saved only in this session.
                </p>
                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    to="/login"
                    className="font-semibold text-indigo-400 hover:text-indigo-300 hover:underline"
                  >
                    Sign in
                  </Link>
                  <span>or</span>
                  <Link
                    to="/register"
                    className="font-semibold text-indigo-400 hover:text-indigo-300 hover:underline"
                  >
                    Create account
                  </Link>
                </div>
              </div>
            )}

            {/* Search Input Section */}
            <SearchBar
              query={query}
              setQuery={setQuery}
              onSearch={handleSearch}
              loading={searchLoading}
            />

            {/* Error Notification */}
            {error && (
              <div
                role="alert"
                className="p-4 rounded-xl bg-rose-950/30 border border-rose-900/50 text-rose-300 text-sm flex items-start gap-3 shadow-xs"
              >
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-rose-200">Search Encountered an Error</h4>
                  <p className="mt-0.5 text-xs text-rose-300/90">{error}</p>
                </div>
              </div>
            )}

            {/* Paper Results Section */}
            <PaperList papers={papers} pdfFilename={pdfFilename} />
          </div>
        </main>
      </div>
    </div>
  );
}

