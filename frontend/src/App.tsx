import React, { useState, useEffect } from 'react';
import { io, Socket } from 'socket.io-client';
import ChatContainer from './components/ChatContainer';
import Navbar from './components/Navbar';

const App: React.FC = () => {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme as 'dark' | 'light';
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    const newSocket = io();
    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, []);

  useEffect(() => {
    // Remove both classes first
    document.documentElement.classList.remove('dark', 'light-mode');
    
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.add('light-mode');
    }
    
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
      <Navbar theme={theme} toggleTheme={toggleTheme} />
      <div className="flex-1 container mx-auto p-4">
        {socket && <ChatContainer socket={socket} />}
      </div>
    </div>
  );
};

export default App; 
