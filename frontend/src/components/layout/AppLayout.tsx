import { Outlet, useOutletContext } from 'react-router-dom';
import TopBar from './TopBar';
import LeftSidebar from './LeftSidebar';
import { useAuth } from '../../contexts/AuthContext';
import { useState } from 'react';
import type { ChatSession } from '../../types';

type OutletContextType = {
    setSession: (session: ChatSession | null) => void;
};

export default function AppLayout() {
    const { user } = useAuth();
    const [session, setSession] = useState<ChatSession | null>(null);

    return (
        <div className="h-screen bg-gray-900 text-white flex flex-col overflow-hidden">
            {/* TopBar always visible - fixed at top */}
            <TopBar session={session} />

            {/* Free Tier Notification */}
            <div className="bg-blue-900/40 border-b border-blue-800/50 px-4 py-1.5 text-center text-xs text-blue-200">
                Please note: This demo is hosted on a free-tier server, so the first request may take up to a minute for the app to 'wake up.' Subsequent requests will be faster.
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* LeftSidebar - only if logged in */}
                {user && (
                    <LeftSidebar />
                )}

                {/* Main content area - rendered by routes, no overflow here */}
                <main className="flex-1 flex flex-col overflow-hidden">
                    <Outlet context={{ setSession }} />
                </main>
            </div>
        </div>
    );
}

export function useAppLayout() {
    return useOutletContext<OutletContextType>();
}