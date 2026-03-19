import React, { useEffect, useState } from 'react';
import { usersAPI, authAPI } from '../api/axiosClient.js';
import { auditAPI } from '../api/axiosClient.js';
import toast from 'react-hot-toast';

export default function AdminPage() {
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('users');
  const [form, setForm] = useState({ username: '', email: '', password: '', role: 'user' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const loadUsers = async () => { const r = await usersAPI.list(); setUsers(r.data); };
  const loadAudit = async () => { const r = await auditAPI.list(); setAuditLogs(r.data); };

  useEffect(() => { loadUsers(); loadAudit(); }, []);

  const addUser = async (e) => {
    e.preventDefault();
    if (!form.username || !form.email || !form.password) { toast.error('All fields required'); return; }
    try {
      await authAPI.register ? authAPI.register(form) : null;
      // Using register endpoint
      const { default: axios } = await import('../api/axiosClient.js');
      toast.success('User created!');
      setForm({ username: '', email: '', password: '', role: 'user' });
      loadUsers();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
  };

  const deleteUser = async (id) => {
    if (!confirm(`Delete user #${id}?`)) return;
    try { await usersAPI.delete(id); toast.success('Deleted'); loadUsers(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
  };

  const toggleActive = async (user) => {
    try {
      await usersAPI.update(user.id, { is_active: !user.is_active });
      toast.success(`User ${user.is_active ? 'deactivated' : 'activated'}`);
      loadUsers();
    } catch (err) { toast.error('Failed'); }
  };

  const tabStyle = (t) => ({
    padding: '9px 20px', border: 'none', cursor: 'pointer', borderRadius: 7,
    fontWeight: 600, fontSize: 13,
    background: activeTab === t ? 'var(--accent)' : 'var(--bg-card)',
    color: activeTab === t ? 'white' : 'var(--text-muted)',
    borderBottom: activeTab === t ? 'none' : '1px solid var(--border)',
  });

  return (
    <div className="fade-in">
      <h1 className="page-title">⚙️ Admin Panel</h1>
      <div className="flex gap-2 mb-4">
        <button style={tabStyle('users')} onClick={() => setActiveTab('users')}>👥 Users ({users.length})</button>
        <button style={tabStyle('audit')} onClick={() => setActiveTab('audit')}>📋 Audit Logs ({auditLogs.length})</button>
      </div>

      {activeTab === 'users' && (
        <>
          <div className="card mb-4">
            <div className="card-header">Create New User</div>
            <form onSubmit={addUser}>
              <div className="form-grid mb-3">
                <div className="form-group">
                  <label className="form-label">Username *</label>
                  <input className="form-input" value={form.username} onChange={e => set('username', e.target.value)} placeholder="username" />
                </div>
                <div className="form-group">
                  <label className="form-label">Email *</label>
                  <input className="form-input" type="email" value={form.email} onChange={e => set('email', e.target.value)} placeholder="user@example.com" />
                </div>
                <div className="form-group">
                  <label className="form-label">Password *</label>
                  <input className="form-input" type="password" value={form.password} onChange={e => set('password', e.target.value)} placeholder="Min 8 chars" />
                </div>
                <div className="form-group">
                  <label className="form-label">Role</label>
                  <select className="form-select" value={form.role} onChange={e => set('role', e.target.value)}>
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="flex-end">
                <button type="submit" className="btn btn-primary">+ Create User</button>
              </div>
            </form>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td className="text-muted">{u.id}</td>
                    <td style={{ fontWeight: 600 }}>{u.username}</td>
                    <td className="text-muted">{u.email}</td>
                    <td><span className={`badge ${u.role === 'admin' ? 'badge-blue' : 'badge-green'}`}>{u.role}</span></td>
                    <td><span className={`badge ${u.is_active ? 'badge-green' : 'badge-red'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td className="text-muted">{u.created_at?.slice(0, 10)}</td>
                    <td className="flex gap-2">
                      <button className="btn btn-ghost btn-sm" onClick={() => toggleActive(u)}>
                        {u.is_active ? '⏸ Deactivate' : '▶ Activate'}
                      </button>
                      <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
                        onClick={() => deleteUser(u.id)}>🗑</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {activeTab === 'audit' && (
        <div className="table-container">
          <table className="data-table">
            <thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Resource</th><th>IP</th></tr></thead>
            <tbody>
              {auditLogs.map(log => (
                <tr key={log.id}>
                  <td className="text-muted">{log.timestamp?.slice(0, 19)}</td>
                  <td>{log.user_id || '—'}</td>
                  <td><span className="badge badge-blue">{log.action}</span></td>
                  <td>{log.resource}</td>
                  <td className="text-muted">{log.ip_address || '—'}</td>
                </tr>
              ))}
              {auditLogs.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>No audit logs yet.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
