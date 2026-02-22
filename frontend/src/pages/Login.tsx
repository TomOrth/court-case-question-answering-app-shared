/**
 * Login Page
 * 
 * Allows users to sign in with email and password.
 * Redirects to home page on successful login.
 */

import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
    // state management
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    // hooks
    const { signIn } = useAuth()
    const navigate = useNavigate()

    // event handlers
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        const { error } = await signIn(email, password)
        if (error) {
            setError(error.message)
            setLoading(false)
        } else {
            // no need to setLoading(false) because we're leaving this page
            // onAuthStateChange in AuthContext will update user state automatically

            // navigate to home page
            navigate('/')
        }
    }

    // render
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900">
            {/* card container */}
            <div className="bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-md">
                {/* Main heading */}
                <h1 className="text-3xl font-bold text-white mb-6 text-center">
                    Court Case Q&A
                </h1>
                {/* Subheading */}
                <h2 className="text-xl text-gray-300 mb-6 text-center">
                    Sign in to your account
                </h2>
                {/* Form element - handles submission */}
                <form action="" className="space-y-4" onSubmit={handleSubmit}>
                    {/* error message */}
                    {error && (
                        <div className="bg-red-900 border border-red-700 px-4 py-3">
                            {error}
                        </div>
                    )}
                    {/* Email input field  */}
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                            Email
                        </label>
                        <input 
                            type="email" 
                            id="email" 
                            required 
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="you@example.com"
                        />
                    </div>
                    {/* Password input field */}
                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                        <input 
                            id="password"
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                            placeholder="••••••••"
                        />
                    </div>
                    {/* Submit button  */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>
                {/* Sign up link  */}
                <p className="mt-6 text-center text-gray-400">
                    Don't have an account?{' '}
                    <Link to="/signup" className="text-blue-400 hover:text-blue-300">
                        Sign Up
                    </Link>
                </p>

                <p className="mt-8 text-center text-xs text-gray-500 max-w-sm mx-auto">
                    This demo app allows users to evaluate an AI chatbot's ability to answer questions about court cases that are publicly available via the University of Michigan's Civil Rights Litigation Clearinghouse.
                </p>

                <p className="mt-4 text-center text-xs text-gray-500 max-w-sm mx-auto">
                    To view an example conversation about a court case (no log-in required), see <a href="https://court-case-question-answering-app.vercel.app/chat/1063dd43-d1ea-4b8d-b00c-0b58ee57cc3a" className="text-blue-400 hover:text-blue-300 underline" target="_blank" rel="noopener noreferrer">this link</a>.
                </p>
                
            </div>
        </div>
    )
}