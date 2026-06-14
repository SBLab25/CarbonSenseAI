import { useState, useRef, useCallback, useEffect } from 'react';

export function useStream() {
  const [content, setContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setContent('');
    setIsStreaming(false);
    setError(null);
  }, []);

  const startStream = useCallback(async (
    endpoint: string, 
    body: object, 
    callbacks?: { onMessageSplit?: (msg: string) => void, onUpdateDashboard?: () => void }
  ) => {
    reset();
    
    setIsStreaming(true);
    setError(null);
    setContent('');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const aiConfigStr = localStorage.getItem('ai_config');
    const aiHeaders: Record<string, string> = {};
    if (aiConfigStr) {
      try {
        const config = JSON.parse(aiConfigStr);
        if (config.provider) aiHeaders['X-AI-Provider'] = config.provider;
        if (config.apiKey) aiHeaders['X-AI-Key'] = config.apiKey;
        if (config.model) aiHeaders['X-AI-Model'] = config.model;
      } catch {}
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...aiHeaders,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        let msg = 'Stream request failed';
        try {
          const err = await response.json();
          msg = err.detail || msg;
        } catch {
          // ignore
        }
        throw new Error(msg);
      }

      if (!response.body) {
        throw new Error('Response body is not readable');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let shouldStop = false;
      let currentMessageContent = '';

      while (!shouldStop) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep partial line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          
          if (trimmed.startsWith('data: ')) {
            let data = trimmed.slice(6);
            data = data.replace(/\\n/g, '\n');
            if (data === '[PIPELINE_COMPLETE]') {
              shouldStop = true;
              break;
            }
            if (data === '[NEXT_MESSAGE]') {
              if (currentMessageContent.trim() && callbacks?.onMessageSplit) {
                callbacks.onMessageSplit(currentMessageContent);
              }
              currentMessageContent = '';
              setContent('');
              continue;
            }
            if (data === '[UPDATE_DASHBOARD]') {
              if (callbacks?.onUpdateDashboard) {
                callbacks.onUpdateDashboard();
              }
              continue;
            }
            if (data.startsWith('[ERROR]')) {
              setError(data.replace('[ERROR]', '').trim() || 'Analysis temporarily unavailable.');
              shouldStop = true;
              break;
            }
            currentMessageContent += data;
            setContent(currentMessageContent);
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Connection lost. Please try again.');
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [reset]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    content,
    isStreaming,
    error,
    startStream,
    reset,
  };
}
