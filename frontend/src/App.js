import React, { useState } from "react";
import axios from "axios";

function App() {
  const [query, setQuery] = useState("self-driving cars");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pdfFilename, setPdfFilename] = useState(null);
  const [error, setError] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await axios.post("/api/search", {
        query,
        max_results: 3,
        generate_pdf: true,
      });
      setResults(
        res.data.result
          .split("--------------------------------------------------")
          .filter((x) => x.trim())
      );
      setPdfFilename(res.data.pdf_filename);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to fetch papers");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen p-6 bg-gray-900 text-gray-100">
      <h1 className="text-3xl font-bold text-blue-400 mb-4">
        arXiv-GPT: Research Assistant
      </h1>
      <form onSubmit={handleSearch} className="mb-6">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full p-3 rounded bg-gray-800 border border-gray-600"
        />
        <button
          type="submit"
          disabled={loading}
          className="mt-4 w-full py-3 rounded font-semibold bg-blue-500 hover:bg-blue-700"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <div className="text-red-400">{error}</div>}

      <div className="space-y-4">
        {results.map((r, i) => (
          <div
            key={i}
            className="bg-gray-800 p-4 rounded shadow"
            dangerouslySetInnerHTML={{
              __html: r.replace(/\n/g, "<br>").replace(/- /g, "<br>&bull; "),
            }}
          />
        ))}
      </div>

      {pdfFilename && (
        <a
          href={`/api/download_pdf/${pdfFilename}`}
          className="inline-block mt-6 py-2 px-4 bg-blue-500 rounded"
          download
        >
          Download PDF
        </a>
      )}
    </div>
  );
}

export default App;
