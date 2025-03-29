import React, { RefObject } from 'react';
import { MessageData } from './ChatContainer';
import ScreenshotGallery from './ScreenshotGallery';

interface ChatMessagesProps {
  messages: MessageData[];
  messagesEndRef: RefObject<HTMLDivElement>;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, messagesEndRef }) => {
  // Helper function to render message content with markdown-like formatting
  const renderMessageContent = (content: string) => {
    // Handle code blocks
    let htmlContent = content.replace(/```(?:\w+\n)?([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Handle bold text
    htmlContent = htmlContent.replace(/\*\*([\s\S]*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text
    htmlContent = htmlContent.replace(/\*([\s\S]*?)\*/g, '<em>$1</em>');
    
    // Handle inline code
    htmlContent = htmlContent.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    return <div dangerouslySetInnerHTML={{ __html: htmlContent }} />;
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 bg-gray-50 dark:bg-gray-900">
      {messages.map((message, index) => (
        <div 
          key={message.id || index}
          className={`message ${message.type === 'user' ? 'user-message' : message.type}`}
        >
          {renderMessageContent(message.content)}
          
          {message.screenshots && message.screenshots.length > 0 && (
            <ScreenshotGallery screenshots={message.screenshots} />
          )}
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatMessages; 
