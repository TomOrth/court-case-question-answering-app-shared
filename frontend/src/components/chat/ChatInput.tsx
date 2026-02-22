import { useState, type KeyboardEvent, useRef, useEffect } from 'react';

interface ChatInputProps {
    onSend: (content: string) => void;
    disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
    const [text, setText] = useState('');
    const [error, setError] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const MAX_LENGTH = 2000;

    const handleSend = () => {
        const trimmedText = text.trim();
        
        if (!trimmedText) return;
        
        if (disabled) return;

        if (trimmedText.length > MAX_LENGTH) {
            setError(`Message is too long. Please limit to ${MAX_LENGTH} characters. (Current: ${trimmedText.length})`);
            return;
        }

        onSend(trimmedText);
        setText('');
        setError('');
        
        // Reset height
        if (textareaRef.current) {
            textareaRef.current.style.height = '50px';
        }
    }

    const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setText(e.target.value);
        if (error) setError('');
    };

    // Auto-resize textarea based on content
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = '50px'; // Reset to min height
            const scrollHeight = textarea.scrollHeight;
            textarea.style.height = Math.min(scrollHeight, 200) + 'px'; // Max 200px
        }
    }, [text]);

    return (
        <div className="p-4 bg-gray-800 border-t border-gray-700 flex-shrink-0">
            <div className="max-w-4xl mx-auto flex flex-col gap-2">
                {error && (
                    <div className="text-red-400 text-sm px-1">
                        {error}
                    </div>
                )}
                <div className="flex gap-2">
                    <textarea 
                        ref={textareaRef}
                        name="" 
                        id="" 
                        className={`flex-1 bg-gray-900 text-white rounded-lg p-3 border ${error ? 'border-red-500' : 'border-gray-700'} focus:border-blue-500 focus:outline-none resize-none min-h-[50px] max-h-[200px]`}
                        value={text} 
                        onKeyDown={handleKeyDown} 
                        placeholder="Ask a question about this case..." 
                        disabled={disabled}
                        onChange={handleChange}
                        style={{ height: '50px', overflowY: 'auto' }}
                    />
                    <button className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-6 rounded-lg font-medium transition-colors flex items-center gap-2" onClick={handleSend} disabled={disabled || !text.trim()}>
                        {disabled ? (
                            <>
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                
                            </>
                        ) : (
                            'Send'
                        )}
                    </button>
                </div>
                <div className="text-xs text-gray-500 text-right px-1">
                    {text.length}/{MAX_LENGTH}
                </div>
            </div>
        </div>
    )

}