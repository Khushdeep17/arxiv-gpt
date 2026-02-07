import React from "react";
import PaperCard from "./PaperCard";
import { downloadPdfUrl } from "../services/api";

export default function PaperList({ papers, pdfFilename }) {

  if (!papers?.length) {
    return (
      <p className="text-gray-300">
        No papers to display. Try a new search.
      </p>
    );
  }

  return (
    <div className="space-y-6">

      <h2 className="text-2xl font-semibold text-blue-400">
        Latest Papers
      </h2>

      {papers.map((paper, i) => (
        <PaperCard
          key={i}
          paper={paper}
          index={i + 1}
        />
      ))}

      {pdfFilename && (
        <div className="mt-6 text-center">
          <a
            href={downloadPdfUrl(pdfFilename)}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg shadow"
          >
            Download PDF Report
          </a>
        </div>
      )}

    </div>
  );
}
