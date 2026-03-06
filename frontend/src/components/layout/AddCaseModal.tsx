import { useState, useEffect } from 'react';
import { api } from '../../services/api';

interface AddCaseModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AddCaseModal({ isOpen, onClose }: AddCaseModalProps) {
    const [caseId, setCaseId] = useState('');
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');

    // Reset state when modal opens
    useEffect(() => {
        if (isOpen) {
            setCaseId('');
            setStatus('idle');
            setMessage('');
        }
    }, [isOpen]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        const caseIdNum = parseInt(caseId);
        if (!caseIdNum || isNaN(caseIdNum)) {
            setStatus('error');
            setMessage('Please enter a valid case ID (number)');
            return;
        }

        // Fire and forget - don't wait for response
        api.preprocessing.preprocessCase(caseIdNum)
            .then(response => {
                console.log('Preprocessing started:', response);
            })
            .catch(err => {
                console.error('Preprocessing error:', err);
                // Error is silent - user already sees success message
            });

        // Immediately show success
        setStatus('success');
        setMessage(`Preprocessing started for Case ID ${caseIdNum}`);
    };

    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-50 z-40"
                onClick={onClose}
            />

            {/* Modal */}
            <div
                className="fixed inset-0 flex items-center justify-center z-50 p-4"
                onClick={onClose}
            >
                <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-semibold text-white">Add New Case</h2>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-white transition-colors"
                        >
                            ✕
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={(e) => handleSubmit(e)} className="space-y-4">
                        <div>
                            <label htmlFor="caseId" className="block text-sm font-medium text-gray-300 mb-2">
                                Case ID (from Clearinghouse)
                            </label>
                            <input
                                type="text"
                                id="caseId"
                                value={caseId}
                                onChange={(e) => setCaseId(e.target.value)}
                                placeholder="e.g., 14919"
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                                required
                            />
                            <p className="text-xs text-gray-400 mt-1">
                                Find case IDs at <a href="https://clearinghouse.net/" target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">clearinghouse.net (Open in a new tab)</a>
                            </p>
                        </div>

                        {/* Status messages */}
                        {message && (
                            <div className={`p-3 rounded-lg text-sm ${status === 'error'
                                ? 'bg-red-900/50 border border-red-700 text-red-200'
                                : 'bg-green-900/50 border border-green-700 text-green-200'
                                }`}>
                                {message}
                            </div>
                        )}

                        {/* Success info */}
                        {status === 'success' && (
                            <div className="bg-gray-700 p-4 rounded-lg space-y-2">
                                <p className="text-sm text-gray-300">
                                    <strong>⏱️ Processing time:</strong> 5-15 minutes
                                </p>
                                <p className="text-sm text-yellow-300">
                                    ℹ️ The case continues to be preprocessed even if you close this screen or reload the page.
                                </p>
                                <p className="text-sm text-gray-300">
                                    If the case is successfully preprocessed, it will show up in the dropdown after 15 minutes.
                                </p>
                                <p className="text-sm text-gray-400">
                                    Please check back later.
                                </p>
                            </div>
                        )}

                        {/* Buttons */}
                        {status !== 'success' && (
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                                >
                                    Close
                                </button>
                                <button
                                    type="button"
                                    className="flex-1 bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg"
                                >
                                    Add Case
                                </button>
                            </div>
                        )}

                        {/* Close button after success */}
                        {status === 'success' && (
                            <button
                                type="button"
                                onClick={onClose}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                            >
                                Got it
                            </button>
                        )}
                    </form>
                </div>
            </div>
        </>
    );
}