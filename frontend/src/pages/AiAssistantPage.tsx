/**
 * @file AiAssistantPage.tsx
 * @description Enterprise AI Assistant chat interface with tool execution indicator and role starter questions.
 *
 * SPECIFICATION (PROJECT.md section 12 & FARHAN_GUIDE.txt Task F12):
 * - Invokes `POST /ai/chat { message, history }`.
 * - Backend executes Groq tool calling loop with caller's role scope.
 * - Displays tool execution pill (e.g. `get_headcount()`, `get_late_comers()`).
 * - All assistant answers show the mandatory "AI-generated" tag.
 * - Handles rate limits (HTTP 429) and timeouts gracefully with friendly fallbacks.
 * - Provides 3 starter questions tailored to the active user role.
 */

import React, { useState } from 'react';
import { api, ApiError } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { AiBadge } from '@/components/ui/AiBadge';
import { Bot, Send, Sparkles, User, Wrench } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  toolUsed?: string;
}

export function AiAssistantPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Hello ${user?.full_name || 'there'}! I am your enterprise HCM AI assistant. I have direct scoped access to company analytics, headcount, attendance logs, and leave quotas. How can I help you today?`,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  /**
   * Starter suggestions from PROJECT.md section 14 (Demo script questions).
   */
  const starterQuestions = React.useMemo(() => {
    if (user?.role === 'admin') {
      return [
        'How many active employees are in the company?',
        'Who came late most often this month?',
        'What is this month’s attendance rate?',
      ];
    }
    if (user?.role === 'hr') {
      return [
        'How many active employees do we have?',
        'Who came late most often this month?',
        'What is the overall attendance rate?',
      ];
    }
    // Employee questions (including privacy refusal test question)
    return [
      'How many sick leaves do I have left?',
      'What is my attendance rate this month?',
      "What is Zeeshan's salary?",
    ];
  }, [user?.role]);

  /**
   * Sends user query to `POST /ai/chat` and formats response.
   */
  const handleSend = async (textToSend?: string) => {
    const q = (textToSend || input).trim();
    if (!q || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: q,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post<{ answer: string; tool_used?: string }>('/ai/chat', {
        message: q,
      });

      const botMsg: ChatMessage = {
        id: `b-${Date.now()}`,
        sender: 'assistant',
        text: res.answer,
        toolUsed: res.tool_used,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      let errText = "I encountered an error querying live data. Please try again in a moment.";
      if (err instanceof ApiError && err.status === 429) {
        errText = "Rate limit reached (20 requests/hour limit). Please wait a short while.";
      }
      setMessages((prev) => [
        ...prev,
        {
          id: `b-err-${Date.now()}`,
          sender: 'assistant',
          text: errText,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto flex flex-col h-[calc(100vh-120px)]">
      <PageHeader
        title="Enterprise AI Assistant"
        description="Truthful responses generated exclusively through live scoped backend tool execution."
        action={<AiBadge />}
      />

      {/* Suggested Starter Questions */}
      <div className="flex flex-wrap gap-2">
        <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
          <Sparkles className="h-3 w-3 text-purple-600" />
          Suggested:
        </span>
        {starterQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="text-xs px-2.5 py-1 rounded bg-surface hover:bg-muted text-foreground border border-border transition-colors text-left"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <Card className="flex-1 overflow-y-auto p-4 space-y-4 bg-surface/30">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.sender === 'assistant' && (
              <div className="h-8 w-8 rounded bg-purple-600 text-white flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-lg p-3.5 text-xs leading-relaxed space-y-2 ${
                m.sender === 'user'
                  ? 'bg-accent text-accent-foreground font-medium'
                  : 'bg-surface-elevated border border-border text-foreground shadow-sm'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-semibold text-[11px] opacity-70">
                  {m.sender === 'user' ? 'You' : 'HCM AI Assistant'}
                </span>
                {m.sender === 'assistant' && <AiBadge />}
              </div>
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.toolUsed && (
                <div className="pt-2 border-t border-border/50 text-[10px] text-muted-foreground flex items-center gap-1 font-mono">
                  <Wrench className="h-3 w-3 text-purple-500" />
                  Tool executed: {m.toolUsed}()
                </div>
              )}
            </div>
            {m.sender === 'user' && (
              <div className="h-8 w-8 rounded bg-muted text-foreground flex items-center justify-center shrink-0 border border-border">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="h-8 w-8 rounded bg-purple-600 text-white flex items-center justify-center shrink-0 animate-pulse">
              <Bot className="h-4 w-4" />
            </div>
            <div className="p-3 bg-surface-elevated border border-border rounded-lg text-xs text-muted-foreground flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-purple-500 animate-ping" />
              Executing scoped tool & formulating answer...
            </div>
          </div>
        )}
      </Card>

      {/* Message Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-2"
      >
        <Input
          placeholder="Ask a question about headcount, attendance, or policy..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1"
          disabled={loading}
        />
        <Button type="submit" loading={loading} className="gap-2 shrink-0">
          <Send className="h-4 w-4" />
          Send
        </Button>
      </form>
    </div>
  );
}
