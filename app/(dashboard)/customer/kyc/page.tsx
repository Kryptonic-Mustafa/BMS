'use client';
import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { UploadCloud, ShieldCheck } from 'lucide-react';
import Swal from 'sweetalert2';

export default function KYCPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('National ID');
  const [docNumber, setDocNumber] = useState('');

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return Swal.fire('Error', 'Please upload a document', 'error');

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = async () => {
      const base64 = reader.result;
      const res = await fetch('/api/customer/kyc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentType: docType, documentNumber: docNumber, fileData: base64 }),
      });

      if (res.ok) {
        Swal.fire('Submitted', 'KYC documents uploaded successfully.', 'success');
        setFile(null); setDocNumber('');
      } else {
        Swal.fire('Error', 'Upload failed', 'error');
      }
    };
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        
        {/* LEFT: INFO */}
        <div className="md:col-span-2 space-y-4 flex flex-col justify-center">
            <div>
                <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
                    <ShieldCheck className="text-purple-600"/> Verification
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                    To comply with banking regulations, we need to verify your identity.
                </p>
            </div>
            <ul className="text-xs text-slate-500 dark:text-slate-400 space-y-2 list-disc pl-4">
                <li>Ensure text is readable.</li>
                <li>Upload both sides if required.</li>
                <li>Supported formats: JPG, PNG.</li>
                <li>Max file size: 5MB.</li>
            </ul>
        </div>

        {/* RIGHT: FORM */}
        <Card className="md:col-span-3 p-6 shadow-lg border-slate-200 dark:border-slate-800">
            <form onSubmit={handleUpload} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Doc Type</label>
                        <select 
                            className="w-full p-2 border border-slate-300 rounded-lg bg-white dark:bg-slate-900 dark:border-slate-700 text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                            value={docType} onChange={e => setDocType(e.target.value)}
                        >
                            <option>National ID Card</option>
                            <option>Passport</option>
                            <option>Driving License</option>
                        </select>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Doc Number</label>
                        <Input 
                            placeholder="e.g. A1234..." 
                            value={docNumber} onChange={e => setDocNumber(e.target.value)} 
                            required 
                            className="py-2"
                        />
                    </div>
                </div>

                <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-6 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer group relative">
                    <input 
                        type="file" accept="image/*" 
                        onChange={e => setFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <div className="flex flex-col items-center justify-center">
                        <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-full mb-2 text-purple-600 group-hover:scale-110 transition">
                            <UploadCloud size={24} />
                        </div>
                        {file ? (
                            <p className="font-bold text-green-600 text-sm">{file.name}</p>
                        ) : (
                            <p className="text-sm font-bold text-slate-600 dark:text-slate-300">Click to Upload Image</p>
                        )}
                    </div>
                </div>

                <Button type="submit" className="w-full py-2.5 bg-purple-600 hover:bg-purple-700">
                    Submit Document
                </Button>
            </form>
        </Card>
      </div>
    </div>
  );
}