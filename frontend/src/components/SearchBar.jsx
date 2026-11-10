import React, { useState } from "react";
import { Search, SlidersHorizontal, FileText, Sparkles, Loader2 } from "lucide-react";

const SUGGESTIONS = [
  "Transformers",
  "Reinforcement Learning",
  "Self-Driving Cars",
  "Quantum Computing",
  "Diffusion Models",
];

export default function SearchBar({ query, setQuery, onSearch, loading }) {
  const [maxResults, setMaxResults] = useState(3);
  const [generatePdf, setGeneratePdf] = useState(true);
  const [validationError, setValidationError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query || query.trim().length < 3) {
      setValidationError("Search query must be at least 3 characters long.");
      return;
    }
    setValidationError("");
    onSearch({ query: query.trim(), maxResults, generatePdf });
  };

  const handleSuggestionClick = (topic) => {
    setQuery(topic);
    setValidationError("");
    onSearch({ query: topic, maxResults, generatePdf });
  };

  return (
    <div className="bg-dark-card rounded-2xl border border-dark-border shadow-xl p-6 sm:p-7">
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {/* Main Search Input */}
        <div>
          <label
            htmlFor="search-input"
            className="block text-sm font-semibold text-dark-primary mb-2"
          >
            Research Topic or Question
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-dark-muted">
              <Search className="w-5 h-5" />
            </div>
            <input
              id="search-input"
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (validationError && e.target.value.trim().length >= 3) {
                  setValidationError("");
                }
              }}
              disabled={loading}
              placeholder="e.g. attention mechanism in vision transformers, multi-agent reinforcement learning"
              className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-dark-border bg-dark-inset text-dark-primary text-base
                         placeholder:text-dark-muted focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20
                         disabled:opacity-50 shadow-inner transition-colors"
            />
          </div>
          {validationError && (
            <p className="mt-1.5 text-xs text-rose-400 font-medium">
              {validationError}
            </p>
          )}
        </div>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-0.5">
          <span className="text-xs font-medium text-dark-muted flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Suggestions:
          </span>
          {SUGGESTIONS.map((topic) => (
            <button
              key={topic}
              type="button"
              disabled={loading}
              onClick={() => handleSuggestionClick(topic)}
              className="text-xs font-medium px-2.5 py-1 rounded-full bg-dark-subtle text-dark-secondary
                         hover:bg-indigo-950/70 hover:text-indigo-300 hover:border-indigo-800/60 border border-dark-border transition-colors disabled:opacity-50"
            >
              {topic}
            </button>
          ))}
        </div>

        {/* Options & Controls */}
        <div className="pt-3 border-t border-dark-border-subtle flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Max results slider */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs font-medium text-dark-secondary">
              <SlidersHorizontal className="w-3.5 h-3.5 text-dark-muted" />
              <span>Max Papers:</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={maxResults}
              onChange={(e) => setMaxResults(parseInt(e.target.value, 10))}
              disabled={loading}
              className="w-24 sm:w-32 h-1.5 bg-dark-inset rounded-lg appearance-none cursor-pointer accent-indigo-500 disabled:opacity-50 border border-dark-border-subtle"
              aria-label="Max results"
            />
            <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-dark-subtle text-dark-primary border border-dark-border min-w-[24px] text-center">
              {maxResults}
            </span>
          </div>

          {/* PDF Checkbox */}
          <label className="flex items-center gap-2.5 text-xs font-medium text-dark-secondary hover:text-dark-primary cursor-pointer select-none">
            <input
              type="checkbox"
              checked={generatePdf}
              onChange={(e) => setGeneratePdf(e.target.checked)}
              disabled={loading}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 border-dark-border bg-dark-inset accent-indigo-500"
            />
            <span className="flex items-center gap-1">
              <FileText className="w-3.5 h-3.5 text-dark-muted" />
              Generate Downloadable PDF Report
            </span>
          </label>
        </div>

        {/* Primary CTA */}
        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl font-semibold text-white
                     bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:bg-indigo-950/80 disabled:text-indigo-400/60
                     disabled:cursor-not-allowed shadow-md shadow-indigo-950/50 transition-colors text-base"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Synthesizing Literature from arXiv…</span>
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              <span>Search & Summarize Papers</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
