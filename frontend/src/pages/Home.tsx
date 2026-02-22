/**
 * Home Page
 * 
 * Main page after login. Shows user email and logout button.
 * This is a placeholder - we'll build the actual UI later.
 */

import { api } from '../services/api'
import { useState, useEffect } from 'react'
import type { Case } from '../types'
import { useNavigate } from 'react-router-dom'

export default function Home() {
    // hooks
    // const { user, signOut } = useAuth()
    const navigate = useNavigate()

    // State for data
    const [cases, setCases] = useState<Case[]>([])
    // const [sessions, setSessions] = useState<ChatSession[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    // State for "New Chat" selection
    const [selectedCaseId, setSelectedCaseId] = useState<number | ''>('')
    const [creating, setCreating] = useState(false)

    // Fetch data on mount
    useEffect(() => {

        const fetchData = async () => {
            try {
                // const [casesData, sessionsData] = await Promise.all([
                //     api.chat.getAvailableCases(),
                //     api.chat.getSessions()
                // ])
                const casesData = await api.chat.getAvailableCases()
                setCases(casesData)
                // setSessions(sessionsData)
            
            } catch(err) {
                console.error(err)
                setError('Failed to load data')
            } finally {
                setLoading(false)
            }
        }

        fetchData()
    }, [])

    // Handle creating a new chat
    const handleStartChat = async () => {

        if (!selectedCaseId) return

        setCreating(true)
        try {
            const newSession = await api.chat.createSession(Number(selectedCaseId))
            navigate(`/chat/${newSession.session_id}`)
        } catch(err) {
            console.error(err)
            setError('Failed to create chat session')
        } finally {
            setCreating(false)
        }
    }

    // // Handle deleting a session
    // const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {

    //     e.stopPropagation()
    //     if (!confirm("Are you sure you want to delete this chat?")) return;

    //     try {
    //         await api.chat.deleteSession(sessionId);
    //         // remove from local state
    //         setSessions(sessions.filter(s => s.session_id !== sessionId));
    //     } catch(err) {
    //         console.error(err);
    //         alert("Failed to delete session")
    //     }
    // }
    
    // render
    return (
        <div className="p-6">
            <div className="max-w-7xl mx-auto flex justify-center">
                {/* Error */}
                {error && (
                    <div className="bg-red-900/50 border border-red-700 text-red-200 p-4 rounded mb-6">
                        {error}
                    </div>
                )}

                {/* Case Selector Card */}
                <div className="bg-gray-800 p-6 rounded-lg max-w-md">
                    <div className="flex items-center gap-2 mb-4">
                        <h2 className="text-xl font-semibold">
                            Start New Chat
                        </h2>
                        {loading && (
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                        )}
                    </div>
                    <p className="text-gray-400 text-sm mb-4">
                        Select a processed case to begin analyzing. (Try reloading the page if you have added a case for preprocessing.)
                    </p>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">
                                Select Case
                            </label>
                            <select 
                                value={selectedCaseId}
                                onChange={(e) => setSelectedCaseId(Number(e.target.value))}
                                disabled={loading}
                                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <option value="">-- Choose a case --</option>
                                {cases.map(c => (
                                    <option key={c.case_id} value={c.case_id}>
                                        {`[${c.case_id}] ${c.case_name}`}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <button
                            onClick={handleStartChat}
                            disabled={!selectedCaseId || creating || loading}
                            className={`w-full py-2 px-4 rounded font-medium transition-colors ${
                                !selectedCaseId || creating || loading ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'
                            }`}
                        >
                            {creating ? 'Creating...' : 'Start Chat'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )

    // render
    // return (
    //     <div className="min-h-screen bg-gray-900 text-white">
    //         {/* navigation bar */}
    //         <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4">
    //             <div className="max-w-7xl mx-auto flex justify-between items-center">
    //                 {/* left side: logo/title*/}
    //                 <h1 className="text-2xl font-bold">Court Case Q&A</h1>

    //                 {/* right side: user info and logout button */}
    //                 <div className="flex items-center gap-4">
    //                     {/* display user email */}
    //                     <span className="text-gray-300">{user?.email}</span>
    //                     {/* sign out button */}
    //                     <button
    //                         onClick={signOut}
    //                         className="bg-red-600 hover:bg-red-700 text-white font-semibold py-1 px-4 rounded-lg transition duration-200"
    //                     >
    //                         Sign Out
    //                     </button>
    //                 </div>
    //             </div>
    //         </nav>

    //         {/* main content */}
    //         <main className="max-w-7xl mx-auto px-6 py-8">
    //             {/* error  */}
    //             {error && (
    //                 <div className="bg-red-900/50 border border-red-700 text-red-200 p-4 rounded mb-6">
    //                     {error}
    //                 </div>
    //             )}
    //             <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
    //                 {/* LEFT COLUMN Start New Chat */}
    //                 <div className="md:col-span-1 bg-gray-800 p-6 rounded-lg">
    //                     <h2 className="text-xl font-semibold mb-4">
    //                         Start New Chat
    //                     </h2>
    //                     <p className="text-gray-400 text-sm mb-4">
    //                         Select a processed case to begin analyzing.
    //                     </p>
    //                     <div className="space-y-4">
    //                         <div>
    //                             <label className="block text-sm font-medium text-gray-400 mb-1">
    //                                 Select Case
    //                             </label>
    //                             <select 
    //                                 value={selectedCaseId}
    //                                 onChange={(e) => setSelectedCaseId(Number(e.target.value))}
    //                                 className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
    //                             >
    //                                 <option value="">-- Choose a case --</option>
    //                                 {cases.map(c => (
    //                                     <option key={c.case_id} value={c.case_id}>
    //                                         {`[${c.case_id}] ${c.case_name}`}
    //                                     </option>
    //                                 ))}

    //                             </select>
    //                         </div>

    //                         <button
    //                             onClick={handleStartChat}
    //                             disabled={!selectedCaseId || creating}
    //                             className={`w-full py-2 px-4 rounded font-medium transition-colors ${
    //                                 !selectedCaseId || creating ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'
    //                             }`}
    //                         >
    //                             {creating ? 'Creating...' : 'Start Chat'}
    //                         </button>
    //                     </div>
    //                 </div>

    //                 {/* RIGHT COLUMN Recent Chats  */}
    //                 <div className="md:col-span-2">
    //                     <h2 className="text-xl font-semibold mb-4">
    //                         Your Chats
    //                     </h2>
    //                     {loading ? (
    //                         <div className="text-gray-400">
    //                             Loading sessions...
    //                         </div>
    //                     ) : sessions.length === 0 ? (
    //                         <div className="bg-gray-800 p-8 rounded-lg text-center text-gray-400">
    //                             No chat sessions yet. Start one on the left!
    //                         </div>

    //                     ) : (
    //                         <div className="space-y-3">
    //                             {sessions.map(session => (
    //                                 <div
    //                                     key={session.session_id}
    //                                     onClick={() => navigate(`/chat/${session.session_id}`)}
    //                                     className="bg-gray-800 p-4 rounded-lg hover:bg-gray-750 cursor-pointer transition-colors border border-gray-700 hover:border-gray-600 flex justify-between items-center group"
    //                                 >
    //                                     <div>
    //                                         <h3 className="font-medium text-blue-300 group-hover:text-blue-200">
    //                                             {session.session_title}
    //                                         </h3>
    //                                         <p className="text-sm text-gray-500">
    //                                             Last updated: {new Date(session.updated_at).toLocaleDateString()}
    //                                         </p>
    //                                     </div>
    //                                     <button
    //                                         onClick={(e) => handleDeleteSession(session.session_id, e)}
    //                                         className="text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1"
    //                                         title="Delete chat"
    //                                     >
    //                                         X
    //                                     </button>

    //                                 </div>
    //                             ))}
    //                         </div>
    //                     )}
    //                 </div>
    //             </div>

    //         </main>
    //     </div>
    // )
}