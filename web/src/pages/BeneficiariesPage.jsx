import React, { useEffect, useState } from 'react';
import { beneficiariesAPI } from '../api/axiosClient.js';
import toast from 'react-hot-toast';

export default function BeneficiariesPage() {
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [search, setSearch] = useState('');
  const [form, setForm] = useState({ name: '', mobile_number: '', bank_name: '', account_number: '', ifsc_code: '' });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const load = async () => { const r = await beneficiariesAPI.list(); setBeneficiaries(r.data); };
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name) { toast.error('Name is required'); return; }
    try {
      await beneficiariesAPI.create(form);
      toast.success('Beneficiary added!');
      setForm({ name: '', mobile_number: '', bank_name: '', account_number: '', ifsc_code: '' });
      load();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
  };

  const deleteBen = async (id) => {
    if (!confirm('Delete this beneficiary?')) return;
    await beneficiariesAPI.delete(id);
    toast.success('Deleted');
    load();
  };

  const filtered = beneficiaries.filter(b =>
    !search ||
    b.name.toLowerCase().includes(search.toLowerCase()) ||
    (b.mobile_number || '').includes(search) ||
    (b.bank_name || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="fade-in">
      <h1 className="page-title">👤 Beneficiaries</h1>

      {/* ── Add Form ──────────────────────────────────────────────────────── */}
      <div className="card mb-4">
        <div className="card-header">
          Add New Beneficiary&nbsp;
          <span style={{ color: 'var(--text-muted)', fontSize: 11, fontWeight: 400 }}>🔒 PII encrypted at rest</span>
        </div>
        <form onSubmit={submit}>
          <div className="form-grid mb-3">

            {/* Row 1 */}
            <div className="form-group">
              <label className="form-label">Full Name *</label>
              <input className="form-input" placeholder="Beneficiary name" value={form.name}
                onChange={e => set('name', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Mobile Number 🔒</label>
              <input className="form-input" placeholder="+91-XXXXXXXXXX" value={form.mobile_number}
                onChange={e => set('mobile_number', e.target.value)} />
            </div>

            {/* Row 2 */}
            <div className="form-group">
              <label className="form-label">Bank Name</label>
              <input className="form-input" placeholder="e.g. SBI" value={form.bank_name}
                onChange={e => set('bank_name', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Account Number 🔒</label>
              <input className="form-input" placeholder="Account (encrypted)" value={form.account_number}
                onChange={e => set('account_number', e.target.value)} />
            </div>

            {/* Row 3 — IFSC optional */}
            <div className="form-group">
              <label className="form-label">IFSC Code <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
              <input className="form-input" placeholder="SBIN0000XXX" value={form.ifsc_code}
                onChange={e => set('ifsc_code', e.target.value)} />
            </div>

          </div>
          <div className="flex-end">
            <button id="add-beneficiary-btn" type="submit" className="btn btn-primary">+ Add Beneficiary</button>
          </div>
        </form>
      </div>

      {/* ── Search Bar ─────────────────────────────────────────────────────── */}
      <div className="filter-bar mb-3">
        <input
          className="form-input"
          style={{ maxWidth: 360 }}
          placeholder="🔍 Search by name, mobile, or bank…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <span className="text-muted" style={{ fontSize: 12 }}>{filtered.length} of {beneficiaries.length} shown</span>
        {search && (
          <button className="btn btn-ghost btn-sm" onClick={() => setSearch('')}>✕ Clear</button>
        )}
      </div>

      {/* ── Table ─────────────────────────────────────────────────────────── */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th><th>Name</th><th>Mobile</th><th>Bank</th><th>Account</th><th>IFSC</th><th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(b => (
              <tr key={b.id}>
                <td className="text-muted">{b.id}</td>
                <td style={{ fontWeight: 600 }}>{b.name}</td>
                <td>{b.mobile_number || '—'}</td>
                <td>{b.bank_name || '—'}</td>
                <td className="text-muted">{b.account_number || '—'}</td>
                <td className="text-muted">{b.ifsc_code || '—'}</td>
                <td>
                  <button className="btn btn-ghost btn-sm"
                    style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
                    onClick={() => deleteBen(b.id)}>🗑</button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>
                {search ? `No beneficiaries match "${search}"` : 'No beneficiaries added yet.'}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
