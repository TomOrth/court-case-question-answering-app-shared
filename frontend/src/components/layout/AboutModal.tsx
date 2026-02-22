interface AboutModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AboutModal({ isOpen, onClose }: AboutModalProps) {
    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
                onClick={onClose}
            />

            {/* Modal */}
            <div 
                className="fixed inset-0 flex items-center justify-center z-50 p-4"
                onClick={onClose}
            >
                <div 
                    className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-semibold text-white">About Court Case Q&A</h2>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-white transition-colors"
                        >
                            ✕
                        </button>
                    </div>

                    {/* Content */}
                    <div className="space-y-4 text-gray-300">
                        <p>
                            This demo app allows users to evaluate an AI chatbot's ability to answer questions about court cases that are publicly available via the University of Michigan's Civil Rights Litigation Clearinghouse.
                        </p>
                        
                        <div>
                            <h3 className="text-white font-semibold mb-2">Usage:</h3>
                            <ul className="list-disc pl-5 space-y-1">
                                <li>Sign up for an account (check your email for confirmation link)</li>
                                <li>Select an available case / Add a new case (wait 5-15 minutes for preprocessing, then refresh the page).</li>
                                <li>The chatbot will query documents in the case to answer questions and cite sources.</li>
                                <li>Click to expand the chatbot's step-by-step reasoning & tool calls.</li>
                                <li>Copy chat URL to share with others for discussion (no log in required)</li>
                            </ul>
                        </div>

                        <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600 mt-6">
                            <p className="text-sm text-gray-400">
                                <span className="font-semibold text-yellow-500">Note:</span> Please feel free to test the app as much as you need, but please note that preprocessing new cases and generating answers incur small charges that for now are covered by the developer.
                            </p>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="mt-8 flex justify-end">
                        <button
                            onClick={onClose}
                            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition duration-200"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
}
