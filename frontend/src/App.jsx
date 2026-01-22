import React, { useState } from "react";
import axios from "axios";

import SearchBar from "./components/SearchBar";
import PaperList from "./components/PaperList";
import HistorySidebar from "./components/HistorySidebar";

export default function App() {
  const [papers, setPapers] = useState([]);
  const [pdfFilename, setPdfFilename] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);

  const handleSearch = async ({ query, maxResults, generatePdf }) => {
    setLoading(true);
    setError("");

    try {
      const res = await axios.post("http://127.0.0.1:8000/search", {
        query,
        max_results: maxResults,
        generate_pdf: generatePdf,
      });

      const paperList = res.data.papers.map((p, idx) => ({
        id: idx + 1,
        title: p.title,
        authors: p.authors.join(", "),
        published: p.published,
        url: p.url,
        summary: p.summary,
      }));

      setPapers(paperList);
      setPdfFilename(res.data.pdf_filename);

      setHistory((prev) => [
        {
          query,
          papers: paperList,
          pdfFilename: res.data.pdf_filename,
          timestamp: new Date().toLocaleString(),
        },
        ...prev,
      ]);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to fetch papers");
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex">
      {/* Sidebar */}
      <div className="hidden md:block w-72 p-4 border-r border-gray-700 bg-gray-800">
        <h2 className="text-xl font-semibold mb-4 text-blue-400">History</h2>
        <HistorySidebar
          history={history}
          setPapers={setPapers}
          setPdfFilename={setPdfFilename}
        />
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col items-center p-6">
        <h1 className="text-4xl font-bold text-blue-400 mb-10 mt-4">
          arXiv-GPT: Research Assistant
        </h1>

        <div className="w-full max-w-3xl bg-gray-800 p-6 rounded-xl shadow-lg">
          <SearchBar onSearch={handleSearch} loading={loading} />
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
  );
}
