import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../../services/api';
import type { ChatSession } from '../../types';

export default function LeftSidebar() {
    const navigate = useNavigate();
    const { sessionId } = useParams<{ sessionId?: string }>();

    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Editing state
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editingTitle, setEditingTitle] = useState('');

    // Fetch sessions on mount
    useEffect(() => {
        const fetchSessions = async () => {
            try {
                const data = await api.chat.getSessions();
                setSessions(data);
            } catch (err) {
                console.error(err);
                setError('Failed to load sessions');
            } finally {
                setLoading(false);
            }
        };

        fetchSessions();
    }, []);

    const handleDeleteSession = async (sid: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm('Delete this chat session?')) return;

        try {
            await api.chat.deleteSession(sid);
            setSessions(sessions.filter(s => s.session_id !== sid));
            
            // If we deleted the current session, go home
            if (sid === sessionId) {
                navigate('/');
            }
        } catch (err) {
            console.error(err);
            alert('Failed to delete session');
        }
    };

    const startEditing = (session: ChatSession, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingId(session.session_id);
        setEditingTitle(session.session_title);
    };

    const cancelEditing = () => {
        setEditingId(null);
        setEditingTitle('');
    };

    const saveEdit = async (sid: string) => {
        if (!editingTitle.trim()) {
            cancelEditing();
            return;
        }

        // Optimistic update
        const oldSessions = [...sessions];
        setSessions(sessions.map(s => 
            s.session_id === sid 
                ? { ...s, session_title: editingTitle } 
                : s
        ));
        setEditingId(null);

        try {
            await api.chat.renameSession(sid, editingTitle);
        } catch (err) {
            console.error(err);
            // Revert on error
            setSessions(oldSessions);
            alert('Failed to rename session');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent, sid: string) => {
        if (e.key === 'Enter') {
            saveEdit(sid);
        } else if (e.key === 'Escape') {
            cancelEditing();
        }
    };

    return (
        <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-700">
                <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold">Your Chats</h2>
                    {loading && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    )}
                </div>
            </div>

            {/* Sessions list */}
            <div className="flex-1 overflow-y-auto p-4">
                {loading ? (
                    <div className="text-gray-400 text-sm">Loading...</div>
                ) : error ? (
                    <div className="text-red-400 text-sm">{error}</div>
                ) : sessions.length === 0 ? (
                    <div className="text-gray-400 text-sm">No chats yet</div>
                ) : (
                    <div className="space-y-2">
                        {sessions.map(session => (
                            <div
                                key={session.session_id}
                                onClick={() => {
                                    if (editingId !== session.session_id) {
                                        navigate(`/chat/${session.session_id}`);
                                    }
                                }}
                                className={`p-3 rounded-lg transition-colors group ${
                                    session.session_id === sessionId
                                        ? 'bg-blue-600'
                                        : 'bg-gray-700 hover:bg-gray-650'
                                } ${editingId === session.session_id ? '' : 'cursor-pointer'}`}
                            >
                                <div className="flex justify-between items-start">
                                    <div className="flex-1 min-w-0">
                                        {/* Editable title */}
                                        {editingId === session.session_id ? (
                                            <input
                                                type="text"
                                                value={editingTitle}
                                                onChange={(e) => setEditingTitle(e.target.value)}
                                                onKeyDown={(e) => handleKeyDown(e, session.session_id)}
                                                onBlur={() => saveEdit(session.session_id)}
                                                autoFocus
                                                className="w-full bg-gray-600 text-white text-sm px-2 py-1 rounded border border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            />
                                        ) : (
                                            <div className="font-medium text-sm truncate">
                                                {session.session_title}
                                            </div>
                                        )}
                                        <div className="text-xs text-gray-400 mt-1">
                                            {new Date(session.updated_at).toLocaleDateString()}
                                        </div>
                                    </div>

                                    {/* Action buttons */}
                                    {editingId !== session.session_id && (
                                        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                                            <button
                                                onClick={(e) => startEditing(session, e)}
                                                className="text-gray-400 hover:text-blue-400"
                                                title="Rename"
                                            >
                                                ✏️
                                            </button>
                                            <button
                                                onClick={(e) => handleDeleteSession(session.session_id, e)}
                                                className="text-gray-400 hover:text-red-400"
                                                title="Delete"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}