import React, { useState } from "react";

function PaperList({ papers, pdfFilename }) {
  const [expanded, setExpanded] = useState({});

  if (!papers?.length) {
    return (
      <p className="text-gray-300">
        No papers to display. Try a new search.
      </p>
    );
  }

  const toggle = (i) => {
    setExpanded(prev => ({
      ...prev,
      [i]: !prev[i]
    }));
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-blue-400 mb-4">
        Latest Papers
      </h2>

      {papers.map((p, i) => {

        // ✅ SAFELY HANDLE AUTHORS
        const authors = Array.isArray(p.authors)
          ? p.authors.join(", ")
          : p.authors || "Unknown authors";

        const s = p.summary || {};

        return (
          <div
            key={i}
            className="bg-gray-800 p-6 rounded-xl shadow-md border border-gray-700"
          >
            <h3 className="text-xl font-semibold text-blue-400 mb-2">
              {i + 1}. {p.title}
            </h3>

            <p className="text-sm text-gray-400 mb-1">
              <span className="font-medium">Authors:</span> {authors}
            </p>

            <p className="text-sm text-gray-400 mb-3">
              <span className="font-medium">Published:</span> {p.published}
            </p>

            <a
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 underline text-sm"
            >
              View Paper
            </a>

            {/* TLDR */}
            <div className="mt-4">
              <p className="text-gray-200">
                <span className="text-blue-300 font-semibold">
                  TL;DR:
                </span>{" "}
                {s.tldr || "No summary available"}
              </p>
            </div>

            {/* EXPAND BUTTON */}
            <button
              onClick={() => toggle(i)}
              className="text-blue-400 mt-2 hover:underline"
            >
              {expanded[i] ? "Hide details" : "Show details"}
            </button>

            {/* DETAILS */}
            {expanded[i] && (
              <div className="mt-3 space-y-2 text-gray-300">

                {s.key_contributions?.length > 0 && (
                  <>
                    <p className="text-blue-300 font-semibold">
                      Key Contributions:
                    </p>
                    <ul className="list-disc ml-6">
                      {s.key_contributions.map((c, idx) => (
                        <li key={idx}>{c}</li>
                      ))}
                    </ul>
                  </>
                )}

                {s.methods?.length > 0 && (
                  <>
                    <p className="text-blue-300 font-semibold">
                      Methods:
                    </p>
                    <ul className="list-disc ml-6">
                      {s.methods.map((m, idx) => (
                        <li key={idx}>{m}</li>
                      ))}
                    </ul>
                  </>
                )}

                {s.results?.length > 0 && (
                  <>
                    <p className="text-blue-300 font-semibold">
                      Results:
                    </p>
                    <ul className="list-disc ml-6">
                      {s.results.map((r, idx) => (
                        <li key={idx}>{r}</li>
                      ))}
                    </ul>
                  </>
                )}

                {s.why_it_matters && (
                  <p>
                    <span className="text-blue-300 font-semibold">
                      Why it matters:
                    </span>{" "}
                    {s.why_it_matters}
                  </p>
                )}

                {s.citation && (
                  <p className="italic text-gray-400">
                    {s.citation}
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}

      {pdfFilename && (
        <div className="mt-6 text-center">
          <a
            href={`http://127.0.0.1:8000/download_pdf?filename=${pdfFilename}`}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg shadow"
          >
            Download PDF Report
          </a>
        </div>
      )}
    </div>
  );
}

export default PaperList;
