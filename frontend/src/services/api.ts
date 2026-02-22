import { supabase } from "../utils/supabaseClient";
import type { Case, ChatSession, Citation } from "../types";
import type {  PreprocessCaseResponse } from "../types";

const API_URL = import.meta.env.VITE_API_URL

/**
 * Make authenticated API request.
 * 
 * Automatically includes JWT token in Authorization header.
 * 
 * @param endpoint - API endpoint path (e.g., "/api/auth/me")
 * @param options - Fetch options (method, body, headers, etc.)
 * @returns Promise with JSON response data
 * @throws Error if not authenticated or request fails
 */
async function authenticatedFetch(endpoint: string, options: RequestInit = {}) {
    // get JWT token from Supabase
    // Get current session fromm Supabase
    const { data: { session } } = await supabase.auth.getSession()

    // Check if user is authenticated
    if (!session) {
        throw new Error('Not authenticated')
    }

    // Make authenticated request
    // Make fetch request with JWT token
    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
        }
    })

    // Error handling
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
    }

    // Handle no-content responses
    if (response.status === 204 || response.headers.get('content-length') === '0') {
        return undefined  // or null
    }    
    
    // Return JSON data
    return response.json()
}

export const api = {
    auth: {
        getMe: () => authenticatedFetch('/api/auth/me'),
        testProtected: () => authenticatedFetch('/api/auth/protected'),
    },

    chat: {
        // get available cases for new chat
        getAvailableCases: async (): Promise<Case[]> => {
            return authenticatedFetch('/api/chat/cases');
        },

        // get user's chat sessions
        getSessions: async (): Promise<ChatSession[]> => {
            return authenticatedFetch('/api/chat/sessions')
        },

        // create a new session
        createSession: async (caseId: number): Promise<ChatSession> => {
            return authenticatedFetch('/api/chat/sessions', {
                method: 'POST',
                body: JSON.stringify({ case_id: caseId })
            })
        },

        // get a specific session (public - no auth required for viewing shared sessions)
        getSession: async (sessionId: string): Promise<ChatSession> => {
            const response = await fetch(`${API_URL}/api/chat/sessions/${sessionId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load session: ${response.statusText}`);
            }

            return response.json();
        },

        // delete a session
        deleteSession: async (sessionId: string): Promise<void> => {
            return authenticatedFetch(`/api/chat/sessions/${sessionId}`, {
                method: 'DELETE'
            });
        },

        // rename a session
        renameSession: async (sessionId: string, newTitle: string): Promise<ChatSession> => {
            return authenticatedFetch(`/api/chat/sessions/${sessionId}`, {
                method: 'PATCH',
                body: JSON.stringify({ session_title: newTitle })
            });
        },

        // Send a message and handle streaming response
        sendMessageStream: async (
            sessionId: string,
            content: string,
            onChunk: (event: any) => void
        ): Promise<void> => {
            const { data: { session } } = await supabase.auth.getSession()
            if (!session) throw new Error('Not authenticated')

            const response = await fetch(`${API_URL}/api/chat/sessions/${sessionId}/messages`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session.access_token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            })

            if (!response.ok) {
                throw new Error('Failed to send message')
            }

            if (!response.body) return;

            // Create a reader
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // Decode the chunk
                const chunk = decoder.decode(value, { stream: true });
                
                buffer += chunk

                // split by new line to get NDJSON objects
                const lines = buffer.split('\n');

                // Keep the last part in buffer if it's incomplete
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const event = JSON.parse(line);
                            onChunk(event);
                        } catch (e) {
                            console.log("Error parsing stream line", e);
                        }
                    }
                }
            }
        }
    },

    citations: {
        // Fetch citation details by ID (public - no auth required for viewing citations in shared sessions)
        async getCitation(citationId: string): Promise<Citation> {
            const response = await fetch(`${API_URL}/api/citations/${citationId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error(`Citation not found: ${citationId}`);
                }
                if (response.status === 400) {
                    throw new Error(`Invalid citation ID format: ${citationId}`);
                }
                throw new Error(`Failed to fetch citation: ${response.statusText}`);
            }
            
            return response.json();
        }
    },

    preprocessing: {
        // Trigger preprocessing for a case (fire and forget)
        preprocessCase: async (caseId: number): Promise<PreprocessCaseResponse> => {
            return authenticatedFetch('/api/preprocessing/case', {
                method: 'POST',
                body: JSON.stringify({ case_id: caseId })
            });
        }
    }    
    
};