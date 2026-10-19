import React from "react";
import { FileText } from "lucide-react"; // lightweight icon

function HistorySidebar({ history, setPapers, setPdfFilename }) {
  const handleHistoryClick = (entry) => {
    if (
      entry.result.includes("No papers found") ||
      entry.result.includes("Unable to process")
    ) {
      setPapers([]);
      setPdfFilename(null);
    } else {
      const paperList = entry.result
        .split("--------------------------------------------------")
        .filter((p) => p.trim())
        .map((p) => ({
          text: p,
          id: Math.random().toString(),
        }));
      setPapers(paperList);
      setPdfFilename(entry.pdfFilename);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-800 border-r border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-gray-200">Search History</h3>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {history.length === 0 && (
          <p className="text-gray-400 text-sm px-2">No search history yet.</p>
        )}

        {history.map((entry, idx) => (
          <div key={idx} className="group">
            <button
              onClick={() => handleHistoryClick(entry)}
              className="w-full flex justify-between items-center px-3 py-2 rounded-lg 
                         text-gray-300 hover:bg-gray-700 hover:text-white transition-colors text-sm"
              aria-label={`View search: ${entry.query}`}
            >
              <span className="truncate">{entry.query}</span>
              {entry.pdfFilename && (
                <a
                  href={`/api/download_pdf/${entry.pdfFilename}`}
                  className="ml-2 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity"
                  download
                  onClick={(e) => e.stopPropagation()}
                >
                  <FileText size={16} />
                </a>
              )}
            </button>
            <p className="text-xs text-gray-500 px-3">{entry.timestamp}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default HistorySidebar;
