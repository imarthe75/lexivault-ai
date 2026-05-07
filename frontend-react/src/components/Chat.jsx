import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Loader2, Paperclip, MessageSquare } from 'lucide-react';
import axios from '../axiosSetup';

const Message = ({ msg }) => {
  const isBot = msg.role === 'assistant';
  return (
    <div className={`flex gap-4 p-6 ${isBot ? 'bg-primary/5' : 'bg-white'} rounded-3xl animate-fade-in`}>
      <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 ${isBot ? 'bg-primary text-white' : 'bg-slate-100 text-primary'}`}>
        {isBot ? <Bot size={20} /> : <User size={20} />}
      </div>
      <div className="flex flex-col gap-2 flex-1">
        <p className="text-xs font-bold uppercase tracking-wider text-text-muted">
          {isBot ? 'Asistente LexiVault IA' : 'Tú'}
        </p>
        <div className="text-sm prose prose-slate max-w-none">
          {msg.content}
        </div>
        {isBot && msg.sources && (
          <div className="mt-4 pt-4 border-t border-border flex flex-col gap-2">
            <p className="text-[10px] font-bold text-text-muted uppercase">Fuentes Consultadas:</p>
            <div className="flex flex-wrap gap-2">
              {msg.sources.map((source, i) => (
                <div key={i} className="flex items-center gap-2 bg-white px-3 py-1 rounded-full border border-border text-[10px] font-medium text-primary">
                  <Paperclip size={10} /> {source.filename}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const Chat = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hola. Soy el Asistente de LexiVault. Puedo ayudarte a encontrar información dentro de tus documentos almacenados. ¿Qué necesitas saber hoy?' }
  ]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Llamada al endpoint RAG del backend
      const response = await axios.post('/chat/query', { query: input });
      
      const botMessage = { 
        role: 'assistant', 
        content: response.data.answer,
        sources: response.data.sources || []
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Error in chat query", error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Lo siento, ha ocurrido un error al consultar la inteligencia documental. Por favor, intenta de nuevo más tarde.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-180px)]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-2 py-4 flex flex-col gap-4">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && (
          <div className="flex gap-4 p-6 bg-primary/5 rounded-3xl animate-pulse">
            <div className="w-10 h-10 rounded-2xl bg-primary flex items-center justify-center shrink-0">
              <Loader2 className="text-white animate-spin" size={20} />
            </div>
            <div className="flex flex-col gap-2">
              <p className="text-xs font-bold uppercase tracking-wider text-text-muted">Procesando consulta...</p>
              <div className="h-4 w-64 bg-slate-200 rounded"></div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="mt-4 premium-card p-4 flex flex-col gap-4">
        <form onSubmit={handleSend} className="relative">
          <input 
            type="text" 
            placeholder="Escribe tu pregunta sobre los documentos..." 
            className="form-input pr-32 py-4 shadow-sm"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
            <button 
              type="submit" 
              className="btn btn-primary px-6 py-2"
              disabled={loading || !input.trim()}
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
              <span>Consultar</span>
            </button>
          </div>
        </form>
        <div className="flex items-center gap-4 text-[10px] text-text-muted uppercase font-bold tracking-widest px-2">
          <div className="flex items-center gap-1"><Sparkles size={12} className="text-primary" /> RAG Multimodal</div>
          <div className="flex items-center gap-1"><MessageSquare size={12} className="text-primary" /> NVIDIA NIM v1.5</div>
          <div className="flex items-center gap-1 border-l border-border pl-4">Sincronizado con SeaweedFS</div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
