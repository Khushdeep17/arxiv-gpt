import React, { useState } from "react";

function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState("self-driving cars");
  const [maxResults, setMaxResults] = useState(3);
  const [generatePdf, setGeneratePdf] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.length < 3) {
      alert("Query must be at least 3 characters.");
      return;
    }
    onSearch({ query, maxResults, generatePdf });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      {/* Search Input */}
      <div>
        <label className="block text-gray-300 mb-2 text-lg font-medium">
          Search Topic
        </label>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full p-4 rounded-lg bg-gray-700 text-gray-100 border border-gray-600 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
          placeholder="Enter topic (e.g., self-driving cars)"
          disabled={loading}
        />
      </div>

      {/* Controls Row */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        {/* Max Results */}
        <div className="flex-1">
          <label className="block text-gray-300 mb-2">Max Results (1-10)</label>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min="1"
              max="10"
              value={maxResults}
              onChange={(e) => setMaxResults(parseInt(e.target.value))}
              className="w-full accent-blue-500"
              disabled={loading}
            />
            <span className="text-gray-300 font-semibold">{maxResults}</span>
          </div>
        </div>

        {/* PDF Checkbox */}
        <div className="flex items-center">
          <label className="flex items-center text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={generatePdf}
              onChange={(e) => setGeneratePdf(e.target.checked)}
              className="mr-2 accent-blue-500"
              disabled={loading}
            />
            Generate PDF
          </label>
        </div>
      </div>

      {/* Search Button */}
      <button
        type="submit"
        disabled={loading}
        className={`w-full py-3 rounded-lg font-semibold text-lg 
                    ${loading ? "bg-gray-600 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"} 
                    text-white transition-colors shadow-md`}
      >
        {loading ? (
          <span className="flex items-center justify-center">
            <svg
              className="animate-spin h-5 w-5 mr-2 text-white"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v8H4z"
              />
            </svg>
            Searching...
          </span>
        ) : (
          "Search"
        )}
      </button>
    </form>
  );
}

export default SearchBar;
