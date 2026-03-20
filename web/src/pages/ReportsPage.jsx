import React, { useEffect, useState } from 'react';
import { reportsAPI, banksAPI } from '../api/axiosClient.js';
import toast from 'react-hot-toast';

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const [banks, setBanks] = useState([]);
  const [filters, setFilters] = useState({
    date_from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
    date_to: new Date().toISOString().slice(0, 10),
    bank_id: '',
    app_used: '',
  });
  const set = (k, v) => setFilters(f => ({ ...f, [k]: v }));
  const [loading, setLoading] = useState('');

  useEffect(() => { banksAPI.list().then(r => setBanks(r.data)); }, []);

  const getParams = () => {
    const p = { date_from: filters.date_from, date_to: filters.date_to };
    if (filters.bank_id) p.bank_id = parseInt(filters.bank_id);
    if (filters.app_used) p.app_used = filters.app_used;
    return p;
  };

  const exportFile = async (type) => {
    setLoading(type);
    try {
      let res, filename, mimeType;
      const params = getParams();
      if (type === 'csv') { res = await reportsAPI.exportCsv(params); filename = 'transactions.csv'; mimeType = 'text/csv'; }
      else if (type === 'excel') { res = await reportsAPI.exportExcel(params); filename = 'transactions.xlsx'; mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'; }
      else { res = await reportsAPI.exportPdf(params); filename = 'transactions.pdf'; mimeType = 'application/pdf'; }
      downloadBlob(new Blob([res.data], { type: mimeType }), filename);
      toast.success(`${filename} downloaded!`);
    } catch (err) {
      toast.error('Export failed. Please try again.');
    } finally {
      setLoading('');
    }
  };

  const APPS = ['PhonePe', 'Paytm', 'PayNear', 'Bank App', 'ATM', 'UPI', 'Cash', 'Other'];

  return (
    <div className="fade-in">
      <h1 className="page-title">📄 Reports & Export</h1>
      <div className="card">
        <div className="card-header">Filter Options</div>
        <div className="form-grid mb-4">
          <div className="form-group">
            <label className="form-label">From Date</label>
            <input id="date-from" type="date" className="form-input" value={filters.date_from} onChange={e => set('date_from', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">To Date</label>
            <input id="date-to" type="date" className="form-input" value={filters.date_to} onChange={e => set('date_to', e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Bank</label>
            <select className="form-select" value={filters.bank_id} onChange={e => set('bank_id', e.target.value)}>
              <option value="">All Banks</option>
              {banks.map(b => <option key={b.id} value={b.id}>{b.bank_name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">App / Channel</label>
            <select className="form-select" value={filters.app_used} onChange={e => set('app_used', e.target.value)}>
              <option value="">All Apps</option>
              {APPS.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
        </div>

        <div className="flex gap-3" style={{ flexWrap: 'wrap' }}>
          {[
            { type: 'csv', label: '📊 Export CSV', color: 'var(--green)' },
            { type: 'excel', label: '📗 Export Excel', color: 'var(--teal)' },
            { type: 'pdf', label: '📕 Export PDF', color: 'var(--red)' },
          ].map(({ type, label, color }) => (
            <button
              key={type}
              id={`export-${type}-btn`}
              className="btn"
              style={{ background: color, color: 'white', minWidth: 160 }}
              onClick={() => exportFile(type)}
              disabled={!!loading}
            >
              {loading === type ? 'Exporting...' : label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
