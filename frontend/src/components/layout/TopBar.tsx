import { useAuth } from '../../contexts/AuthContext';
import { useNavigate, useParams } from 'react-router-dom';
import { useState } from 'react';
import AddCaseModal from './AddCaseModal';
import AboutModal from './AboutModal';
import type { ChatSession } from '../../types';

interface TopBarProps {
    session?: ChatSession | null;
}

export default function TopBar({ session }: TopBarProps) {
    const { user, signOut } = useAuth();
    const navigate = useNavigate();
    const { sessionId } = useParams<{ sessionId?: string }>();

    // Add Case modal state
    const [showAddCaseModal, setShowAddCaseModal] = useState(false);
    // About modal state
    const [showAboutModal, setShowAboutModal] = useState(false);

    const handleShareSession = () => {
        if (sessionId) {
            const url = `${window.location.origin}/chat/${sessionId}`;
            navigator.clipboard.writeText(url);
            alert('Session URL copied to clipboard! Chat sessions can be viewed without logging in.');
        }
    };
  

    return (
        <>
        <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4">
            <div className="w-full flex justify-between items-center">
                {/* Left: Logo/Title (clickable to home) */}
                <div className="flex items-center gap-6">
                    <button
                        onClick={() => navigate('/')}
                        className="text-2xl font-bold hover:text-blue-400 transition-colors"
                    >
                        Court Case Q&A
                    </button>

                    {/* Case info - only show if in a session */}
                    {session && (
                        <div className="border-l border-gray-600 pl-6">
                            {/* <div className="text-sm text-gray-400">Current Case</div> */}
                            <div className="font-semibold text-white">{session.case_name || 'Unknown Case'}</div>
                            <div className="text-xs text-gray-500">
                                Case ID: {session.case_id}
                                <span className="mx-2 text-gray-600">|</span>
                                <a 
                                    href={`https://clearinghouse.net/case/${session.case_id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-400 hover:text-blue-300 hover:underline"
                                >
                                    Clearinghouse link
                                </a>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-4 shrink-0">
                    {/* Available Cases button - only show if logged in */}
                    {user && (
                        <button
                            onClick={() => navigate('/')}
                            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-1 px-4 rounded-lg transition duration-200 border border-blue-500 whitespace-nowrap"
                        >
                            📋 Available Cases
                        </button>
                    )}
                    {/* Share button - only show if viewing a session */}
                    {sessionId && user && (
                        <button
                            onClick={handleShareSession}
                            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-1 px-4 rounded-lg transition duration-200 whitespace-nowrap"
                        >
                            Copy URL
                        </button>
                    )}

                    {/* Add Case button - only show if logged in */}
                    {user && (
                        <button
                            onClick={() => setShowAddCaseModal(true)}
                            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-1 px-4 rounded-lg transition duration-200 whitespace-nowrap"
                        >
                            + Add Case
                        </button>
                    )}                    

                    {/* About Button */}
                    <button
                        onClick={() => setShowAboutModal(true)}
                        className="bg-gray-600 hover:bg-gray-500 text-white font-semibold py-1 px-4 rounded-lg transition duration-200 flex items-center gap-2 whitespace-nowrap"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        About
                    </button>

                    {/* User email + Sign Out (if logged in) */}
                    {user && (
                        <>
                            {/* Settings Button (New) */}
                            <button
                                onClick={() => navigate('/settings')}
                                className="text-gray-300 hover:text-white"
                                title="Settings"
                            >
                                ⚙️
                            </button>
                            <span className="text-gray-300 whitespace-nowrap hidden lg:inline">{user.email}</span>
                            <button
                                onClick={signOut}
                                className="bg-red-600 hover:bg-red-700 text-white font-semibold py-1 px-4 rounded-lg transition duration-200 whitespace-nowrap"
                            >
                                Sign Out
                            </button>
                        </>
                    )}

                    {/* Login button (if NOT logged in) */}
                    {!user && (
                        <button
                            onClick={() => navigate('/login')}
                            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-1 px-4 rounded-lg transition duration-200 whitespace-nowrap"
                        >
                            Log In
                        </button>
                    )}
                </div>
            </div>
        </nav>

        {/* Add Case Modal */}
        <AddCaseModal 
            isOpen={showAddCaseModal}
            onClose={() => setShowAddCaseModal(false)}
            // onSuccess={handleCaseAdded}
        />
        
        {/* About Modal */}
        <AboutModal
            isOpen={showAboutModal}
            onClose={() => setShowAboutModal(false)}
        />
        </> 
    );
}