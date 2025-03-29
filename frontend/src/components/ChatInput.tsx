import React, { useState, useEffect, useRef } from 'react';

interface ChatInputProps {
  sendMessage: (message: string) => void;
  isDisabled: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ sendMessage, isDisabled }) => {
  const [message, setMessage] = useState('');
  const [promptHistory, setPromptHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [currentInput, setCurrentInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load prompt history from localStorage
  useEffect(() => {
    const STORAGE_KEY = 'browserAgentPromptHistory';
    const savedHistory = localStorage.getItem(STORAGE_KEY);
    if (savedHistory) {
      setPromptHistory(JSON.parse(savedHistory));
    }
    setHistoryIndex(JSON.parse(savedHistory || '[]').length);
    
    // Focus the textarea on load
    textareaRef.current?.focus();
  }, []);

  // Save prompt history to localStorage when it changes
  useEffect(() => {
    if (promptHistory.length > 0) {
      localStorage.setItem('browserAgentPromptHistory', JSON.stringify(promptHistory));
    }
  }, [promptHistory]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isDisabled) {
      sendMessage(message);
      
      // Add to history (avoiding consecutive duplicates)
      if (promptHistory.length === 0 || promptHistory[promptHistory.length - 1] !== message) {
        setPromptHistory([...promptHistory, message]);
        setHistoryIndex(historyIndex + 1);
      }
      
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Handle Shift+Enter to create new lines
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent default newline
      handleSubmit(e as unknown as React.FormEvent);
      return;
    }

    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      if (!e.ctrlKey && !e.metaKey) {
        // Only intercept arrow keys for history when used with Ctrl/Cmd
        return;
      }

      if (historyIndex === promptHistory.length) {
        // Store current potentially unsaved input before navigating
        setCurrentInput(message);
      }

      if (e.key === 'ArrowUp') {
        if (promptHistory.length > 0 && historyIndex > 0) {
          e.preventDefault(); // Prevent cursor moving to start
          setHistoryIndex(historyIndex - 1);
          setMessage(promptHistory[historyIndex - 1]);
        }
      } else if (e.key === 'ArrowDown') {
        if (historyIndex < promptHistory.length - 1) {
          e.preventDefault(); // Prevent cursor moving to end
          setHistoryIndex(historyIndex + 1);
          setMessage(promptHistory[historyIndex + 1]);
        } else if (historyIndex === promptHistory.length - 1) {
          // Reached the end of history, restore potentially unsaved input
          setHistoryIndex(promptHistory.length);
          setMessage(currentInput);
        }
      }
    } else if (e.key !== 'Enter' && e.key !== 'Shift') {
      // Any other key press means the user is typing something new
      setHistoryIndex(promptHistory.length);
      setCurrentInput('');
    }
  };

  // Auto-resize textarea height based on content
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target;
    setMessage(textarea.value);
    
    // Reset height to auto to correctly calculate the new height
    textarea.style.height = 'auto';
    // Set the height to match the content (plus a small buffer)
    textarea.style.height = `${textarea.scrollHeight}px`;
  };

  return (
    <form onSubmit={handleSubmit} className="flex p-3 bg-gray-100 dark:bg-gray-800 border-t border-gray-300 dark:border-gray-700">
      <textarea
        ref={textareaRef}
        value={message}
        onChange={handleTextareaChange}
        onKeyDown={handleKeyDown}
        placeholder="Type your instruction here... (Shift+Enter for new line)"
        className="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded-md mr-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none overflow-hidden min-h-[38px] max-h-[200px]"
        disabled={isDisabled}
        rows={1}
      />
      <button
        type="submit"
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed h-fit"
        disabled={isDisabled || !message.trim()}
      >
        Send
      </button>
    </form>
  );
};

export default ChatInput; 
