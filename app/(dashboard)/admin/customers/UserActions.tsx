'use client';
import { Button } from '@/components/ui/Button';
import { Trash2, Edit } from 'lucide-react';
import Swal from 'sweetalert2';
import { useRouter } from 'next/navigation';

interface Props {
    user: any;
    permissions: { canEdit: boolean; canDelete: boolean };
}

export default function UserActions({ user, permissions }: Props) {
  const router = useRouter();

  const handleDelete = async () => {
    const res = await Swal.fire({
        title: 'Delete User?',
        text: 'This will delete all their accounts and history!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Yes, Delete'
    });

    if (res.isConfirmed) {
        const apiRes = await fetch(`/api/admin/users?id=${user.id}`, { method: 'DELETE' });
        
        if (apiRes.ok) {
            router.refresh();
            Swal.fire('Deleted', 'User removed', 'success');
        } else {
            const data = await apiRes.json();
            Swal.fire('Permission Denied', data.error, 'error');
        }
    }
  };

  const handleEdit = async () => {
    const { value: formValues } = await Swal.fire({
        title: 'Edit User',
        html:
            `<input id="swal-input1" class="swal2-input" value="${user.name}">` +
            `<input id="swal-input2" class="swal2-input" value="${user.email}">`,
        focusConfirm: false,
        preConfirm: () => [
            (document.getElementById('swal-input1') as HTMLInputElement).value,
            (document.getElementById('swal-input2') as HTMLInputElement).value
        ]
    });

    if (formValues) {
        const apiRes = await fetch('/api/admin/users', {
            method: 'PUT',
            body: JSON.stringify({ id: user.id, name: formValues[0], email: formValues[1] })
        });
        
        if (apiRes.ok) {
            router.refresh();
            Swal.fire('Updated', 'User details updated', 'success');
        } else {
            const data = await apiRes.json();
            Swal.fire('Permission Denied', data.error, 'error');
        }
    }
  };

  return (
    <div className="flex gap-2">
        {permissions.canEdit && (
            <button onClick={handleEdit} className="text-blue-600 hover:bg-blue-50 p-2 rounded" title="Edit">
                <Edit size={16}/>
            </button>
        )}
        {permissions.canDelete && (
            <button onClick={handleDelete} className="text-red-600 hover:bg-red-50 p-2 rounded" title="Delete">
                <Trash2 size={16}/>
            </button>
        )}
    </div>
  );
}