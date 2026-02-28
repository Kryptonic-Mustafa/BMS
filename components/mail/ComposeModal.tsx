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

  useEffect(() => {
    if (isOpen && replyTo) {
      setTo([replyTo.email]);
      setSubject(replyTo.subject.startsWith('Re:') ? replyTo.subject : `Re: ${replyTo.subject}`);
      setBody(`\n\n------ Original Message ------\nFrom: ${replyTo.email}\n\n${replyTo.originalBody?.substring(0, 200)}...`);
    } else if (isOpen && !replyTo) {
      setTo([]); setSubject(''); setBody(''); setAttachment(null);
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
        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Sent!', timer: 2000, showConfirmButton: false });
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
      <div className="fixed bottom-0 right-4 md:right-10 w-64 bg-slate-900 text-white p-3 rounded-t-lg shadow-xl cursor-pointer flex justify-between items-center z-50 hover:bg-slate-800 transition" onClick={() => setMinimized(false)}>
        <span className="font-bold text-sm truncate">Draft: {subject || 'New Message'}</span>
        <button onClick={(e) => { e.stopPropagation(); onClose(); }}><X size={16} /></button>
      </div>
    );
  }

  // UPDATED CLASSES: w-full h-full on mobile (inset-0), specific size on desktop
  return (
    <div className="fixed inset-0 md:inset-auto md:bottom-0 md:right-10 z-50 flex flex-col animate-in slide-in-from-bottom-10">
      <div className="w-full h-full md:w-[32rem] md:h-[600px] bg-white shadow-2xl md:rounded-t-xl border border-slate-200 flex flex-col">
        
        {/* Header */}
        <div className="bg-slate-900 text-white p-3 md:rounded-t-xl flex justify-between items-center shrink-0">
          <h3 className="font-bold text-sm">{replyTo ? 'Reply' : 'New Message'}</h3>
          <div className="flex gap-3 text-slate-300">
            <button onClick={() => setMinimized(true)} className="hidden md:block hover:text-white"><Minimize2 size={16}/></button>
            <button onClick={onClose} className="hover:text-white"><X size={20}/></button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 flex flex-col p-2 gap-2 overflow-y-auto">
          <EmailInput selected={to} onChange={setTo} />
          <input 
            className="w-full p-2 border-b border-slate-100 focus:outline-none text-sm font-medium" 
            placeholder="Subject"
            value={subject}
            onChange={e => setSubject(e.target.value)}
          />
          <textarea 
            className="flex-1 p-2 focus:outline-none resize-none text-base md:text-sm font-sans" 
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

        {/* Footer */}
        <div className="p-3 border-t border-slate-100 flex justify-between items-center bg-slate-50 pb-safe">
          <label className="cursor-pointer p-2 hover:bg-slate-200 rounded-full text-slate-600 transition">
            <Paperclip size={24} />
            <input type="file" accept="image/*" className="hidden" onChange={handleFile} />
          </label>
          <button 
            onClick={send} 
            disabled={loading}
            className="bg-blue-900 text-white px-6 py-2 rounded-full font-bold text-sm shadow-md hover:bg-blue-800 transition flex items-center gap-2"
          >
             {loading ? 'Sending...' : <>Send <Send size={16} /></>}
          </button>
        </div>
      </div>
    </div>
  );
}