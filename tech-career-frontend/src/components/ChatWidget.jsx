import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Trash2, Loader2 } from 'lucide-react';
import { streamChatResponse, resetChatSession } from '../services/api.js';
import useStore from '../store/useStore';

const ChatWidget = () => {
  const { isChatOpen, setChatOpen, cvText, savedJobs } = useStore();
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! I am your AI Career Assistant. How can I help you today?' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleReset = async () => {
    await resetChatSession();
    setMessages([{ role: 'assistant', content: 'Memory cleared. We can start a new conversation!' }]);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    const userMessage = inputValue;
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
          newMessages[newMessages.length - 1].content += chunk;
          return newMessages;
        });
      });
    } catch (error) {
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].content = "Connection error.";
        return newMessages;
      });
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end lg:w-[350px]">
  {isChatOpen && (
    <div className="w-full h-[450px] mb-4 bg-slate-900/95 backdrop-blur-xl border border-emerald-500/20 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          <div className="flex items-center justify-between p-4 bg-white/5 border-b border-white/10">
            <div className="flex items-center gap-2 text-emerald-400 font-medium">
              <MessageSquare size={20} />
              <span>AI Career Assistant</span>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={handleReset} title="Clear Memory" className="text-gray-400 hover:text-rose-400 transition-colors p-1"><Trash2 size={16} /></button>
              <button onClick={() => setChatOpen(false)} className="text-gray-400 hover:text-white transition-colors p-1"><X size={20} /></button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, index) => (
              <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-2xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-emerald-500 text-slate-950 rounded-tr-sm' : 'bg-slate-800 text-gray-200 border border-white/10 rounded-tl-sm'}`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {isTyping && messages[messages.length - 1].content === '' && (
              <div className="flex justify-start">
                <div className="bg-slate-800 border border-white/10 p-3 rounded-2xl rounded-tl-sm">
                  <Loader2 size={16} className="text-emerald-400 animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-slate-950 border-t border-white/10">
            <div className="relative flex items-center">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask something..."
                className="w-full bg-white/5 border border-white/10 rounded-xl pl-4 pr-12 py-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
              />
              <button onClick={handleSendMessage} disabled={!inputValue.trim() || isTyping} className="absolute right-2 text-emerald-400 hover:text-emerald-300 disabled:text-gray-600 p-2"><Send size={18} /></button>
            </div>
          </div>
        </div>
      )}

      <button onClick={() => setChatOpen(!isChatOpen)} className="w-14 h-14 bg-emerald-500 hover:bg-emerald-400 rounded-full flex items-center justify-center shadow-lg transition-transform duration-300 hover:scale-105">
        {isChatOpen ? <X size={24} className="text-slate-950" /> : <MessageSquare size={24} className="text-slate-950" />}
      </button>
    </div>
  );
};
export default ChatWidget;