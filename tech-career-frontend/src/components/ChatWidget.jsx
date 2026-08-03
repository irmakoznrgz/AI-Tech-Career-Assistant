import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Trash2, Loader2, Sparkles } from 'lucide-react';
import { streamChatResponse, resetChatSession } from '../services/api.js';
import useStore from '../store/useStore';

const ChatWidget = () => {
  const { isChatOpen, setChatOpen, cvText, savedJobs } = useStore();
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! I am your AI Career Assistant. How can I help you?' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]); 

  const handleReset = async () => {
    await resetChatSession();
    setMessages([{ role: 'assistant', content: 'Memory cleared. We can start a new conversation!' }]);
  };

  const triggerSendMessage = async (textToSend) => {
    if (!textToSend.trim() || isTyping) return;
    const userMessage = textToSend;
    setInputValue('');
    
    setMessages((prev) => [
      ...prev, 
      { role: 'user', content: userMessage },
      { role: 'assistant', content: '' }
    ]);
    setIsTyping(true);

    try {
      await streamChatResponse(userMessage, savedJobs, cvText, (chunk) => {
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastIndex = newMessages.length - 1;
          
          newMessages[lastIndex] = {
            ...newMessages[lastIndex],
            content: newMessages[lastIndex].content + chunk
          };
          
          return newMessages;
        });
      });
    } catch (error) {
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastIndex = newMessages.length - 1;
        newMessages[lastIndex] = {
            ...newMessages[lastIndex],
            content: "Connection error."
        };
        return newMessages;
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleSendMessage = () => {
    triggerSendMessage(inputValue);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end w-[90%] sm:w-[450px]">
      {isChatOpen ? (
        <div className="w-full max-h-[65vh] h-[550px] mb-4 bg-slate-900/95 backdrop-blur-xl border border-emerald-500/30 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          <div className="flex items-center justify-between p-4 bg-slate-950 border-b border-white/10 shrink-0">
            <div className="flex items-center gap-2 text-emerald-400 font-medium">
              <MessageSquare size={20} />
              <span>AI Career Assistant</span>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={handleReset} title="Clear Memory" className="text-gray-400 hover:text-rose-400 transition-colors p-1"><Trash2 size={18} /></button>
              <button onClick={() => setChatOpen(false)} title="Close Chat" className="text-gray-400 hover:text-white transition-colors p-1"><X size={24} /></button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-slate-900">
            {messages.map((msg, index) => (
              <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[90%] p-4 rounded-2xl text-[15px] leading-relaxed whitespace-pre-wrap break-words ${msg.role === 'user' ? 'bg-emerald-500 text-slate-950 rounded-tr-sm font-medium' : 'bg-slate-800 text-gray-200 border border-white/10 rounded-tl-sm'}`}>
                  {msg.content}
                </div>
              </div>
            ))}

            {messages.length === 1 && (
              <div className="flex flex-col gap-2 pt-2">
                <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium px-1">
                  <Sparkles size={14} />
                  <span>Suggested Quick Prompts:</span>
                </div>
                
                <button
                  onClick={() => triggerSendMessage("Could you please evaluate my resume and recommend matching career opportunities based on my profile?")}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-gray-300 hover:text-emerald-400 border border-white/10 rounded-xl p-3 text-left transition-all cursor-pointer flex items-center justify-between group"
                >
                  <span>📄 Evaluate resume & recommend matching roles</span>
                  <span className="text-emerald-400 group-hover:translate-x-1 transition-transform">→</span>
                </button>

                <button
                  onClick={() => triggerSendMessage("What strategic enhancements can I make to my resume to increase its impact and visibility to recruiters?")}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-gray-300 hover:text-emerald-400 border border-white/10 rounded-xl p-3 text-left transition-all cursor-pointer flex items-center justify-between group"
                >
                  <span>✨ Optimize resume to stand out to recruiters</span>
                  <span className="text-emerald-400 group-hover:translate-x-1 transition-transform">→</span>
                </button>

                <button
                  onClick={() => triggerSendMessage("I would like to conduct a mock technical interview session to refine my responses.")}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-gray-300 hover:text-emerald-400 border border-white/10 rounded-xl p-3 text-left transition-all cursor-pointer flex items-center justify-between group"
                >
                  <span>🎤 Run a mock technical interview session</span>
                  <span className="text-emerald-400 group-hover:translate-x-1 transition-transform">→</span>
                </button>
              </div>
            )}

            {isTyping && messages[messages.length - 1].content === '' && (
              <div className="flex justify-start">
                <div className="bg-slate-800 border border-white/10 p-3 rounded-2xl rounded-tl-sm">
                  <Loader2 size={16} className="text-emerald-400 animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-slate-950 border-t border-white/10 shrink-0">
            <div className="relative flex items-center">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask something..."
                className="w-full bg-white/5 border border-white/10 rounded-xl pl-4 pr-12 py-4 text-[15px] text-white focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
              />
              <button onClick={handleSendMessage} disabled={!inputValue.trim() || isTyping} className="absolute right-2 text-emerald-400 hover:text-emerald-300 disabled:text-gray-600 p-2"><Send size={20} /></button>
            </div>
          </div>
        </div>
      ) : (
        <button onClick={() => setChatOpen(true)} className="w-16 h-16 bg-emerald-500 hover:bg-emerald-400 rounded-full flex items-center justify-center shadow-lg transition-transform duration-300 hover:scale-105 shrink-0">
          <MessageSquare size={28} className="text-slate-950" />
        </button>
      )}
    </div>
  );
};

export default ChatWidget;