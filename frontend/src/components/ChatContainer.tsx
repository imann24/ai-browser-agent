import React, { useState, useEffect, useRef } from 'react';
import { Socket } from 'socket.io-client';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';

interface ChatContainerProps {
  socket: Socket;
}

export interface MessageData {
  id?: string;
  content: string;
  type: 'user' | 'agent' | 'thinking' | 'progress-message' | 'error';
  screenshots?: ScreenshotData[];
}

export interface ScreenshotData {
  image: string;
  description: string;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ socket }) => {
  const [messages, setMessages] = useState<MessageData[]>([
    { type: 'agent', content: "Hello! I'm your browser assistant. Tell me what you'd like me to help you with on the web." }
  ]);
  const [isInputDisabled, setIsInputDisabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Keep track of the current thinking message ID to update it when a response comes in
  const thinkingMessageIdRef = useRef<string | null>(null);

  useEffect(() => {
    // Scroll to bottom when messages update
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Socket event handlers
    socket.on('agent response', (data: any) => {
      console.log('Received:', data);
      setIsInputDisabled(false);

      switch (data.type) {
        case 'thinking':
          const thinkingId = `msg-${Date.now()}`;
          thinkingMessageIdRef.current = thinkingId;
          
          setMessages(prevMessages => [
            ...prevMessages,
            { id: thinkingId, type: 'thinking', content: data.message, screenshots: [] }
          ]);
          break;
          
        case 'progress':
          if (thinkingMessageIdRef.current) {
            setMessages(prevMessages => 
              prevMessages.map(msg => 
                msg.id === thinkingMessageIdRef.current 
                  ? { ...msg, type: 'progress-message', content: data.message }
                  : msg
              )
            );
          }
          break;
          
        case 'screenshot':
          if (thinkingMessageIdRef.current) {
            setMessages(prevMessages => 
              prevMessages.map(msg => {
                if (msg.id === thinkingMessageIdRef.current) {
                  const newScreenshots = [...(msg.screenshots || []), {
                    image: data.screenshot,
                    description: data.description
                  }];
                  return { ...msg, screenshots: newScreenshots };
                }
                return msg;
              })
            );
          }
          break;
          
        case 'result':
          if (thinkingMessageIdRef.current) {
            setMessages(prevMessages => 
              prevMessages.map(msg => 
                msg.id === thinkingMessageIdRef.current 
                  ? { ...msg, type: 'agent', content: data.message }
                  : msg
              )
            );
            thinkingMessageIdRef.current = null;
          } else {
            setMessages(prevMessages => [
              ...prevMessages,
              { type: 'agent', content: data.message }
            ]);
          }
          break;
          
        case 'error':
          if (thinkingMessageIdRef.current) {
            setMessages(prevMessages => 
              prevMessages.map(msg => 
                msg.id === thinkingMessageIdRef.current 
                  ? { ...msg, type: 'error', content: data.message }
                  : msg
              )
            );
            thinkingMessageIdRef.current = null;
          } else {
            setMessages(prevMessages => [
              ...prevMessages,
              { type: 'error', content: data.message }
            ]);
          }
          break;
      }
    });

    return () => {
      socket.off('agent response');
    };
  }, [socket]);

  const sendMessage = (message: string) => {
    if (message.trim()) {
      setMessages(prevMessages => [
        ...prevMessages,
        { type: 'user', content: message }
      ]);
      socket.emit('chat message', message);
      setIsInputDisabled(true);
    }
  };

  return (
    <div className="flex flex-col h-full border border-gray-300 dark:border-gray-700 rounded-lg overflow-hidden shadow-sm">
      <ChatMessages messages={messages} messagesEndRef={messagesEndRef} />
      <ChatInput sendMessage={sendMessage} isDisabled={isInputDisabled} />
    </div>
  );
};

export default ChatContainer; 
