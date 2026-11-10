import React from "react";
import PaperCard from "./PaperCard";
import { downloadPdfUrl } from "../services/api";
import { FileDown, Sparkles, BookOpen } from "lucide-react";

export default function PaperList({ papers, pdfFilename }) {
  if (!papers || !papers.length) {
    return (
      <div className="bg-dark-card rounded-2xl border border-dark-border p-8 sm:p-12 text-center shadow-lg">
        <div className="w-12 h-12 rounded-2xl bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center mx-auto mb-4 text-indigo-400">
          <BookOpen className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-dark-primary mb-1">
          No research literature to display
        </h3>
        <p className="text-sm text-dark-secondary max-w-md mx-auto mb-6">
          Enter a topic, concept, or research question above to search recent publications on arXiv and generate executive summaries.
        </p>
        <div className="inline-flex items-center gap-2 text-xs font-medium text-dark-muted">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Real-time arXiv discovery powered by structured LLM synthesis</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Results Header & Summary Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-dark-border-subtle">
        <div className="flex items-center gap-2.5">
          <h2 className="text-xl font-bold text-dark-primary tracking-tight">
            Synthesized Papers
          </h2>
          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-indigo-950/60 text-indigo-300 border border-indigo-800/40">
            {papers.length} {papers.length === 1 ? "paper" : "papers"}
          </span>
        </div>

        {pdfFilename && (
          <a
            href={downloadPdfUrl(pdfFilename)}
            download
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white
                       bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 shadow-sm shadow-emerald-950 transition-colors self-start sm:self-auto"
          >
            <FileDown className="w-4 h-4" />
            <span>Download Report (PDF)</span>
          </a>
        )}
      </div>

      {/* Paper Cards */}
      <div className="space-y-5">
        {papers.map((paper, i) => (
          <PaperCard key={paper.id || i} paper={paper} index={i + 1} />
        ))}
      </div>

      {/* Bottom Download Banner if PDF is available */}
      {pdfFilename && (
        <div className="mt-8 p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 to-dark-card border border-indigo-900/40 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-lg">
          <div>
            <h4 className="text-sm font-bold text-dark-primary mb-0.5">
              Complete Research Briefing Ready
            </h4>
            <p className="text-xs text-dark-secondary">
              Download the structured report with full TL;DRs, citations, and key contributions.
            </p>
          </div>
          <a
            href={downloadPdfUrl(pdfFilename)}
            download
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white
                       bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 shadow-md shadow-indigo-950/50 transition-colors shrink-0"
          >
            <FileDown className="w-4 h-4" />
            <span>Download PDF Dossier</span>
          </a>
        </div>
      )}
    </div>
  );
}
