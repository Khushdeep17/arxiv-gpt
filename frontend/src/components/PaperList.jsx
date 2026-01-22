import React from "react";

function PaperList({ papers, pdfFilename }) {
  if (!papers.length) {
    return (
      <p className="text-gray-300">
        No papers to display. Try a new search.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-blue-400 mb-4">
        Latest Papers
      </h2>

      {papers.map((p) => (
        <div
          key={p.id}
          className="bg-gray-800 p-6 rounded-xl shadow-md border border-gray-700"
        >
          <h3 className="text-xl font-semibold text-blue-400 mb-2">
            {p.id}. {p.title}
          </h3>

          <p className="text-sm text-gray-400 mb-1">
            <span className="font-medium">Authors:</span> {p.authors}
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
            View PDF
          </a>

          <div className="mt-4">
            <p className="text-gray-200 leading-relaxed">
              {p.summary}
            </p>
          </div>
        </div>
      ))}

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
