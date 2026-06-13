import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Leaf, Send, Sparkles, AlertCircle, RefreshCw, User, MessageSquare } from 'lucide-react';
import { useStream } from '../hooks/useStream';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export const ChatInterface: React.FC<{ userId: string }> = ({ userId }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  
  const { content, isStreaming, error, startStream, reset } = useStream();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, content, isStreaming]);

  // Handle auto-triggering analyze from search param
  useEffect(() => {
    if (searchParams.get('analyze') === 'true') {
      // Remove the search param so it doesn't run again on reload
      setSearchParams({}, { replace: true });
      triggerAnalysis();
    }
  }, [searchParams]);

  // Adjust textarea height dynamically
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputText]);

  // Complete streaming response callback
  useEffect(() => {
    if (!isStreaming && content && !error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: content,
          timestamp: new Date(),
        },
      ]);
      reset();
    }
  }, [isStreaming, content, error, reset]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = inputText.trim();
    if (!text || isStreaming) return;

    const userMsg: Message = {
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');

    // Prepare history payload of last 10 messages (matching API schemas)
    const history = messages
      .slice(-10)
      .map((msg) => ({ role: msg.role, content: msg.content }));

    startStream(
      api.chat.streamUrl, 
      {
        user_id: userId,
        message: text,
        history: history,
      },
      {
        onMessageSplit: (msg) => {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: msg, timestamp: new Date() },
          ]);
        },
        onUpdateDashboard: () => {
          queryClient.invalidateQueries({ queryKey: ['activities'] });
          queryClient.invalidateQueries({ queryKey: ['missions'] });
        }
      }
    );
  };

  const triggerAnalysis = () => {
    if (isStreaming) return;

    const userMsg: Message = {
      role: 'user',
      content: 'Analyze my carbon footprint data.',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);

    startStream(
      api.agents.analyzeUrl, 
      {
        user_id: userId,
      },
      {
        onMessageSplit: (msg) => {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: msg, timestamp: new Date() },
          ]);
        },
        onUpdateDashboard: () => {
          queryClient.invalidateQueries({ queryKey: ['activities'] });
          queryClient.invalidateQueries({ queryKey: ['missions'] });
        }
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[650px] bg-slate-950 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden relative">
      <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-slate-700 to-transparent"></div>
      
      {/* Chat Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-600/15 text-emerald-400 rounded-xl border border-emerald-500/10">
            <Sparkles size={18} className="animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">AI Sustainability Coach</h2>
            <p className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
              Online • Gemini Chained Agents
            </p>
          </div>
        </div>

        <button
          onClick={triggerAnalysis}
          disabled={isStreaming}
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 disabled:opacity-50 text-xs font-bold rounded-lg border border-emerald-500/20 transition-all duration-200"
        >
          <Leaf size={12} />
          <span>Full AI Analysis</span>
        </button>
      </div>

      {/* Messages Container */}
      <div
        ref={messagesContainerRef}
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
        className="flex-1 overflow-y-auto px-6 py-6 space-y-4 scrollbar-thin scrollbar-thumb-slate-800"
      >
        {messages.length === 0 && !isStreaming && (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto space-y-4">
            <div className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800 text-emerald-500/70">
              <MessageSquare size={36} />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-200">Start carbon coaching</p>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Ask about reduction tips, diet alternatives, or tap "Full AI Analysis" to audit your monthly footprint.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 max-w-[80%] ${
              msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
            }`}
          >
            {/* Avatar */}
            <div className={`p-2 h-9 w-9 rounded-xl flex items-center justify-center shrink-0 border ${
              msg.role === 'user' 
                ? 'bg-slate-800 border-slate-700 text-slate-300' 
                : 'bg-emerald-950/20 border-emerald-900/20 text-emerald-400'
            }`}>
              {msg.role === 'user' ? <User size={16} /> : <Leaf size={16} />}
            </div>

            {/* Bubble */}
            <div className={`rounded-2xl px-4 py-2.5 text-sm ${
              msg.role === 'user'
                ? 'bg-emerald-600 text-white rounded-tr-none'
                : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none'
            }`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({node, ...props}) => <p className="mb-3 last:mb-0 leading-relaxed whitespace-pre-wrap" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-bold text-emerald-400" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-base font-bold mt-5 mb-2 text-white border-b border-slate-800 pb-1" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />,
                  li: ({node, ...props}) => <li className="pl-1" {...props} />,
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}

        {/* Live streaming message */}
        {isStreaming && content && (
          <div className="flex gap-3 max-w-[80%] mr-auto">
            <div className="p-2 h-9 w-9 rounded-xl flex items-center justify-center shrink-0 border bg-emerald-950/20 border-emerald-900/20 text-emerald-400">
              <Leaf size={16} />
            </div>
            <div className="rounded-2xl px-4 py-2.5 text-sm bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({node, ...props}) => <p className="mb-3 last:mb-0 leading-relaxed whitespace-pre-wrap inline" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-bold text-emerald-400" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-base font-bold mt-5 mb-2 text-white border-b border-slate-800 pb-1" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />,
                  li: ({node, ...props}) => <li className="pl-1" {...props} />,
                }}
              >
                {content}
              </ReactMarkdown>
              <span className="inline-block w-1.5 h-3.5 ml-1 bg-emerald-400 animate-pulse"></span>
            </div>
          </div>
        )}

        {/* Loading placeholder when starting stream */}
        {isStreaming && !content && (
          <div className="flex gap-3 max-w-[80%] mr-auto">
            <div className="p-2 h-9 w-9 rounded-xl flex items-center justify-center shrink-0 border bg-emerald-950/20 border-emerald-900/20 text-emerald-400">
              <Leaf size={16} />
            </div>
            <div className="flex items-center gap-1 rounded-2xl px-4 py-3 bg-slate-900 border border-slate-800 rounded-tl-none">
              <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2.5 p-3.5 bg-red-950/20 border border-red-900/30 text-red-400 rounded-xl text-xs max-w-sm mx-auto">
            <AlertCircle size={16} className="shrink-0" />
            <div className="flex-1 leading-snug">{error}</div>
            <button
              onClick={() => reset()}
              className="p-1 hover:bg-red-900/20 rounded-md transition-colors"
            >
              <RefreshCw size={12} />
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={handleSend}
        className="p-4 border-t border-slate-850 bg-slate-900/30 backdrop-blur-md flex items-end gap-2"
      >
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            placeholder={isStreaming ? 'AI is coaching...' : 'Message to sustainability coach...'}
            aria-label="Message to sustainability coach"
            className="w-full bg-slate-900 border border-slate-800 focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 rounded-xl pl-4 pr-12 py-3 text-sm text-slate-200 placeholder-slate-500 resize-none outline-none transition-colors disabled:opacity-50"
          />
          {inputText.length > 200 && (
            <span className="absolute bottom-2 right-4 text-[10px] font-semibold text-slate-500">
              {inputText.length} chars
            </span>
          )}
        </div>

        <button
          type="submit"
          disabled={!inputText.trim() || isStreaming}
          aria-label="Send message"
          className="p-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:bg-slate-800 text-white rounded-xl shadow-lg transition-all duration-200 active:scale-95 flex items-center justify-center shrink-0 h-[46px] w-[46px]"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};
