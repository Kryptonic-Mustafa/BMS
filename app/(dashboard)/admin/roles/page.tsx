'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Edit, Trash2, Plus } from 'lucide-react';
import Swal from 'sweetalert2';

export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [allPermissions, setAllPermissions] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<any>(null);
  
  // Form State
  const [formData, setFormData] = useState({ name: '', description: '', permissions: [] as string[] });

  const fetchData = async () => {
    const [rolesRes, permsRes] = await Promise.all([
        fetch('/api/admin/roles'),
        fetch('/api/admin/permissions/list')
    ]);
    if (rolesRes.ok) setRoles(await rolesRes.json());
    if (permsRes.ok) setAllPermissions(await permsRes.json());
  };

  useEffect(() => { fetchData(); }, []);

  const openModal = (role?: any) => {
    if (role) {
        setEditingRole(role);
        setFormData({ 
            name: role.name, 
            description: role.description, 
            permissions: role.permissions || [] 
        });
    } else {
        setEditingRole(null);
        setFormData({ name: '', description: '', permissions: [] });
    }
    setIsModalOpen(true);
  };

  const togglePerm = (permName: string) => {
    setFormData(prev => {
        const exists = prev.permissions.includes(permName);
        return {
            ...prev,
            permissions: exists 
                ? prev.permissions.filter(p => p !== permName)
                : [...prev.permissions, permName]
        };
    });
  };

  const handleSave = async () => {
    // 1. CREATE ROLE (No Confirmation needed)
    if (!editingRole) {
        await fetch('/api/admin/roles', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        setIsModalOpen(false);
        fetchData();
        Swal.fire({
            title: 'Created!',
            text: 'New role has been added.',
            icon: 'success',
            timer: 1500,
            showConfirmButton: false
        });
        return;
    }

    // 2. UPDATE ROLE (Smart Confirmation)
    const oldPerms = editingRole.permissions || [];
    const newPerms = formData.permissions;

    // Calculate diffs
    const added = newPerms.filter((p: string) => !oldPerms.includes(p));
    const removed = oldPerms.filter((p: string) => !newPerms.includes(p));
    const isNameChanged = formData.name !== editingRole.name || formData.description !== editingRole.description;

    // If nothing changed, just close
    if (added.length === 0 && removed.length === 0 && !isNameChanged) {
        setIsModalOpen(false);
        return;
    }

    // Build the confirmation message
    let htmlContent = '<div class="text-left text-sm space-y-2">';
    
    if (isNameChanged) {
        htmlContent += `<p class="text-slate-600">Updating role details.</p>`;
    }

    if (added.length > 0) {
        htmlContent += `
            <div class="p-2 bg-green-50 border border-green-200 rounded">
                <strong class="text-green-700 block mb-1">Adding Permissions:</strong>
                <span class="text-green-800">${added.join(', ')}</span>
            </div>`;
    }

    if (removed.length > 0) {
        htmlContent += `
            <div class="p-2 bg-red-50 border border-red-200 rounded">
                <strong class="text-red-700 block mb-1">Removing Permissions:</strong>
                <span class="text-red-800">${removed.join(', ')}</span>
            </div>`;
    }
    htmlContent += '</div>';

    // Show Confirmation
    const result = await Swal.fire({
        title: 'Confirm Changes?',
        html: htmlContent,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#1E3A8A',
        cancelButtonColor: '#64748B',
        confirmButtonText: 'Yes, Update Role'
    });

    if (!result.isConfirmed) return;

    // Proceed with Update
    await fetch('/api/admin/roles', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ...formData, id: editingRole.id })
    });

    setIsModalOpen(false);
    fetchData();
    
    Swal.fire({
        title: 'Updated!',
        text: 'Role permissions successfully modified.',
        icon: 'success',
        timer: 1500,
        showConfirmButton: false
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold dark:text-white">Roles Management</h2>
        <Button onClick={() => openModal()}><Plus size={18} className="mr-2"/> Add Role</Button>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl shadow border border-slate-200 dark:border-slate-700 overflow-hidden">
        <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 dark:bg-slate-800 text-slate-500 font-bold uppercase">
                <tr>
                    <th className="px-6 py-4">Role</th>
                    <th className="px-6 py-4">Description</th>
                    <th className="px-6 py-4">Permissions</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                </tr>
            </thead>
            <tbody>
                {roles.map((role: any) => (
                    <tr key={role.id} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="px-6 py-4 font-bold dark:text-white">{role.name}</td>
                        <td className="px-6 py-4 text-slate-500">{role.description}</td>
                        <td className="px-6 py-4">
                            <div className="flex flex-wrap gap-1">
                                {role.permissions.slice(0, 5).map((p: string) => (
                                    <span key={p} className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">{p}</span>
                                ))}
                                {role.permissions.length > 5 && <span className="text-xs text-slate-400">+{role.permissions.length - 5} more</span>}
                            </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                            <button onClick={() => openModal(role)} className="p-2 text-blue-600 hover:bg-blue-50 rounded"><Edit size={16}/></button>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
      </div>

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingRole ? 'Edit Role' : 'Add New Role'}>
        <div className="space-y-4 max-h-[70vh] overflow-y-auto">
            <div className="grid grid-cols-2 gap-4">
                <Input label="Role Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                <Input label="Description" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
            </div>
            
            <div>
                <label className="block text-sm font-medium mb-2 dark:text-slate-300">Permissions</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 border border-slate-200 dark:border-slate-700 p-4 rounded-lg bg-slate-50 dark:bg-slate-800">
                    {allPermissions.map((p: any) => (
                        <label key={p.id} className="flex items-center gap-2 cursor-pointer p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition">
                            <input 
                                type="checkbox" 
                                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                                checked={formData.permissions.includes(p.name)}
                                onChange={() => togglePerm(p.name)}
                            />
                            <span className="text-sm dark:text-slate-300">{p.name}</span>
                        </label>
                    ))}
                </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
                <Button variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button onClick={handleSave}>{editingRole ? 'Update Role' : 'Create Role'}</Button>
            </div>
        </div>
      </Modal>
    </div>
  );
}