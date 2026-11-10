import React from "react";
import { Clock, FileDown, ArrowUpRight, Search } from "lucide-react";
import { downloadPdfUrl } from "../services/api";

export default function HistorySidebar({
  history,
  setPapers,
  setPdfFilename,
  setQuery,
  loading = false,
  onItemClick,
}) {
  const handleHistoryClick = (entry) => {
    if (!entry) return;

    if (setQuery && entry.query) {
      setQuery(entry.query);
    }

    if (Array.isArray(entry.papers)) {
      setPapers(entry.papers);
      setPdfFilename(entry.pdfFilename || null);
    } else if (typeof entry.result === "string") {
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
          .map((p, idx) => ({
            id: idx + 1,
            title: p.trim().split("\n")[0] || "Untitled Paper",
            summary: { tldr: p.trim() },
          }));
        setPapers(paperList);
        setPdfFilename(entry.pdfFilename || null);
      }
    } else {
      setPapers([]);
      setPdfFilename(null);
    }

    if (onItemClick) {
      onItemClick();
    }
  };

  return (
    <aside className="flex flex-col h-full bg-dark-sidebar border-r border-dark-border-subtle">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-dark-border-subtle flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-bold text-dark-primary tracking-tight">
            Search History
          </h3>
        </div>
        {history && history.length > 0 && (
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-dark-subtle text-dark-secondary border border-dark-border-subtle">
            {history.length}
          </span>
        )}
      </div>

      {/* History Items List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading && (
          <div className="space-y-2.5 p-2">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="h-16 rounded-xl bg-dark-subtle/50 animate-pulse border border-dark-border-subtle"
              />
            ))}
          </div>
        )}

        {!loading && (!history || history.length === 0) && (
          <div className="py-12 px-4 text-center">
            <div className="w-9 h-9 rounded-xl bg-dark-subtle flex items-center justify-center mx-auto mb-3 text-dark-muted">
              <Search className="w-4 h-4" />
            </div>
            <p className="text-xs font-semibold text-dark-secondary mb-1">
              No recent searches
            </p>
            <p className="text-[11px] text-dark-muted leading-relaxed">
              Your research queries will appear here automatically.
            </p>
          </div>
        )}

        {!loading &&
          history &&
          history.map((entry, idx) => (
            <div
              key={entry.id || idx}
              className="group relative rounded-xl border border-dark-border-subtle bg-dark-card hover:bg-dark-card-hover
                         hover:border-dark-border transition-all p-3 cursor-pointer shadow-xs"
              onClick={() => handleHistoryClick(entry)}
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <span className="text-xs font-semibold text-dark-primary line-clamp-2 group-hover:text-indigo-400 transition-colors">
                  {entry.query}
                </span>
                <ArrowUpRight className="w-3.5 h-3.5 text-dark-muted group-hover:text-indigo-400 shrink-0 transition-colors" />
              </div>

              <div className="flex items-center justify-between text-[11px] text-dark-muted pt-1">
                <span>{entry.timestamp || "Recent"}</span>

                {entry.pdfFilename && (
                  <a
                    href={downloadPdfUrl(entry.pdfFilename)}
                    download
                    onClick={(e) => e.stopPropagation()}
                    title="Download generated PDF report"
                    className="p-1 rounded text-dark-muted hover:text-indigo-400 hover:bg-indigo-950/50 transition-colors"
                    aria-label={`Download PDF report for ${entry.query}`}
                  >
                    <FileDown className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            </div>
          ))}
      </div>
    </aside>
  );
}
