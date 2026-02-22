import { useMemo } from 'react';

interface CitationRendererProps {
    content: string;
    onCitationClick: (citationId: string) => void;
}

interface ParsedSegment {
    type: 'text' | 'citation';
    content: string;
    citationId?: string;
    citationNumber?: number;
}

// CitationRenderer: parses content & renders citations as clickable badges
export default function CitationRenderer({ content, onCitationClick }: CitationRendererProps) {
    // Parse content into text and citation segments
    const segments = useMemo(() => {
        const parsed: ParsedSegment[] = [];
        const citationMap = new Map<string, number>(); // Track citation ID -> number mapping

        // Regex to match [CITE:doc_XXXXX_chunk_XXXXX] or [CITE:case_XXXXX_docket_entry_XXXXX]
        const citationRegex = /\[CITE:((?:doc_\d+_chunk_\d+)|(?:case_\d+_docket_entry_\d+))\]/g;

        let lastIndex = 0;
        let citationCounter = 1;
        let match;

        while ((match = citationRegex.exec(content)) != null) {
            // Add text before citation
            if (match.index > lastIndex) {
                parsed.push({
                    type: 'text',
                    content: content.substring(lastIndex, match.index)
                });
            }

            const citationId = match[1];
            
            // Check if we've seen this citation before
            let citationNumber: number;
            if (citationMap.has(citationId)) {
                citationNumber = citationMap.get(citationId)!;
            } else {
                citationNumber = citationCounter++;
                citationMap.set(citationId, citationNumber);
            }

            // Add citation
            parsed.push({
                type: 'citation',
                content: match[0],
                citationId: citationId,
                citationNumber: citationNumber
            });

            lastIndex = match.index + match[0].length;
        }

        // Add remaining text
        if (lastIndex < content.length) {
            parsed.push({
                type: 'text',
                content: content.substring(lastIndex)
            });
        }

        return parsed;
    }, [content]);

    return (
        <div className="whitespace-pre-wrap">
            {segments.map((segment, index) => {
                if (segment.type === 'text') {
                    return <span key={index}>{segment.content}</span>
                } else {
                    // Citation badget
                    return (
                        <button
                            key={index}
                            onClick={() => onCitationClick(segment.citationId!)}
                            className="inline-flex items-center justify-center w-6 h-5 mx-0.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded border border-blue-400 transition-colors cursor-pointer align-super"
                            title={`View source: ${segment.citationId}`}
                            aria-label={`Citation ${segment.citationNumber}: ${segment.citationId}`}
                        >
                            {segment.citationNumber}
                        </button>
                    );
                }
            })}
        </div>
    );
}