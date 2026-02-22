import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import type { ChatSession } from '../types'

import MessageBubble from '../components/chat/MessageBubble';
import ChatInput from '../components/chat/ChatInput';
import { useRef } from 'react';
import type { ChatMessage } from '../types';
import SourceViewer from '../components/chat/SourceViewer';
import { useAppLayout } from '../components/layout/AppLayout';
import { useAuth } from '../contexts/AuthContext';

export default function ChatPage() {
    // states
    const { sessionId } = useParams<{ sessionId: string }>()
    const navigate = useNavigate()
    const { setSession: setAppLayoutSession } = useAppLayout();
    const { user } = useAuth();

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [streamingMsg, setStreamingMsg] = useState<ChatMessage | null>(null);

    const [session, setSession] = useState<ChatSession | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    const [selectedCitationId, setSelectedCitationId] = useState<string | null>(null);

    const streamingMsgRef = useRef<ChatMessage | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Check if current user is the owner
    const isOwner = user && session && user.id === session.user_id;
    const canSendMessages = isOwner;

    // useEffect
    useEffect(() => {
        if (!sessionId) return

        const fetchSession = async () => {
            try {
                const data = await api.chat.getSession(sessionId)
                setSession(data)
                setAppLayoutSession(data); // Pass to AppLayout for TopBar
                if (data.messages) {
                    setMessages(data.messages);
                }                
            } catch(err) {
                console.error(err)
                setError('Failed to load chat session')
            } finally {
                setLoading(false)
            }
        }
        fetchSession()
    }, [sessionId, setAppLayoutSession])

    // Clear session from TopBar when leaving chat page
    useEffect(() => {
        return () => {
            setAppLayoutSession(null);
        };
    }, [setAppLayoutSession]);

    // Scroll to bottom on initial load
    useEffect(() => {
        if (!loading) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
        }
    }, [loading]);

    // Scroll to bottom when user sends a message
    useEffect(() => {
        const lastMsg = messages[messages.length - 1];
        if (lastMsg?.role === 'user') {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    const handleSendMessage = async (content: string) => {
        if (!sessionId) return;

        // 1. Add User Message immediately
        const userMsg: ChatMessage = {
            message_id: crypto.randomUUID(),
            session_id: sessionId,
            role: 'user',
            content: content,
            created_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMsg]);

        // 2. Prepare Assistant Message Placeholder
        const assistantMsgId = crypto.randomUUID();
        const assistantMsg: ChatMessage = {
            message_id: assistantMsgId,
            session_id: sessionId,
            role: 'assistant',
            content: 'Thinking (please wait)...',
            created_at: new Date().toISOString(),
            reasoning_steps: []
        }
        setStreamingMsg(assistantMsg);
        streamingMsgRef.current = assistantMsg;

        try {
            await api.chat.sendMessageStream(sessionId, content, (event) => {
                setStreamingMsg(current => {

                    if (!current) return assistantMsg;

                    // Create a shallow copy of the current message
                    const next = { ...current };

                    // =============================================
                    // Handle: gathered_context
                    // =============================================
                    if (event.type === 'gathered_context') {
                        next.reasoning_steps = [...(next.reasoning_steps || []), {
                            step_id: event.data.id,
                            message_id: assistantMsgId,
                            step_type: 'gathered_context',
                            step_data: event.data,
                            step_order: event.data.step_number,
                            created_at: new Date().toISOString()
                        }];
                    }
                    
                    // =============================================
                    // Handle: reasoning
                    // =============================================
                    else if (event.type === 'reasoning') {
                        next.reasoning_steps = [...(next.reasoning_steps || []), {
                            step_id: event.data.id,
                            message_id: assistantMsgId,
                            step_type: 'reasoning',
                            step_data: event.data,
                            step_order: event.data.step_number,
                            created_at: new Date().toISOString()
                        }];
                    }
                    
                    // =============================================
                    // Handle: tool_call
                    // =============================================
                    else if (event.type === 'tool_call') {
                        // Use the ID provided by backend (not crypto.randomUUID)
                        // This ID is what links the call to its result
                        next.reasoning_steps = [...(next.reasoning_steps || []), {
                            step_id: event.data.id,  // backend-provided UUID
                            message_id: assistantMsgId,
                            step_type: 'tool_call',
                            step_data: {
                                ...event.data,
                                status: 'pending'
                            },
                            step_order: event.data.step_number,
                            created_at: new Date().toISOString(),
                        }];
                    }
                    
                    // =============================================
                    // Handle: tool_result
                    // =============================================
                    else if (event.type === 'tool_result') {
                        // Make a copy of the reasoning_steps array
                        const steps = [...(next.reasoning_steps || [])];
                        
                        // Find the matching tool call by ID
                        const toolCallIndex = steps.findIndex(
                            step => step.step_type === 'tool_call' && step.step_id === event.data.id
                        );
                        
                        if (toolCallIndex !== -1) {
                            // Update the tool call's status to "completed"
                            steps[toolCallIndex] = {
                                ...steps[toolCallIndex],
                                step_data: {
                                    ...steps[toolCallIndex].step_data,
                                    status: 'completed'
                                }
                            };
                            
                            steps.splice(toolCallIndex + 1, 0, {
                                step_id: `${event.data.id}_result`,
                                message_id: assistantMsgId,
                                step_type: 'tool_result',
                                step_data: {
                                    ...event.data,
                                    parent_id: event.data.id
                                },
                                step_order: event.data.step_number,
                                created_at: new Date().toISOString()
                            });
                        }
                        
                        next.reasoning_steps = steps;
                    }
                    
                    // =============================================
                    // Handle: tool_result
                    // =============================================
                    else if (event.type === 'content') {
                        // Append to the message content (streaming text)
                        if (next.content === 'Thinking (please wait)...') {
                            next.content = "";
                        }
                        next.content += event.data
                    }
                    
                    streamingMsgRef.current = next;
                    return next;
                });
            });
        } catch(err) {
            // handle error
            console.error(err);
        } finally {
            // move streaming message to permanent list
            const finalMsg = streamingMsgRef.current;
            if (finalMsg) {
                setMessages(prev => [...prev, finalMsg]);
            }
            setStreamingMsg(null);
            streamingMsgRef.current = null;
        }
    }

    const handleCitationClick = (citationId: string) => {
        setSelectedCitationId(citationId);
    }

    const handleCloseSourceViewer = () => {
        setSelectedCitationId(null);
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                Loading chat...
            </div>
        )
    }

    if (error || !session) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center flex-col gap-4">
                <div className="text-red-400">
                    {error || 'Session not found'}
                </div>
                <button
                    onClick={() => navigate('/')}
                    className="text-blue-400 hover:underline"
                >
                    Return Home
                </button>
            </div>
        )
    }

    return (
        <div className="flex flex-col h-full overflow-hidden">
            {/* Read-only banner for viewers */}
            {!canSendMessages && (
                <div className="bg-yellow-900/50 border-b border-yellow-700 px-6 py-3 flex-shrink-0">
                    <div className="max-w-4xl mx-auto flex items-center gap-2">
                        <span className="text-yellow-200">📖 Viewing shared chat</span>
                        {!user && (
                            <button
                                onClick={() => navigate('/login')}
                                className="ml-auto text-sm bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded"
                            >
                                Log in to chat
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* Messages area - scrollable */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto">
                    {/* Render completed messages (not streaming)  */}
                    {messages.map(msg => (
                        <MessageBubble 
                            key={msg.message_id}
                            message={msg}
                            isStreaming={false}  // this message is not streaming
                            onCitationClick={handleCitationClick}
                        />
                    ))}

                    {/* Render the currently streaming message (if any)   */}
                    {streamingMsg && (
                        <MessageBubble 
                            key={streamingMsg.message_id}
                            message={streamingMsg}
                            isStreaming={true}  // this message is streaming
                            onCitationClick={handleCitationClick}
                        />
                    )}
                    
                    {/* Element to scroll to */}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input area - only show if user can send messages */}
            {canSendMessages && (
                <ChatInput onSend={handleSendMessage} disabled={!!streamingMsg} />
            )}

            <SourceViewer 
                citationId={selectedCitationId}
                onClose={handleCloseSourceViewer}
            />
        </div>
    )
}