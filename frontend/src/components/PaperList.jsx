import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';

function PaperList({ papers, pdfFilename }) {
  const [expanded, setExpanded] = useState({});

  const toggleExpand = (id) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-blue-400 mb-4">Latest Papers</h2>
      {papers.length === 0 && <p className="text-gray-300">No papers to display. Try a new search.</p>}
      {papers.map((paper) => {
        const summaryIndex = paper.text.indexOf("Summary:");
        const preview = summaryIndex !== -1 ? paper.text.slice(0, summaryIndex) : paper.text;

        return (
          <div key={paper.id} className="bg-gray-700 p-6 rounded-lg shadow-lg mb-4">
            <div className="paper-content prose prose-invert max-w-none">
              <ReactMarkdown>
                {expanded[paper.id] ? paper.text : preview}
              </ReactMarkdown>
            </div>
            <button
              onClick={() => toggleExpand(paper.id)}
              className="text-blue-400 hover:underline mt-2 flex items-center"
              aria-label={expanded[paper.id] ? 'Collapse summary' : 'Expand summary'}
            >
              {expanded[paper.id] ? 'Collapse' : 'Expand Summary'}
              {expanded[paper.id] ? (
                <ChevronUpIcon className="w-5 h-5 ml-2" />
              ) : (
                <ChevronDownIcon className="w-5 h-5 ml-2" />
              )}
            </button>
          </div>
        );
      })}
      {pdfFilename && (
        <a
          href={`/api/download_pdf/${pdfFilename}`}
          className="inline-block mt-4 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold transition-colors"
          download
        >
          Download PDF
        </a>
      )}
    </div>
  );
}

export default PaperList;
