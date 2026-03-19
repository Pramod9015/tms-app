import React, { useEffect, useState, useCallback, useRef } from 'react';
import { transactionsAPI, banksAPI, beneficiariesAPI } from '../api/axiosClient.js';
import axiosClient from '../api/axiosClient.js';
import toast from 'react-hot-toast';

const TYPES = ['withdrawal', 'transfer', 'phonepe', 'paytm', 'paynear', 'bank_app', 'atm', 'upi', 'other'];
const APPS  = ['phonepe', 'paytm', 'paynear', 'bank_app', 'atm', 'upi', 'other'];
const STATUSES = ['completed', 'pending', 'failed', 'reversed'];

const today = () => new Date().toISOString().slice(0, 10);

const empty = () => ({
  mobile: '',                  // look-up field (not saved)
  beneficiary_id: '',
  account_number: '',          // display only
  bank_id: '',
  amount: '',
  transaction_type: 'withdrawal',
  app_used: 'other',
  status: 'completed',
  reference_number: '',
  notes: '',
  transaction_date: today(),
});

// ── Mobile auto-fill timeout ─
let mobileTimer = null;

export default function TransactionsPage() {
  const [txns, setTxns]       = useState([]);
  const [banks, setBanks]      = useState([]);
  const [bens, setBens]        = useState([]);
  const [search, setSearch]   = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm]        = useState(empty());
  const [mobileBens, setMobileBens] = useState([]);
  const [mobileLoading, setMobileLoading] = useState(false);
  const [filters, setFilters]  = useState({ type: '', start: '', end: '' });
  // Slip OCR
  const [slipSrc, setSlipSrc]       = useState(null);    // preview URL
  const [slipScanning, setSlipScanning] = useState(false);
  const [slipResult, setSlipResult]   = useState(null);  // extracted fields
  const slipInputRef = useRef();

  const load = useCallback(async () => {
    const params = {};
    if (filters.type)  params.transaction_type = filters.type;
    if (filters.start) params.start_date = filters.start;
    if (filters.end)   params.end_date   = filters.end;
    const [t, b, bn] = await Promise.all([
      transactionsAPI.list(params),
      banksAPI.list(),
      beneficiariesAPI.list(),
    ]);
    setTxns(t.data);
    setBanks(b.data);
    setBens(bn.data);
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  // ── Form helpers ────────────────────────────────────────────────────────────
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const openModal = () => { setForm(empty()); setMobileBens([]); setSlipSrc(null); setSlipResult(null); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setMobileBens([]); setSlipSrc(null); setSlipResult(null); };

  // ── Mobile auto-fill ────────────────────────────────────────────────────────
  const onMobileChange = (val) => {
    set('mobile', val);
    clearTimeout(mobileTimer);
    // Reset auto-filled fields when mobile changes
    setForm(f => ({ ...f, mobile: val, beneficiary_id: '', account_number: '', bank_id: '' }));
    setMobileBens([]);
    if (val.replace(/\D/g, '').length < 10) return;
    mobileTimer = setTimeout(async () => {
      setMobileLoading(true);
      try {
        const r = await beneficiariesAPI.byMobile(val.trim());
        const matched = r.data;
        if (matched.length === 0) {
          toast('No beneficiary found for this number', { icon: 'ℹ️' });
        } else if (matched.length === 1) {
          applyBeneficiary(matched[0]);
          toast.success(`Auto-filled: ${matched[0].name}`);
        } else {
          // Multiple — show selection dropdown
          setMobileBens(matched);
          toast(`${matched.length} beneficiaries found — please select one`, { icon: '👥' });
        }
      } catch (_) {} finally { setMobileLoading(false); }
    }, 600);
  };

  const applyBeneficiary = (ben) => {
    setForm(f => ({
      ...f,
      beneficiary_id: String(ben.id),
      account_number: ben.account_number || '',
      bank_id: banks.find(b => b.bank_name === ben.bank_name)?.id ? String(banks.find(b => b.bank_name === ben.bank_name).id) : f.bank_id,
    }));
    setMobileBens([]);
  };

  // ── Slip OCR ────────────────────────────────────────────────────────────────
  const handleSlipFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSlipSrc(URL.createObjectURL(file));
    setSlipResult(null);
    setSlipScanning(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const r = await axiosClient.post('/transactions/parse-slip', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const d = r.data;
      setSlipResult(d);
      if (d.error) { toast.error(`OCR: ${d.error}`); return; }
      // Auto-fill extracted fields
      setForm(f => ({
        ...f,
        amount:           d.amount           || f.amount,
        transaction_date: d.date             || f.transaction_date,
        mobile:           d.mobile_number    || f.mobile,
        account_number:   d.account_number   || f.account_number,
        reference_number: d.reference_number || f.reference_number,
      }));
      // Auto-match bank by name
      if (d.bank_name) {
        const matched = banks.find(b => b.bank_name.toLowerCase().includes(d.bank_name.toLowerCase()));
        if (matched) setForm(f => ({ ...f, bank_id: String(matched.id) }));
      }
      // Auto-match beneficiary by name
      if (d.beneficiary_name) {
        const ben = bens.find(b => b.name.toLowerCase().includes(d.beneficiary_name.toLowerCase()));
        if (ben) setForm(f => ({ ...f, beneficiary_id: String(ben.id), account_number: ben.account_number || f.account_number }));
      }
      // Also trigger mobile lookup if we got a mobile number
      if (d.mobile_number) onMobileChange(d.mobile_number);
      const filled = [d.amount, d.date, d.mobile_number, d.bank_name, d.account_number, d.beneficiary_name, d.reference_number].filter(Boolean).length;
      toast.success(`✅ Slip scanned! ${filled} field${filled !== 1 ? 's' : ''} extracted (${d.confidence} confidence)`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Slip scan failed';
      toast.error(msg);
      if (msg.includes('GEMINI_API_KEY')) {
        toast('Add GEMINI_API_KEY to your .env file to enable slip OCR', { icon: '🔑', duration: 6000 });
      }
    } finally {
      setSlipScanning(false);
      e.target.value = '';
    }
  };

  // ── Submit ──────────────────────────────────────────────────────────────────
  const submit = async (e) => {
    e.preventDefault();
    if (!form.amount || isNaN(form.amount)) { toast.error('Valid amount required'); return; }
    const payload = {
      amount: parseFloat(form.amount),
      transaction_type: form.transaction_type,
      app_used: form.app_used,
      status: form.status,
      transaction_date: form.transaction_date,
      reference_number: form.reference_number || null,
      notes: form.notes || null,
      bank_id: form.bank_id ? parseInt(form.bank_id) : null,
      beneficiary_id: form.beneficiary_id ? parseInt(form.beneficiary_id) : null,
    };
    try {
      await transactionsAPI.create(payload);
      toast.success('Transaction saved!');
      closeModal();
      load();
    } catch (err) { toast.error(err.response?.data?.detail || 'Save failed'); }
  };

  // ── Search / filter ─────────────────────────────────────────────────────────
  const displayed = txns.filter(t => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (t.bank_name || '').toLowerCase().includes(q) ||
      (t.beneficiary_name || '').toLowerCase().includes(q) ||
      (t.transaction_type || '').includes(q) ||
      (t.reference_number || '').toLowerCase().includes(q) ||
      String(t.amount).includes(q)
    );
  });

  const fmt = (d) => d ? new Date(d).toLocaleDateString('en-IN') : '—';
  const fmtAmt = (a) => `₹${parseFloat(a).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  const badge = (s) => {
    const map = { completed: 'badge-success', pending: 'badge-warning', failed: 'badge-error', reversed: 'badge-muted' };
    return <span className={`badge ${map[s] || ''}`}>{s}</span>;
  };

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 className="page-title" style={{ margin: 0 }}>💸 Transactions</h1>
        <button id="add-transaction-btn" className="btn btn-primary" onClick={openModal}>+ Add Transaction</button>
      </div>

      {/* ── Filter + Search bar ───────────────────────────────────────────── */}
      <div className="filter-bar mb-4" style={{ flexWrap: 'wrap', gap: 10 }}>
        <input className="form-input" style={{ maxWidth: 280 }}
          placeholder="🔍 Search amount, bank, beneficiary, ref…"
          value={search} onChange={e => setSearch(e.target.value)} />

        <select className="form-select" value={filters.type}
          onChange={e => setFilters(f => ({ ...f, type: e.target.value }))}>
          <option value="">All Types</option>
          {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>

        <input className="form-input" type="date" style={{ maxWidth: 160 }} value={filters.start}
          onChange={e => setFilters(f => ({ ...f, start: e.target.value }))} />
        <span className="text-muted">to</span>
        <input className="form-input" type="date" style={{ maxWidth: 160 }} value={filters.end}
          onChange={e => setFilters(f => ({ ...f, end: e.target.value }))} />

        <button className="btn btn-ghost btn-sm" onClick={() => { setFilters({ type: '', start: '', end: '' }); setSearch(''); }}>
          ✕ Reset
        </button>
        <span className="text-muted" style={{ fontSize: 12, marginLeft: 'auto' }}>
          {displayed.length} transaction{displayed.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* ── Table ─────────────────────────────────────────────────────────── */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th><th>Amount</th><th>Type</th><th>App / Channel</th>
              <th>Bank</th><th>Beneficiary</th><th>Status</th><th>Ref</th><th></th>
            </tr>
          </thead>
          <tbody>
            {displayed.map(t => (
              <tr key={t.id}>
                <td>{fmt(t.transaction_date)}</td>
                <td style={{ fontWeight: 700 }}>{fmtAmt(t.amount)}</td>
                <td><span className="badge badge-info">{t.transaction_type}</span></td>
                <td className="text-muted">{t.app_used}</td>
                <td>{t.bank_name || '—'}</td>
                <td>{t.beneficiary_name || '—'}</td>
                <td>{badge(t.status)}</td>
                <td className="text-muted" style={{ fontSize: 11 }}>{t.reference_number || '—'}</td>
                <td>
                  <button className="btn btn-ghost btn-sm"
                    style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
                    onClick={async () => {
                      if (!confirm('Delete this transaction?')) return;
                      await transactionsAPI.delete(t.id);
                      toast.success('Deleted'); load();
                    }}>🗑</button>
                </td>
              </tr>
            ))}
            {displayed.length === 0 && (
              <tr><td colSpan={9} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>
                {search ? `No transactions match "${search}"` : 'No transactions recorded yet.'}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Add Transaction Modal ─────────────────────────────────────────── */}
      {showModal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && closeModal()}>
          <div className="modal" style={{ minWidth: 620, maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <div className="modal-title">+ Add Transaction</div>
              <button className="modal-close" onClick={closeModal}>✕</button>
            </div>

            <form onSubmit={submit}>
              {/* ── Scan Slip panel ────────────────────────────────────────── */}
              <div style={{
                background: 'linear-gradient(135deg, #1e3a5f22, #2563eb11)',
                border: '1px solid #2563eb44', borderRadius: 10,
                padding: '12px 14px', marginBottom: 14,
                display: 'flex', gap: 14, alignItems: 'flex-start',
              }}>
                {/* Preview */}
                {slipSrc ? (
                  <img src={slipSrc} alt="slip" style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 6, border: '1px solid var(--border)', flexShrink: 0 }} />
                ) : (
                  <div style={{ width: 80, height: 80, background: 'var(--bg)', borderRadius: 6, border: '2px dashed var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, flexShrink: 0 }}>📄</div>
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>📷 Scan Transaction Slip</div>
                  <p className="text-muted" style={{ fontSize: 11, margin: '0 0 8px' }}>Upload a photo of your slip — fields will be auto-filled (supports Hindi &amp; English handwriting)</p>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <button type="button" id="scan-slip-btn"
                      className="btn btn-ghost btn-sm"
                      style={{ color: '#8B5CF6', borderColor: '#8B5CF6' }}
                      onClick={() => slipInputRef.current?.click()}
                      disabled={slipScanning}>
                      {slipScanning ? '⏳ Scanning…' : '📷 Upload Slip'}
                    </button>
                    {slipResult && !slipResult.error && (
                      <span className="badge" style={{ background: slipResult.confidence === 'high' ? '#166534' : slipResult.confidence === 'medium' ? '#92400e' : '#374151', color: 'white', fontSize: 10 }}>
                        {slipResult.confidence} confidence
                      </span>
                    )}
                    {slipSrc && (
                      <button type="button" className="btn btn-ghost btn-sm"
                        style={{ fontSize: 10 }}
                        onClick={() => { setSlipSrc(null); setSlipResult(null); }}>
                        ✕ Clear
                      </button>
                    )}
                  </div>
                  {slipResult && slipResult.error && (
                    <p style={{ color: 'var(--red)', fontSize: 11, marginTop: 4 }}>⚠️ {slipResult.error}</p>
                  )}
                  {slipResult && !slipResult.error && (
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                      {[
                        slipResult.amount          && `₹${slipResult.amount}`,
                        slipResult.date            && `📅 ${slipResult.date}`,
                        slipResult.mobile_number   && `📱 ${slipResult.mobile_number}`,
                        slipResult.bank_name       && `🏦 ${slipResult.bank_name}`,
                        slipResult.beneficiary_name && `👤 ${slipResult.beneficiary_name}`,
                        slipResult.reference_number && `#${slipResult.reference_number}`,
                      ].filter(Boolean).map((tag, i) => (
                        <span key={i} style={{ background: '#2563eb22', color: 'var(--accent)', border: '1px solid #2563eb44', borderRadius: 4, padding: '2px 7px', fontSize: 11 }}>{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
                <input ref={slipInputRef} type="file" accept="image/*" capture="environment" hidden onChange={handleSlipFile} />
              </div>

              {/* ── Mobile lookup (top) ──────────────────────────────────── */}
              <div className="form-group mb-3"
                style={{ background: 'var(--bg-hover)', borderRadius: 8, padding: '12px 14px', border: '1px solid var(--border)' }}>
                <label className="form-label">
                  📱 Mobile Number
                  {mobileLoading && <span className="text-muted" style={{ fontSize: 11 }}> &nbsp;looking up…</span>}
                </label>
                <input id="txn-mobile" className="form-input" placeholder="Enter 10-digit mobile to auto-fill beneficiary…"
                  value={form.mobile} onChange={e => onMobileChange(e.target.value)} />

                {/* Multiple beneficiary picker */}
                {mobileBens.length > 1 && (
                  <div style={{ marginTop: 8 }}>
                    <p className="text-muted mb-1" style={{ fontSize: 12 }}>
                      👥 Multiple beneficiaries found — select one:
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {mobileBens.map(b => (
                        <button key={b.id} type="button"
                          className="btn btn-ghost btn-sm"
                          style={{ justifyContent: 'flex-start', textAlign: 'left' }}
                          onClick={() => applyBeneficiary(b)}>
                          <strong>{b.name}</strong>&nbsp;
                          <span className="text-muted">— {b.bank_name || 'No bank'} {b.account_number ? `(***${b.account_number.slice(-4)})` : ''}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* ── Main fields ──────────────────────────────────────────── */}
              <div className="form-grid mb-3" style={{ gridTemplateColumns: '1fr 1fr' }}>

                <div className="form-group">
                  <label className="form-label">Amount (₹) *</label>
                  <input id="txn-amount" className="form-input" type="number" step="0.01" placeholder="0.00"
                    value={form.amount} onChange={e => set('amount', e.target.value)} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input className="form-input" type="date" value={form.transaction_date}
                    onChange={e => set('transaction_date', e.target.value)} />
                </div>

                <div className="form-group">
                  <label className="form-label">Type</label>
                  <select className="form-select" value={form.transaction_type}
                    onChange={e => set('transaction_type', e.target.value)}>
                    {TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">App / Channel</label>
                  <select className="form-select" value={form.app_used}
                    onChange={e => set('app_used', e.target.value)}>
                    {APPS.map(a => <option key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</option>)}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Bank</label>
                  <select className="form-select" value={form.bank_id}
                    onChange={e => set('bank_id', e.target.value)}>
                    <option value="">— Select Bank —</option>
                    {banks.map(b => <option key={b.id} value={b.id}>{b.bank_name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Beneficiary</label>
                  <select className="form-select" value={form.beneficiary_id}
                    onChange={e => {
                      const ben = bens.find(b => String(b.id) === e.target.value);
                      set('beneficiary_id', e.target.value);
                      if (ben) set('account_number', ben.account_number || '');
                    }}>
                    <option value="">— Select Beneficiary —</option>
                    {bens.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                </div>

                {/* Account number (auto-filled or manual) */}
                <div className="form-group">
                  <label className="form-label">Account Number</label>
                  <input className="form-input" placeholder="Auto-filled from beneficiary"
                    value={form.account_number} onChange={e => set('account_number', e.target.value)} />
                </div>

                <div className="form-group">
                  <label className="form-label">Status</label>
                  <select className="form-select" value={form.status}
                    onChange={e => set('status', e.target.value)}>
                    {STATUSES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                  </select>
                </div>

                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label">Reference / UTR</label>
                  <input className="form-input" placeholder="Reference number"
                    value={form.reference_number} onChange={e => set('reference_number', e.target.value)} />
                </div>

                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label">Notes 🔒 <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: 11 }}>(encrypted)</span></label>
                  <textarea className="form-input" rows={3} placeholder="Optional notes…"
                    value={form.notes} onChange={e => set('notes', e.target.value)} />
                </div>
              </div>

              <div className="flex-end gap-2">
                <button type="button" className="btn btn-ghost" onClick={closeModal}>Cancel</button>
                <button id="save-transaction-btn" type="submit" className="btn btn-primary">💾 Save Transaction</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
