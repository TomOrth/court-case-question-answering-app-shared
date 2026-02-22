/**
 * Protected Route Component
 * 
 * Wraps routes that require authentication.
 * Redirects to login if user is not authenticated.
 */

import { Navigate } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    // hooks
    const { user, loading } = useAuth()

    // conditional rendering

    // case 1: still checking if user is logged in
    if (loading) {
        // show loading indicator
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-900">
                <div className="text-white text-xl">
                    Loading...
                </div>
            </div>
        )
    }

    // case 2: finished checking, user is NOT logged in
    if (!user) {
        return <Navigate to="/login" replace />
    }

    // case 3: user is logged in
    return <>{children}</>
}