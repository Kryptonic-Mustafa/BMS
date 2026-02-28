'use client';
import { useState, useEffect } from 'react';
import { Inbox, Send, Search, Paperclip, Reply, ArrowLeft } from 'lucide-react';
import { ComposeModal } from '@/components/mail/ComposeModal';

export default function MailSystem() {
  const [view, setView] = useState('inbox'); 
  const [messages, setMessages] = useState<any[]>([]);
  const [selectedMsg, setSelectedMsg] = useState<any | null>(null);
  const [isComposeOpen, setIsComposeOpen] = useState(false);
  const [replyData, setReplyData] = useState<any>(null);

  const fetchMessages = async (type: string) => {
    try {
      const res = await fetch(`/api/messages?type=${type}`);
      const data = await res.json();
      setMessages(Array.isArray(data) ? data : []);
    } catch (e) {
      setMessages([]);
    }
  };

  useEffect(() => { fetchMessages(view); }, [view]);

  // SMART REPLY HANDLER
  const openCompose = (replyTo?: any) => {
    if (replyTo) {
        setReplyData({ 
            email: view === 'inbox' ? replyTo.sender_email : replyTo.receiver_email,
            subject: replyTo.subject,
            originalBody: replyTo.body // Pass original body for quoting
        });
    } else {
        setReplyData(null);
    }
    setIsComposeOpen(true);
  };

  const getName = (msg: any) => {
    const name = view === 'inbox' ? msg.sender_name : msg.receiver_name;
    return name || 'Unknown User';
  };

  const getInitial = (msg: any) => {
    const name = getName(msg);
    return name.charAt(0).toUpperCase();
  };

  return (
    <div className="h-[85vh] flex bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
      {/* Sidebar */}
      <div className="w-16 md:w-64 bg-slate-50 border-r border-slate-200 flex flex-col py-4">
        <button 
          onClick={() => openCompose()}
          className="mx-2 md:mx-4 mb-6 bg-white border border-slate-200 hover:shadow-md p-3 md:px-4 md:py-3 rounded-xl flex items-center justify-center md:justify-start gap-3 transition text-slate-700"
        >
          <span className="text-2xl md:text-xl text-red-500">+</span> 
          <span className="hidden md:block font-semibold">Compose</span>
        </button>

        <nav className="space-y-1 px-2">
          <button onClick={() => { setView('inbox'); setSelectedMsg(null); }} className={`w-full flex items-center gap-3 p-3 rounded-lg text-sm font-medium ${view === 'inbox' ? 'bg-blue-100 text-blue-900' : 'text-slate-600 hover:bg-slate-200'}`}>
            <Inbox size={18} /> <span className="hidden md:block">Inbox</span>
          </button>
          <button onClick={() => { setView('sent'); setSelectedMsg(null); }} className={`w-full flex items-center gap-3 p-3 rounded-lg text-sm font-medium ${view === 'sent' ? 'bg-blue-100 text-blue-900' : 'text-slate-600 hover:bg-slate-200'}`}>
            <Send size={18} /> <span className="hidden md:block">Sent</span>
          </button>
        </nav>
      </div>

      {/* Message List or Detail View */}
      <div className="flex-1 flex flex-col min-w-0">
        {!selectedMsg ? (
           // LIST VIEW
           <>
             <div className="h-16 border-b border-slate-200 flex items-center px-6">
                <div className="relative w-full max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input className="w-full bg-slate-100 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none" placeholder="Search mail" />
                </div>
             </div>
             <div className="flex-1 overflow-y-auto">
               {messages.map((msg) => (
                 <div key={msg.id} onClick={() => setSelectedMsg(msg)} className={`group px-4 py-3 border-b border-slate-100 hover:bg-slate-50 cursor-pointer flex items-center gap-4 transition ${!msg.is_read && view === 'inbox' ? 'bg-blue-50/50' : ''}`}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold shrink-0 ${view === 'inbox' ? 'bg-indigo-500' : 'bg-teal-500'}`}>
                        {getInitial(msg)}
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-baseline mb-1">
                            <h4 className={`truncate ${!msg.is_read && view === 'inbox' ? 'font-bold text-slate-900' : 'font-semibold text-slate-700'}`}>{getName(msg)}</h4>
                            <span className="text-xs text-slate-400 shrink-0">{new Date(msg.created_at).toLocaleDateString()}</span>
                        </div>
                        <p className={`text-sm truncate ${!msg.is_read && view === 'inbox' ? 'font-bold text-slate-800' : 'font-medium text-slate-600'}`}>{msg.subject || '(No Subject)'}</p>
                        <p className="text-xs text-slate-500 truncate">{msg.body || ''}</p>
                    </div>
                    {msg.attachment && <Paperclip size={16} className="text-slate-400" />}
                 </div>
               ))}
               {messages.length === 0 && <div className="p-10 text-center text-slate-400">Nothing here yet.</div>}
             </div>
           </>
        ) : (
           // DETAIL VIEW
           <div className="flex-1 flex flex-col h-full">
             <div className="h-16 border-b border-slate-200 flex items-center px-4 gap-4">
                <button onClick={() => setSelectedMsg(null)} className="p-2 hover:bg-slate-100 rounded-full"><ArrowLeft size={20} /></button>
                <h3 className="font-bold text-lg truncate flex-1">{selectedMsg.subject || '(No Subject)'}</h3>
             </div>
             <div className="flex-1 p-6 overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center font-bold text-xl">
                            {getInitial(selectedMsg)}
                        </div>
                        <div>
                            <p className="font-bold text-slate-900">{getName(selectedMsg)}</p>
                            <p className="text-xs text-slate-500">&lt;{view === 'inbox' ? (selectedMsg.sender_email || 'unknown') : (selectedMsg.receiver_email || 'unknown')}&gt;</p>
                        </div>
                    </div>
                    <span className="text-sm text-slate-500">{new Date(selectedMsg.created_at).toLocaleString()}</span>
                </div>
                
                <div className="prose text-slate-800 whitespace-pre-wrap mb-8 text-sm md:text-base font-sans leading-relaxed">
                    {selectedMsg.body}
                </div>

                {selectedMsg.attachment && (
                    <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-xl">
                        <p className="text-xs font-bold text-slate-500 uppercase mb-3 flex items-center gap-2">
                            <Paperclip size={14}/> Attachment
                        </p>
                        <img src={selectedMsg.attachment} alt="Attachment" className="max-w-full md:max-w-sm rounded-lg shadow-sm border border-slate-200" />
                    </div>
                )}
             </div>
             <div className="p-4 border-t border-slate-200 bg-slate-50">
                <button 
                  onClick={() => openCompose(selectedMsg)}
                  className="px-6 py-2 border border-slate-300 bg-white rounded-full text-sm font-semibold text-slate-700 hover:bg-slate-100 hover:border-slate-400 transition flex items-center gap-2 w-fit"
                >
                    <Reply size={16} /> Reply
                </button>
             </div>
           </div>
        )}
      </div>

      <ComposeModal 
        isOpen={isComposeOpen} 
        onClose={() => setIsComposeOpen(false)} 
        replyTo={replyData}
      />
    </div>
  );
}