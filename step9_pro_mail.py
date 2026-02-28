import os

files = {
    # --- 1. UPGRADED COMPOSE MODAL (Handles Smart Reply) ---
    "components/mail/ComposeModal.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { X, Minimize2, Paperclip, Send } from 'lucide-react';
import { EmailInput } from '@/components/ui/EmailInput';
import Swal from 'sweetalert2';

interface ComposeModalProps {
  isOpen: boolean;
  onClose: () => void;
  replyTo?: { email: string; subject: string; originalBody?: string } | null;
}

export function ComposeModal({ isOpen, onClose, replyTo }: ComposeModalProps) {
  const [to, setTo] = useState<string[]>([]);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [attachment, setAttachment] = useState<string | null>(null);
  const [minimized, setMinimized] = useState(false);
  const [loading, setLoading] = useState(false);

  // Reset or Initialize state when modal opens
  useEffect(() => {
    if (isOpen && replyTo) {
      setTo([replyTo.email]); // Pre-fill recipient as a tag
      setSubject(replyTo.subject.startsWith('Re:') ? replyTo.subject : `Re: ${replyTo.subject}`);
      // Quote the original message
      setBody(`\\n\\n------ Original Message ------\\nFrom: ${replyTo.email}\\n\\n${replyTo.originalBody?.substring(0, 200)}...`);
    } else if (isOpen && !replyTo) {
      // Clear for new blank message
      setTo([]);
      setSubject('');
      setBody('');
      setAttachment(null);
    }
  }, [isOpen, replyTo]);

  if (!isOpen) return null;

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) { 
        Swal.fire('Error', 'File too large (Max 2MB)', 'error');
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => setAttachment(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const send = async () => {
    if (to.length === 0) return Swal.fire('Error', 'Add a recipient', 'warning');
    setLoading(true);
    
    try {
      const res = await fetch('/api/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ to, subject, body, attachment })
      });
      
      if (res.ok) {
        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Message Sent!', timer: 2000, showConfirmButton: false });
        onClose();
      }
    } catch (e) {
      Swal.fire('Error', 'Failed to send', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (minimized) {
    return (
      <div className="fixed bottom-0 right-10 w-64 bg-slate-900 text-white p-3 rounded-t-lg shadow-xl cursor-pointer flex justify-between items-center z-50 hover:bg-slate-800 transition" onClick={() => setMinimized(false)}>
        <span className="font-bold text-sm truncate">Draft: {subject || 'New Message'}</span>
        <button onClick={(e) => { e.stopPropagation(); onClose(); }}><X size={16} /></button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-0 right-4 md:right-10 w-96 md:w-[32rem] bg-white shadow-2xl rounded-t-xl border border-slate-200 z-50 flex flex-col h-[600px] animate-in slide-in-from-bottom-10">
      <div className="bg-slate-900 text-white p-3 rounded-t-xl flex justify-between items-center shrink-0">
        <h3 className="font-bold text-sm">{replyTo ? 'Reply' : 'New Message'}</h3>
        <div className="flex gap-3 text-slate-300">
          <button onClick={() => setMinimized(true)} className="hover:text-white"><Minimize2 size={16}/></button>
          <button onClick={onClose} className="hover:text-white"><X size={16}/></button>
        </div>
      </div>

      <div className="flex-1 flex flex-col p-2 gap-2 overflow-y-auto">
        <EmailInput selected={to} onChange={setTo} />
        <input 
          className="w-full p-2 border-b border-slate-100 focus:outline-none text-sm font-medium" 
          placeholder="Subject"
          value={subject}
          onChange={e => setSubject(e.target.value)}
        />
        <textarea 
          className="flex-1 p-2 focus:outline-none resize-none text-sm font-sans" 
          placeholder="Type your message..."
          value={body}
          onChange={e => setBody(e.target.value)}
          autoFocus={!replyTo}
        />
        
        {attachment && (
            <div className="bg-slate-50 p-2 rounded flex justify-between items-center border border-slate-200">
                <span className="text-xs text-slate-500 truncate max-w-[200px]">Attachment Ready</span>
                <button onClick={() => setAttachment(null)} className="text-red-500"><X size={14}/></button>
            </div>
        )}
      </div>

      <div className="p-3 border-t border-slate-100 flex justify-between items-center bg-slate-50">
        <label className="cursor-pointer p-2 hover:bg-slate-200 rounded-full text-slate-600 transition">
          <Paperclip size={20} />
          <input type="file" accept="image/*" className="hidden" onChange={handleFile} />
        </label>
        <button 
          onClick={send} 
          disabled={loading}
          className="bg-blue-900 text-white px-6 py-2 rounded-full font-bold text-sm shadow-md hover:bg-blue-800 transition flex items-center gap-2"
        >
           {loading ? 'Sending...' : <>Send <Send size={14} /></>}
        </button>
      </div>
    </div>
  );
}
""",

    # --- 2. ENHANCED NOTIFICATION LISTENER (Aggressive Polling for Mail) ---
    "components/layout/NotificationListener.tsx": """
'use client';
import { useEffect, useRef } from 'react';
import Swal from 'sweetalert2';
import { useRouter } from 'next/navigation';

export function NotificationListener() {
  const router = useRouter();
  const lastIdRef = useRef<number>(0);

  useEffect(() => {
    const checkNotifications = async () => {
      try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        
        // Filter for unread
        const unread = data.filter((n: any) => !n.is_read);

        if (unread.length > 0) {
          const latest = unread[0];
          
          // Only show toast if it's a NEW notification we haven't seen in this session
          if (latest.id > lastIdRef.current) {
            lastIdRef.current = latest.id;
            
            const isMail = latest.message.includes('New Message');

            const Toast = Swal.mixin({
              toast: true,
              position: 'top-end',
              showConfirmButton: false,
              timer: 5000,
              timerProgressBar: true,
              didOpen: (toast) => {
                toast.addEventListener('click', () => {
                   if (isMail) router.push('/messages'); // Click to go to mail
                });
              }
            });

            Toast.fire({
              icon: isMail ? 'info' : latest.type,
              title: isMail ? '📧 New Email Received' : latest.message,
              text: isMail ? latest.message : ''
            });

            // Mark as read immediately
            await fetch('/api/notifications', { method: 'PUT' });
          }
        }
      } catch (error) {
        // silent fail
      }
    };

    // Poll frequently (every 3 seconds) for that "Instant" feel
    const interval = setInterval(checkNotifications, 3000);
    return () => clearInterval(interval);
  }, [router]);

  return null;
}
""",

    # --- 3. FIX MAIL PAGE (Pass Data to Reply) ---
    "app/(dashboard)/messages/page.tsx": """
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
"""
}

def pro_upgrade():
    print("🚀 Installing Pro Mail Features (Smart Reply & Instant Alerts)...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✨ Done! Mail System is now Professional Grade.")

if __name__ == "__main__":
    pro_upgrade()