import { io, Socket } from 'socket.io-client';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface WebSocketContextType {
  socket: Socket | null;
  connected: boolean;
  lastMessage: any;
}

const WebSocketContext = createContext<WebSocketContextType>({
  socket: null,
  connected: false,
  lastMessage: null,
});

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    const newSocket = io('http://localhost:8000', {
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    newSocket.on('connect', () => {
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      setConnected(false);
    });

    newSocket.on('scraper_update', (data) => {
      setLastMessage({ type: 'scraper_update', data });
    });

    newSocket.on('log_update', (data) => {
      setLastMessage({ type: 'log_update', data });
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ socket, connected, lastMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  return useContext(WebSocketContext);
}
