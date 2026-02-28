'use client';
import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface EmailInputProps {
  selected: string[];
  onChange: (emails: string[]) => void;
}

export function EmailInput({ selected, onChange }: EmailInputProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);

  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      const res = await fetch(`/api/users/search?q=${query}`);
      setSuggestions(await res.json());
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const addEmail = (email: string) => {
    if (!selected.includes(email)) {
      onChange([...selected, email]);
    }
    setQuery('');
    setSuggestions([]);
  };

  const removeEmail = (email: string) => {
    onChange(selected.filter(e => e !== email));
  };

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-2 p-2 border border-slate-300 rounded-lg bg-white focus-within:ring-2 focus-within:ring-blue-900/20">
        {selected.map(email => (
          <span key={email} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs flex items-center gap-1">
            {email}
            <button onClick={() => removeEmail(email)}><X size={12} /></button>
          </span>
        ))}
        <input 
          className="flex-1 outline-none min-w-[120px] text-sm"
          placeholder={selected.length === 0 ? "To: (Type name...)" : ""}
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
      </div>
      
      {suggestions.length > 0 && (
        <div className="absolute z-50 w-full bg-white border border-slate-200 shadow-lg rounded-lg mt-1 max-h-48 overflow-auto">
          {suggestions.map(user => (
            <div 
              key={user.id} 
              className="p-2 hover:bg-slate-50 cursor-pointer flex flex-col"
              onClick={() => addEmail(user.email)}
            >
              <span className="font-medium text-sm text-slate-900">{user.name}</span>
              <span className="text-xs text-slate-500">{user.email}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}