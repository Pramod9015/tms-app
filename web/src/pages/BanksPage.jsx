import React, { useEffect, useState, useRef } from 'react';
import { banksAPI } from '../api/axiosClient.js';
import axiosClient from '../api/axiosClient.js';
import toast from 'react-hot-toast';

// ── API helpers for import endpoints ─────────────────────────────────────────
const importAPI = {
  getDefaults: () => axiosClient.get('/banks/defaults'),
  importList: (names) => axiosClient.post('/banks/import/list', { bank_names: names }),
  importTxt: (formData) => axiosClient.post('/banks/import/txt', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  importExcel: (formData) => axiosClient.post('/banks/import/excel', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};

// ── Default-bank Picker Modal ─────────────────────────────────────────────────
function DefaultBankModal({ onClose, onImported }) {
  const [all, setAll] = useState([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(new Set());
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    importAPI.getDefaults().then(r => {
      setAll(r.data);
      setSelected(new Set(r.data));
    });
  }, []);

  const filtered = all.filter(b => b.toLowerCase().includes(search.toLowerCase()));
  const allFilteredSelected = filtered.every(b => selected.has(b));

  const toggle = (name) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  const toggleAll = () => {
    if (allFilteredSelected) {
      setSelected(prev => { const next = new Set(prev); filtered.forEach(b => next.delete(b)); return next; });
    } else {
      setSelected(prev => { const next = new Set(prev); filtered.forEach(b => next.add(b)); return next; });
    }
  };

  const doImport = async () => {
    const names = [...selected];
    if (!names.length) { toast.error('No banks selected'); return; }
    setImporting(true);
    try {
      const r = await importAPI.importList(names);
      const { added, skipped } = r.data;
      toast.success(`✅ Added ${added} | ⏭ Skipped ${skipped} (already existed)`);
      onImported();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Import failed');
    } finally { setImporting(false); }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 540, width: '90%', maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <div className="modal-title">🏦 Import Indian Banks</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <p className="text-muted mb-3" style={{ fontSize: 13 }}>
          {all.length} banks available — select which to add to your list.
        </p>

        {/* Search + Select All */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 10, alignItems: 'center' }}>
          <input
            className="form-input"
            placeholder="🔍 Filter bank names…"
            style={{ flex: 1 }}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            <input type="checkbox" checked={allFilteredSelected} onChange={toggleAll}
              style={{ width: 15, height: 15, accentColor: 'var(--accent)', cursor: 'pointer' }} />
            Select all
          </label>
          <span className="text-muted" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
            {selected.size}/{all.length}
          </span>
        </div>

        {/* Bank list */}
        <div style={{
          flex: 1, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 8,
          background: 'var(--bg)', maxHeight: 360, marginBottom: 16,
        }}>
          {filtered.map((bank, i) => (
            <label key={i} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '9px 14px', cursor: 'pointer',
              borderBottom: '1px solid var(--border)',
              background: i % 2 === 0 ? 'transparent' : 'var(--bg-hover)',
            }}>
              <input type="checkbox" checked={selected.has(bank)} onChange={() => toggle(bank)}
                style={{ width: 15, height: 15, accentColor: 'var(--accent)', cursor: 'pointer' }} />
              <span style={{ fontSize: 13 }}>{bank}</span>
            </label>
          ))}
          {filtered.length === 0 && (
            <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>No banks match "{search}"</p>
          )}
        </div>

        <div className="flex-end gap-2">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={doImport} disabled={importing || !selected.size}>
            {importing ? 'Importing…' : `📥 Import ${selected.size} Banks`}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Imports result toast helper ─────────────────────────────────────────
function importResultToast(data, filename = '') {
  const msg = `${filename ? filename + '\n' : ''}✅ Added: ${data.added}\n⏭ Skipped: ${data.skipped}`;
  if (data.added > 0) toast.success(msg, { duration: 5000 });
  else toast(`⏭ All ${data.skipped} entries already existed`);
}

// ── Main BanksPage ────────────────────────────────────────────────────────────
export default function BanksPage() {
  const [banks, setBanks] = useState([]);
  const [bankName, setBankName] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showDefaultModal, setShowDefaultModal] = useState(false);
  const txtRef = useRef();
  const xlsRef = useRef();

  const load = async () => { const r = await banksAPI.list(); setBanks(r.data); };
  useEffect(() => { load(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const name = bankName.trim();
    if (!name) { toast.error('Bank name is required'); return; }
    setSaving(true);
    try {
      if (editingId !== null) {
        await banksAPI.update(editingId, { bank_name: name });
        toast.success(`Renamed to "${name}"`);
        cancelEdit();
      } else {
        await banksAPI.create({ bank_name: name });
        toast.success(`"${name}" added!`);
        setBankName('');
      }
      load();
    } catch (err) {
      const status = err.response?.status;
      if (status === 409) toast.error(`"${name}" already exists`);
      else toast.error(err.response?.data?.detail || 'Failed');
    } finally { setSaving(false); }
  };

  const startEdit = (bank) => {
    setEditingId(bank.id);
    setBankName(bank.bank_name);
    document.getElementById('bank-name-input')?.focus();
  };
  const cancelEdit = () => { setEditingId(null); setBankName(''); };

  const deleteBank = async (id, name) => {
    if (!confirm(`Delete "${name}"?\nThis will unlink it from any transactions.`)) return;
    try {
      await banksAPI.delete(id);
      toast.success('Bank deleted');
      if (editingId === id) cancelEdit();
      load();
    } catch (err) { toast.error(err.response?.data?.detail || 'Delete failed'); }
  };

  const handleTxtFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const r = await importAPI.importTxt(fd);
      importResultToast(r.data, file.name);
      load();
    } catch (err) { toast.error(err.response?.data?.detail || 'TXT import failed'); }
    e.target.value = '';
  };

  const handleExcelFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const r = await importAPI.importExcel(fd);
      importResultToast(r.data, file.name);
      load();
    } catch (err) { toast.error(err.response?.data?.detail || 'Excel import failed'); }
    e.target.value = '';
  };

  return (
    <div className="fade-in">
      <h1 className="page-title">🏦 Bank Management</h1>

      {/* ── Form + Import bar ─────────────────────────────────────────────── */}
      <div className="card mb-4">
        {/* Add/Edit row */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', alignItems: 'flex-end', gap: 12, flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: '1 1 280px', minWidth: 200 }}>
            <label className="form-label" htmlFor="bank-name-input">Bank Name</label>
            <input
              id="bank-name-input"
              className="form-input"
              placeholder="e.g. SBI, HDFC, Axis …"
              value={bankName}
              onChange={e => setBankName(e.target.value)}
            />
          </div>
          <button id="bank-submit-btn" type="submit"
            className="btn btn-primary" style={{ height: 42, minWidth: 130 }} disabled={saving}>
            {saving ? 'Saving…' : editingId !== null ? '💾 Save Name' : '+ Add Bank'}
          </button>
          {editingId !== null && (
            <button type="button" className="btn btn-ghost" style={{ height: 42 }} onClick={cancelEdit}>
              ✕ Cancel
            </button>
          )}
        </form>

        {editingId !== null && (
          <p className="text-muted" style={{ marginTop: 8, fontSize: 12 }}>
            ✏️ Editing&nbsp;
            <strong style={{ color: 'var(--text)' }}>
              {banks.find(b => b.id === editingId)?.bank_name}
            </strong>
          </p>
        )}

        {/* Import bar */}
        <div style={{ borderTop: '1px solid var(--border)', marginTop: 16, paddingTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <span className="text-muted" style={{ fontSize: 12, fontWeight: 600 }}>BULK IMPORT:</span>
          <button id="import-defaults-btn" className="btn btn-ghost btn-sm"
            style={{ color: 'var(--accent)', borderColor: 'var(--accent)' }}
            onClick={() => setShowDefaultModal(true)}>
            🏦 Indian Banks (137)
          </button>
          <button id="import-txt-btn" className="btn btn-ghost btn-sm"
            style={{ color: 'var(--green)', borderColor: 'var(--green)' }}
            onClick={() => txtRef.current?.click()}>
            📄 Import TXT
          </button>
          <button id="import-excel-btn" className="btn btn-ghost btn-sm"
            style={{ color: '#16A34A', borderColor: '#16A34A' }}
            onClick={() => xlsRef.current?.click()}>
            📗 Import Excel
          </button>
          <span className="text-muted" style={{ fontSize: 11, marginLeft: 'auto' }}>
            {banks.length} bank{banks.length !== 1 ? 's' : ''} in list
          </span>

          {/* Hidden file inputs */}
          <input ref={txtRef} type="file" accept=".txt,.csv" hidden onChange={handleTxtFile} />
          <input ref={xlsRef} type="file" accept=".xlsx,.xls" hidden onChange={handleExcelFile} />
        </div>
      </div>

      {/* ── Table ──────────────────────────────────────────────────────────── */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 60 }}>ID</th>
              <th>Bank Name</th>
              <th style={{ width: 160, textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {banks.map(b => (
              <tr key={b.id} style={editingId === b.id ? { outline: '2px solid var(--accent)', outlineOffset: -1 } : {}}>
                <td className="text-muted">{b.id}</td>
                <td style={{ fontWeight: 600 }}>{b.bank_name}</td>
                <td>
                  <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                    <button className="btn btn-ghost btn-sm"
                      style={{ color: 'var(--teal)', borderColor: 'var(--teal)' }}
                      onClick={() => startEdit(b)}>✏ Edit</button>
                    <button className="btn btn-ghost btn-sm"
                      style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
                      onClick={() => deleteBank(b.id, b.bank_name)}>🗑 Delete</button>
                  </div>
                </td>
              </tr>
            ))}
            {banks.length === 0 && (
              <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 48 }}>
                No banks yet — add one or import from the list above.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showDefaultModal && (
        <DefaultBankModal
          onClose={() => setShowDefaultModal(false)}
          onImported={load}
        />
      )}
    </div>
  );
}
