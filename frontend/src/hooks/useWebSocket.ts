import { useEffect, useRef, useCallback, useState } from 'react';
import { WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  sendMessage: (message: any) => void;
  connect: (analysisId: string) => void;
  disconnect: () => void;
}

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const analysisIdRef = useRef<string | null>(null);

  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        wsRef.current.close();
      }
      
      wsRef.current = null;
    }
  }, []);

  const attemptReconnect = useCallback(() => {
    if (reconnectCountRef.current < reconnectAttempts && analysisIdRef.current) {
      reconnectCountRef.current++;
      console.log(`WebSocket reconnection attempt ${reconnectCountRef.current}/${reconnectAttempts}`);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connect(analysisIdRef.current!);
      }, reconnectInterval);
    } else {
      console.log('WebSocket max reconnection attempts reached');
      setError('Failed to connect after multiple attempts');
      setIsConnecting(false);
    }
  }, [reconnectAttempts, reconnectInterval]);

  const connect = useCallback((analysisId: string) => {
    cleanup();
    
    analysisIdRef.current = analysisId;
    setIsConnecting(true);
    setError(null);
    
    try {
      const wsUrl = `${WS_BASE_URL}/ws/${analysisId}`;
      console.log(`Connecting to WebSocket: ${wsUrl}`);
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectCountRef.current = 0;
        onConnect?.();
      };
      
      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        
        onDisconnect?.();
        
        // Attempt reconnection if not a clean close
        if (event.code !== 1000 && analysisIdRef.current) {
          attemptReconnect();
        }
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket message received:', message);
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
          setError('Invalid message received from server');
        }
      };
      
      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setIsConnecting(false);
        onError?.(event);
      };
      
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to create WebSocket connection');
      setIsConnecting(false);
    }
  }, [cleanup, onMessage, onConnect, onDisconnect, onError, attemptReconnect]);

  const disconnect = useCallback(() => {
    analysisIdRef.current = null;
    reconnectCountRef.current = reconnectAttempts; // Prevent reconnection
    cleanup();
    setIsConnected(false);
    setIsConnecting(false);
    setError(null);
  }, [cleanup, reconnectAttempts]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (err) {
        console.error('Failed to send WebSocket message:', err);
        setError('Failed to send message');
      }
    } else {
      console.warn('WebSocket is not connected');
      setError('WebSocket is not connected');
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    isConnected,
    isConnecting,
    error,
    sendMessage,
    connect,
    disconnect,
  };
};

export default useWebSocket;