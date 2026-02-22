import { useState, useMemo } from 'react';
import type { ChatMessage, ReasoningStep } from '../../types';
import CitationRenderer from './CitationRenderer';

interface MessageBubbleProps {
    message: ChatMessage;
    isStreaming?: boolean;  // Track if mmessage is still being built
    onCitationClick: (citationId: string) => void;
}

export default function MessageBubble({ message, isStreaming = false, onCitationClick }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    // State for main accordion (show/hide all reasoning)
    const [showReasoning, setShowReasoning] = useState(false);

    // State for individual step accordions (which ones are expanded)
    const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

    // Group reasoning steps by step_number
    // This creates visual sections like "Step 1", "Step 2", etc.
    const groupedSteps = useMemo(() => {
        const groups: Map<number, ReasoningStep[]> = new Map();

        message.reasoning_steps?.forEach(step => {
            const stepNum = step.step_order;
            if (!groups.has(stepNum)) {
                groups.set(stepNum, []);
            }
            groups.get(stepNum)!.push(step);
        });

        // convert Map to sorted array of [stepNumber, steps] pair
        return Array.from(groups.entries()).sort((a, b) => a[0] - b[0]);
    }, [message.reasoning_steps]);

    // // Auto-expand the most recent step during streaming
    // useEffect(() => {
    //     if (isStreaming && showReasoning && message.reasoning_steps && message.reasoning_steps?.length > 0) {
    //         const latestStep = message.reasoning_steps[message.reasoning_steps.length - 1];
            
    //         // Only auto-expand if it's not a tool_result (those are nested)
    //         if (latestStep.step_type !== 'tool_result') {
    //             setExpandedSteps(prev => new Set([...prev, latestStep.step_id]));
    //         }
    //     }
    // }, [message.reasoning_steps?.length, isStreaming, showReasoning]);

    // Toggle function for individual steps
    const toggleStep = (stepId: string) => {
        setExpandedSteps(prev => {
            const next = new Set(prev);
            if (next.has(stepId)) {
                next.delete(stepId);  // Collapse
            } else {
                next.add(stepId);  // Expand
            }
            return next;
        });
    }

    // Rendering
    return (
        <div className={`flex ${isUser ? 'justify-end': 'justify-start'} mb-4`}>
            <div className={`max-w-[80%] rounded-lg p-4 ${
                isUser ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-100'
            }`}>
                {/* Main reasoning accordion (Assistant only) */}
                {!isUser && message.reasoning_steps && message.reasoning_steps.length > 0 && (
                    <div className="mb-3 border-b border-gray-600 pb-2">
                        <button
                            onClick={() => setShowReasoning(!showReasoning)}
                            className="text-xs text-gray-400 hover:text-gray-200 flex items-center gap-2 transition-colors"
                        >
                            <span>{showReasoning ? '▼ Thought Process' : '▶ Thought Process (click to expand)'}</span>

                            {/* Streaming indicator  */}
                            {isStreaming && (
                                <span className="flex itemms-center gap-1 text-blue-400">
                                    <span className="animate-pulse">●</span>
                                    <span>Querying the case</span>
                                </span>
                            )}

                        </button>

                        {/* Reasoning content (when expanded)  */}
                        {showReasoning && (
                            <div className="mt-3 space-y-3">
                                {groupedSteps.map(([stepNum, steps]) => (
                                    <div key={stepNum} className="border-l-2 border-gray-600 pl-3">

                                        {/* Step number label  */}
                                        <div className="text-xs text-gray-500 font-semibold mb-2">
                                            Step {stepNum}
                                        </div>

                                        {/* Individual step accordions */}
                                        {steps.map(step => {
                                            // skip tool_result if it has parent_id (will be nested)
                                            if (step.step_type === 'tool_result' && step.step_data.parent_id) {
                                                return null;
                                            }

                                            return (
                                                <StepAccordion
                                                    key={step.step_id}
                                                    step={step}
                                                    isExpanded={expandedSteps.has(step.step_id)}
                                                    onToggle={() => toggleStep(step.step_id)}
                                                    allSteps={steps}
                                                    onCitationClick={onCitationClick}
                                                />
                                            )

                                        })}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Message content  */}
                <div className="whitespace-pre-wrap">
                    <CitationRenderer 
                        content={message.content}
                        onCitationClick={onCitationClick}
                    />
                </div>
            </div>
        </div>
    );
}

// ================================================
// Separate component for individual step accordion
// ================================================
interface StepAccordionProps {
    step: ReasoningStep;
    isExpanded: boolean;
    onToggle: () => void;
    allSteps: ReasoningStep[];  // All steps in this group (to find nested result)
    onCitationClick: (citationId: string) => void;
}

function StepAccordion({ step, isExpanded, onToggle, allSteps, onCitationClick }: StepAccordionProps) {
    // Get icon based on step type and status
    const getIcon = () => {
        switch (step.step_type) {
            case 'gathered_context':
                return '📋';
            case 'reasoning':
                return '🧠';
            case 'tool_call':
                const status = step.step_data.status;
                // if (status === 'executing') return '🔄';
                if (status === 'pending') return '⏳';
                if (status === 'completed') return '✅';
                // if (status === 'failed') return '❌';
                const hasResult = allSteps.some(s => 
                    s.step_type === 'tool_result' && 
                    s.step_data.parent_id === step.step_id
                );
                return hasResult ? '✅' : '❌';
            default:
                return '📄';
        }
    };

    // Get title for the accordion header
    const getTitle = () => {
        if (step.step_type === 'tool_call') {
            return `Tool: ${step.step_data.tool}`;
        }
        // Convert snake_case to Title Case
        return step.step_type
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    // Get preview text (first 100 chars) when collapsed
    const getPreview = (content: string) => {
        if (!content) return '';
        return content.length > 100 ? content.slice(0, 100) + '...' : content;
    }

    // Extract content from step_data (handle different formats)
    const getContent = () => {
        // For gathered_context and reasoning, content is in step_data.content
        if (step.step_data.content) {
            return step.step_data.content;
        }

        // For tool_call, show parameters as JSON
        if (step.step_type === 'tool_call') {
            const params = { ...step.step_data };
            delete params.id;  // Don't show internal ID
            delete params.step_number;
            return JSON.stringify(params, null, 2);
        }

        // Fallback: stringify entire step_data
        return JSON.stringify(step.step_data, null, 2);

    }
    const content = getContent();

    // Find nested tool result if this is a tool call
    const nestedResult = step.step_type === 'tool_call'
        ? allSteps.find(s => s.step_type === 'tool_result' && s.step_data.parent_id === step.step_id)
        : null;



    // return 
    return (
        <div className="bg-gray-800 rounded-md p-2 mb-2">
            {/* Accordion header (always visible)   */}
            <button
                onClick={onToggle}
                className="w-full text-left text-xs flex items-start gap-2 hover:text-gray-200 transition-colors"
            >
                <span className='text-base'>{getIcon()}</span>
                <div className="flex-1 min-w-0">
                    {/* Title and status  */}
                    <div className="font-semibold text-gray-300 flex items-center gap-2">
                        <span>{getTitle()}</span>
                        {step.step_type === 'tool_call' && step.step_data.status === 'pending' && (
                            <span className="text-blue-400 text-xs font-normal">Executing tool to gather details...</span>
                        )}
                    </div>

                    {/* Preview (only when collapsed)   */}
                    {!isExpanded && (
                        <div className="text-gray-500 mt-1 truncate">
                            {getPreview(content)}
                        </div>
                    )}
                </div>

                {/* Expand / collapse icon  */}
                <span className="text-gray-500 flex-shrink-0">
                   {isExpanded ? '▼' : '▶'}
                </span>
            </button>

            {/* Accordion body (only when expanded)   */}
            {isExpanded && (
                <div className="mt-2 text-xs">
                    {/* Main content  */}
                    <pre className="bg-gray-900 p-2 rounded overflow-x-auto text-gray-300 whitespace-pre-wrap font-mono text-xs">
                        <CitationRenderer 
                            content={content}
                            onCitationClick={onCitationClick}
                        />
                    </pre>

                    {/* Nested tool result (if exists)  */}
                    {nestedResult && (
                        <div className="mt-2 ml-4 border-l-2 border-blue-500 pl-3">
                            <div className="text-blue-400 font-semibold mb-1 flex items-center gap-1">
                                <span>↳</span>
                                <span>Tool Result</span>
                            </div>
                            <pre className="bg-gray-900 p-2 rounded overflow-x-auto text-gray-300 whitespace-pre-wrap font-mono text-xs">
                                <CitationRenderer 
                                    content={nestedResult.step_data.result || JSON.stringify(nestedResult.step_data, null, 2)}
                                    onCitationClick={onCitationClick}
                                />
                            </pre>
                        </div>
                    )}

                </div>
            )}
        </div>
    );
}

// import type { ChatMessage, ReasoningStep } from '../../types';
// import { useState } from 'react';

// interface MessageBubbleProps {
//     message: ChatMessage;
// }

// export default function MessageBubble({ message }: MessageBubbleProps) {

//     const isUser = message.role === 'user';
//     const [showReasoning, setShowReasoning] = useState(false);

//     return (
//         <div className={`flex ${isUser ? 'justify-end': 'justify-start'} mb-4`}>
//             <div className={`max-w-[80%] rounded-lg p-4 ${
//                 isUser ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-100'
//             }`}>
//                 {/* Reasoning Accordion (Assistant Only) */}
//                 {!isUser && message.reasoning_steps && message.reasoning_steps.length > 0 && (
//                     <div className="mb-3 border-b border-gray-700 pb-2">
//                         <button
//                             onClick={() => setShowReasoning(!showReasoning)}
//                             className="text-xs text-gray-400 hovver:text-gray-200 flex items-center gap-1"
//                         >
//                             {showReasoning ? '▼ Hide' : '▶ Show'} Thought Process
//                         </button>
//                         {showReasoning && (
//                             <div className="mt-2 space-y-2 text-xs bg-gray-800 p-2 rounded">
//                                 {message.reasoning_steps.map((step, idx) => (
//                                     <div className="font-mono" key={idx}>
//                                         <span className="text-blue-400">[{step.step_type}]</span>
//                                         <span className="ml-2 text-gray-300">{step.step_data.content || JSON.stringify(step.step_data)}</span>
//                                     </div>
//                                 ))}
//                             </div>

//                         )}
//                     </div>
//                 )}
                
                

//                 {/* Message content  */}
//                 <div className="whitespace-pre-wrap">
//                     {message.content}
//                 </div>
//             </div>
//         </div>
//     )
// }