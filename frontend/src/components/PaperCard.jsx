import React, { useState } from "react";

export default function PaperCard({ paper, index }) {

  const [expanded, setExpanded] = useState(false);

  const s = paper.summary || {};

  const authors = Array.isArray(paper.authors)
    ? paper.authors.join(", ")
    : paper.authors || "Unknown";

  return (
    <div className="bg-gray-800 p-6 rounded-xl shadow-md border border-gray-700">

      <h3 className="text-xl font-semibold text-blue-400 mb-2">
        {index}. {paper.title}
      </h3>

      <p className="text-sm text-gray-400">
        <span className="font-medium">Authors:</span> {authors}
      </p>

      <p className="text-sm text-gray-400 mb-2">
        <span className="font-medium">Published:</span> {paper.published}
        {" • "}
        {paper.category}
      </p>

      <a
        href={paper.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-400 underline text-sm"
      >
        View Paper
      </a>

      {/* TLDR */}
      <p className="mt-4 text-gray-200">
        <span className="text-blue-300 font-semibold">
          TL;DR:
        </span>{" "}
        {s.tldr || "No summary"}
      </p>

      {/* Toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-blue-400 mt-2 hover:underline"
      >
        {expanded ? "Hide details" : "Show details"}
      </button>

      {/* Details */}
      {expanded && (
        <div className="mt-3 space-y-2 text-gray-300">

          {renderList("Key Contributions", s.key_contributions)}
          {renderList("Methods", s.methods)}
          {renderList("Results", s.results)}

          {s.why_it_matters && (
            <p>
              <b>Why it matters:</b> {s.why_it_matters}
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
}

function renderList(title, items) {

  if (!items?.length) return null;

  return (
    <>
      <p className="text-blue-300 font-semibold">
        {title}:
      </p>
      <ul className="list-disc ml-6">
        {items.map((i, idx) => (
          <li key={idx}>{i}</li>
        ))}
      </ul>
    </>
  );
}
