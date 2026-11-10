import React, { useState } from "react";
import {
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Calendar,
  Users,
  Tag,
  Sparkles,
  Quote,
  Check,
  Copy,
} from "lucide-react";

export default function PaperCard({ paper, index }) {
  const [expanded, setExpanded] = useState(false);
  const [copiedCitation, setCopiedCitation] = useState(false);

  const s = paper.summary || {};

  const authors = Array.isArray(paper.authors)
    ? paper.authors.join(", ")
    : paper.authors || "Unknown authors";

  const handleCopyCitation = () => {
    if (!s.citation) return;
    navigator.clipboard.writeText(s.citation);
    setCopiedCitation(true);
    setTimeout(() => setCopiedCitation(false), 2000);
  };

  return (
    <article className="bg-dark-card rounded-2xl border border-dark-border shadow-md hover:border-slate-700/80 hover:bg-dark-card-hover transition-all p-6 sm:p-7">
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3 flex-1">
          <span className="w-7 h-7 rounded-lg bg-indigo-950/70 text-indigo-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 border border-indigo-800/50">
            {index}
          </span>
          <h3 className="text-lg sm:text-xl font-bold text-dark-primary leading-snug">
            {paper.title}
          </h3>
        </div>

        {/* View on arXiv Link */}
        {paper.url && (
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300
                       bg-indigo-950/50 hover:bg-indigo-900/50 px-3 py-1.5 rounded-lg border border-indigo-800/40
                       shrink-0 self-start transition-colors"
          >
            <span>View arXiv PDF</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      {/* Metadata Row */}
      <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs text-dark-muted mb-4 ml-0 sm:ml-10">
        <div className="flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5 text-dark-muted" />
          <span className="line-clamp-1 text-dark-secondary">{authors}</span>
        </div>

        {paper.published && (
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-dark-muted" />
            <span>{paper.published}</span>
          </div>
        )}

        {paper.category && (
          <div className="flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-dark-muted" />
            <span className="px-2 py-0.5 rounded-md bg-dark-subtle text-dark-secondary font-medium border border-dark-border-subtle">
              {paper.category}
            </span>
          </div>
        )}
      </div>

      {/* TL;DR Highlight Callout */}
      <div className="bg-dark-inset border-l-4 border-indigo-500 p-4 rounded-r-xl my-4 ml-0 sm:ml-10 shadow-inner">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Executive Summary (TL;DR)</span>
        </div>
        <p className="text-sm text-dark-secondary leading-relaxed font-normal">
          {s.tldr || "No structured summary available for this paper."}
        </p>
      </div>

      {/* Toggle Details Action */}
      <div className="ml-0 sm:ml-10 pt-2 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300
                     hover:underline py-1 focus:outline-none transition-colors"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              <span>Hide Detailed Synthesis</span>
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              <span>Explore Key Contributions, Methods & Results</span>
            </>
          )}
        </button>

        {s.citation && (
          <button
            type="button"
            onClick={handleCopyCitation}
            className="text-xs text-dark-muted hover:text-dark-primary inline-flex items-center gap-1 px-2.5 py-1 rounded-md hover:bg-dark-subtle transition-colors"
            title="Copy academic citation"
          >
            {copiedCitation ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-medium">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-dark-muted" />
                <span>Citation</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Expanded Details Sections */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-dark-border-subtle space-y-4 ml-0 sm:ml-10 text-sm text-dark-secondary animate-fadeIn">
          {renderInsightSection("Key Contributions", s.key_contributions)}
          {renderInsightSection("Methods & Approach", s.methods)}
          {renderInsightSection("Primary Results", s.results)}

          {s.why_it_matters && (
            <div className="p-3.5 rounded-xl bg-amber-950/25 border border-amber-800/40">
              <span className="block text-xs font-bold uppercase tracking-wider text-amber-400 mb-1">
                Why It Matters
              </span>
              <p className="text-xs sm:text-sm text-amber-200/90 leading-relaxed">
                {s.why_it_matters}
              </p>
            </div>
          )}

          {s.citation && (
            <div className="flex items-start gap-2.5 p-3 rounded-xl bg-dark-inset border border-dark-border text-xs text-dark-muted font-mono">
              <Quote className="w-4 h-4 text-dark-muted shrink-0 mt-0.5" />
              <span className="italic select-all">{s.citation}</span>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

function renderInsightSection(title, items) {
  if (!items || !items.length) return null;

  return (
    <div>
      <h4 className="text-xs font-bold uppercase tracking-wider text-dark-muted mb-2">
        {title}
      </h4>
      <ul className="space-y-1.5 pl-4 list-disc text-dark-secondary text-xs sm:text-sm marker:text-indigo-500">
        {items.map((item, idx) => (
          <li key={idx} className="leading-relaxed">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
