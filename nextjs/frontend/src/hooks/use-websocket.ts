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
  const onMessageRef = useRef(onMessage);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const onErrorRef = useRef(onError);
  onMessageRef.current = onMessage;
  onOpenRef.current = onOpen;
  onCloseRef.current = onClose;
  onErrorRef.current = onError;

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      onOpenRef.current?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        onMessageRef.current?.(data);
      } catch {
        onMessageRef.current?.(event.data);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      onCloseRef.current?.();
    };

    ws.onerror = (error) => {
      onErrorRef.current?.(error);
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