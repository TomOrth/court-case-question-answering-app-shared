import { useState, useEffect } from 'react';
import type { Citation } from '../../types';
import { api } from '../../services/api';

interface SourceViewerProps {
  citationId: string | null;
  onClose: () => void;
}

// SourceViewer - Sidebar that displays full citation source details
export default function SourceViewer({ citationId, onClose }: SourceViewerProps) {
    const [citation, setCitation] = useState<Citation | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

  // Helper to ensure URLs have https:// protocol
  const ensureHttps = (url: string | null | undefined): string | null => {
    if (!url) return null;
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    return `https://${url}`;
  };

  // Fetch citation data when citationId changes
  useEffect(() => {
    if (!citationId) {
      setCitation(null);
      setError(null);
      return;
    }

    const fetchCitation = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await api.citations.getCitation(citationId);
        setCitation(data);
      } catch (err) {
        console.error('Failed to fetch citation:', err);
        setError(err instanceof Error ? err.message : 'Failed to load citation');
      } finally {
        setLoading(false);
      }
    };

    fetchCitation();
  }, [citationId]);

    // Don't render if no citation is selected
  if (!citationId) {
    return null;
  }

  
  return (
    <>
      {/* Backdrop overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar panel */}
      <div className="fixed top-0 right-0 h-full w-full md:w-2/3 lg:w-1/2 bg-white shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900">
            Source Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
            aria-label="Close source viewer"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div>
                  <h3 className="text-sm font-medium text-red-800">Error loading citation</h3>
                  <p className="mt-1 text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {citation && !loading && !error && (
            <div className="space-y-6">
              {/* Citation Type Badge */}
              <div>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  citation.citation_type === 'chunk' 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-purple-100 text-purple-800'
                }`}>
                  {citation.citation_type === 'chunk' ? 'Document Chunk' : 'Docket Entry'}
                </span>
              </div>

              {/* Citation ID */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Citation ID
                </h3>
                <p className="text-sm text-gray-700 font-mono bg-gray-50 px-3 py-2 rounded border border-gray-200">
                  {citationId}
                </p>
              </div>

              {/* Content Display */}
              {citation.citation_type === 'chunk' && (
                <>
                  {/* Document Title */}
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                      Document
                    </h3>
                    <p className="text-sm text-gray-900 font-medium">
                      {citation.document.title || 'Untitled Document'}
                    </p>
                  </div>

                  {/* Chunk Text */}
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Content
                    </h3>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                        {citation.chunk.chunk_text}
                      </p>
                    </div>
                  </div>

                  {/* Chunk Position */}
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                      Position
                    </h3>
                    <p className="text-sm text-gray-700">
                      Chunk {citation.chunk.chunk_index + 1} of {citation.document.total_chunks}
                    </p>
                  </div>

                  {/* Document Type */}
                  {citation.document.document_type && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                        Document Type
                      </h3>
                      <p className="text-sm text-gray-700">
                        {citation.document.document_type}
                      </p>
                    </div>
                  )}

                  {/* Document Date */}
                  {citation.document.doc_date && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                        Document Date
                      </h3>
                      <p className="text-sm text-gray-700">
                        {new Date(citation.document.doc_date).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                    </div>
                  )}

                  {/* External Links */}
                  {(citation.document.file_url || citation.document.clearinghouse_link) && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        External Links
                      </h3>
                      <div className="flex flex-col gap-2">
                        {citation.document.file_url && (
                          <a 
                            href={ensureHttps(citation.document.file_url) || '#'} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                          >
                            <span>📄</span>
                            <span>Download PDF</span>
                          </a>
                        )}
                        {citation.document.clearinghouse_link && (
                          <a 
                            href={ensureHttps(citation.document.clearinghouse_link) || '#'} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                          >
                            <span>🌐</span>
                            <span>View on Clearinghouse</span>
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}

              {citation.citation_type === 'docket_entry' && (
                <>
                  {/* Description */}
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Description
                    </h3>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                        {citation.docket_entry.description}
                      </p>
                    </div>
                  </div>

                  {/* Entry Number */}
                  {citation.docket_entry.entry_number && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                        Entry Number
                      </h3>
                      <p className="text-sm text-gray-700">
                        #{citation.docket_entry.entry_number}
                      </p>
                    </div>
                  )}

                  {/* Date Filed */}
                  {citation.docket_entry.date_filed && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                        Date Filed
                      </h3>
                      <p className="text-sm text-gray-700">
                        {new Date(citation.docket_entry.date_filed).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                    </div>
                  )}

                  {/* External Links */}
                  {(citation.docket_entry.url || citation.docket_entry.recap_pdf_url) && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        External Links
                      </h3>
                      <div className="flex flex-col gap-2">
                        {citation.docket_entry.url && (
                          <a 
                            href={ensureHttps(citation.docket_entry.url) || '#'} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                          >
                            <span>⚖️</span>
                            <span>View on CourtListener</span>
                          </a>
                        )}
                        {citation.docket_entry.recap_pdf_url && (
                          <a 
                            href={ensureHttps(citation.docket_entry.recap_pdf_url) || '#'} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                          >
                            <span>📄</span>
                            <span>Download PDF</span>
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}