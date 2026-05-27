"use client";

import { useEffect, useRef, useState } from "react";

interface WebSocketOptions {
  onMessage?: (data: unknown) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket(
  url: string,
  { onMessage, onOpen, onClose, onError }: WebSocketOptions = {}
) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<unknown>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      onOpen?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        onMessage?.(data);
      } catch {
        onMessage?.(event.data);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      onClose?.();
    };

    ws.onerror = (error) => {
      onError?.(error);
    };

    return () => {
      ws.close();
    };
  }, [url]);

  const send = (data: unknown) => {
    wsRef.current?.send(JSON.stringify(data));
  };

  return { isConnected, lastMessage, send };
}