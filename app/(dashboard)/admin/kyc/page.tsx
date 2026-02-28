'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, X, FileText, History, LayoutList, Clock } from 'lucide-react';
import Swal from 'sweetalert2';
import { Modal } from '@/components/ui/Modal';

export default function AdminKYCPage() {
  const [activeTab, setActiveTab] = useState<'requests' | 'history'>('requests');
  const [requests, setRequests] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState<any>(null);

  const fetchData = async () => {
    const res = await fetch('/api/admin/kyc');
    if (res.ok) {
        const data = await res.json();
        setRequests(data.requests || []);
        setHistory(data.history || []);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAction = async (userId: number, action: 'approve' | 'reject') => {
    let notes = '';
    if (action === 'reject') {
        const { value } = await Swal.fire({ title: 'Reject Reason', input: 'text', showCancelButton: true });
        if (!value) return; 
        notes = value;
    }

    await fetch('/api/admin/kyc', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ userId, action, notes })
    });

    Swal.fire('Success', `User ${action}ed`, 'success');
    fetchData();
    setSelectedDoc(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold dark:text-white">KYC Management</h2>
      </div>

      {/* TABS HEADER */}
      <div className="flex border-b border-slate-200 dark:border-slate-700">
        <button 
            onClick={() => setActiveTab('requests')}
            className={`px-6 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition ${
                activeTab === 'requests' 
                ? 'border-blue-600 text-blue-600' 
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
        >
            <Clock size={16}/> Pending Requests 
            <span className="bg-slate-100 text-slate-600 px-2 rounded-full text-xs">{requests.length}</span>
        </button>
        <button 
            onClick={() => setActiveTab('history')}
            className={`px-6 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition ${
                activeTab === 'history' 
                ? 'border-blue-600 text-blue-600' 
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
        >
            <History size={16}/> Activity Log
        </button>
      </div>

      {/* TAB CONTENT */}
      <div className="pt-4">
        {activeTab === 'requests' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                {requests.map((req: any) => (
                    <Card key={req.id} className="flex flex-col gap-4 border-t-4 border-t-blue-500">
                        <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
                            <div className="bg-blue-100 p-2 rounded-full text-blue-600"><FileText size={20}/></div>
                            <div>
                                <div className="font-bold text-slate-900">{req.name}</div>
                                <div className="text-xs text-slate-500">{req.email}</div>
                            </div>
                        </div>
                        <div className="text-sm space-y-2">
                             <div className="flex justify-between"><span className="text-slate-500">Doc:</span> <span className="font-medium capitalize">{req.document_type}</span></div>
                             <div className="flex justify-between"><span className="text-slate-500">Date:</span> <span>{new Date(req.submitted_at).toLocaleDateString()}</span></div>
                        </div>
                        <Button className="w-full mt-2" onClick={() => setSelectedDoc(req)}>Review Application</Button>
                    </Card>
                ))}
                {requests.length === 0 && (
                    <div className="col-span-3 text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                        <Check size={48} className="mx-auto text-slate-300 mb-2"/>
                        <p className="text-slate-500">All caught up! No pending requests.</p>
                    </div>
                )}
            </div>
        ) : (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                {history.map((log: any) => (
                    <Card key={log.id} className="flex items-center gap-4 p-4">
                        <div className={`p-2 rounded-full ${log.action_type === 'KYC_APPROVE' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                            {log.action_type === 'KYC_APPROVE' ? <Check size={20}/> : <X size={20}/>}
                        </div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-slate-900">
                                {log.actor_name} <span className="text-slate-500 font-normal">marked</span> {log.target_name} <span className="text-slate-500 font-normal">as</span> {log.action_type === 'KYC_APPROVE' ? 'Verified' : 'Rejected'}
                            </p>
                            <p className="text-xs text-slate-400">{new Date(log.created_at).toLocaleString()}</p>
                        </div>
                        {log.details && log.details.includes('Reason:') && (
                            <span className="text-xs bg-slate-100 px-2 py-1 rounded text-slate-500 max-w-xs truncate">
                                {log.details.split('Reason: ')[1]}
                            </span>
                        )}
                    </Card>
                ))}
            </div>
        )}
      </div>

      <Modal isOpen={!!selectedDoc} onClose={() => setSelectedDoc(null)} title="Review Document">
        {selectedDoc && (
            <div className="space-y-6">
                <div className="bg-slate-100 p-4 rounded-lg flex justify-center">
                    <img src={selectedDoc.file_data} className="max-h-[60vh] object-contain shadow-lg rounded" />
                </div>
                <div className="flex justify-end gap-3">
                    <Button variant="danger" onClick={() => handleAction(selectedDoc.user_id, 'reject')}><X size={18} className="mr-2"/> Reject</Button>
                    <Button onClick={() => handleAction(selectedDoc.user_id, 'approve')}><Check size={18} className="mr-2"/> Approve</Button>
                </div>
            </div>
        )}
      </Modal>
    </div>
  );
}