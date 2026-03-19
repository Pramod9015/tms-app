import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, PieChart, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { dashboardAPI } from '../api/axiosClient.js';

const COLORS = ['#2563EB', '#7C3AED', '#059669', '#D97706', '#EF4444', '#0891B2', '#DB2777'];

const STATUS_BADGE = {
  completed: 'badge-green',
  pending: 'badge-yellow',
  failed: 'badge-red',
  reversed: 'badge-red',
};

function SummaryCard({ label, value, color }) {
  return (
    <div className="summary-card">
      <div className="value" style={{ color }}>{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [daily, setDaily] = useState([]);
  const [appUsage, setAppUsage] = useState([]);
  const [bankWise, setBankWise] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [s, d, a, b, m, r] = await Promise.all([
          dashboardAPI.getSummary(),
          dashboardAPI.getDailyChart(30),
          dashboardAPI.getAppUsage(),
          dashboardAPI.getBankWise(),
          dashboardAPI.getMonthlyTrend(),
          dashboardAPI.getRecentTransactions(10),
        ]);
        setSummary(s.data);
        setDaily(d.data);
        setAppUsage(a.data);
        setBankWise(b.data);
        setMonthly(m.data);
        setRecent(r.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div className="spinner" />;

  return (
    <div className="fade-in">
      <div className="flex-between mb-6">
        <h1 className="page-title" style={{ margin: 0 }}>📊 Dashboard</h1>
        <button className="btn btn-ghost btn-sm" onClick={() => window.location.reload()}>🔄 Refresh</button>
      </div>

      {/* Summary Cards */}
      <div className="summary-grid">
        <SummaryCard label="Total Transactions" value={summary?.total_transactions ?? '—'} color="var(--accent)" />
        <SummaryCard label="Withdrawals" value={summary?.total_withdrawals ?? '—'} color="var(--purple)" />
        <SummaryCard label="Transfers" value={summary?.total_transfers ?? '—'} color="var(--green)" />
        <SummaryCard label="Today's Amount" value={summary ? `₹${summary.today_amount.toLocaleString('en-IN')}` : '—'} color="var(--yellow)" />
        <SummaryCard label="This Month" value={summary ? `₹${summary.month_amount.toLocaleString('en-IN')}` : '—'} color="var(--teal)" />
      </div>

      {/* Charts Row 1 */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-title">📈 Daily Transactions (Last 30 Days)</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" tick={{ fill: '#94A3B8', fontSize: 10 }} tickFormatter={v => v.slice(5)} />
              <YAxis tick={{ fill: '#94A3B8', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8 }} labelStyle={{ color: '#F1F5F9' }} />
              <Line type="monotone" dataKey="amount" stroke="#2563EB" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <div className="chart-title">🥧 App Usage</div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={appUsage} dataKey="count" nameKey="app" cx="50%" cy="50%" outerRadius={70} label={({ app, percent }) => `${app} ${(percent * 100).toFixed(0)}%`}>
                {appUsage.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="charts-grid mb-6">
        <div className="chart-card">
          <div className="chart-title">🏦 Bank-wise Transactions</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={bankWise}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="bank" tick={{ fill: '#94A3B8', fontSize: 10 }} />
              <YAxis tick={{ fill: '#94A3B8', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                {bankWise.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <div className="chart-title">📅 Monthly Trend</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={monthly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" tick={{ fill: '#94A3B8', fontSize: 10 }} />
              <YAxis tick={{ fill: '#94A3B8', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8 }} />
              <Line type="monotone" dataKey="amount" stroke="#7C3AED" strokeWidth={2} dot={{ r: 4, fill: '#7C3AED' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="card-header" style={{ fontSize: 16, fontWeight: 700 }}>Recent Transactions</div>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th><th>Type</th><th>App</th><th>Amount</th>
              <th>Bank</th><th>Status</th><th>Reference</th>
            </tr>
          </thead>
          <tbody>
            {recent.map(t => (
              <tr key={t.id}>
                <td>{t.date?.slice(0, 16)}</td>
                <td style={{ textTransform: 'capitalize' }}>{t.transaction_type}</td>
                <td>{t.app_used}</td>
                <td className="text-green" style={{ fontWeight: 600 }}>₹{parseFloat(t.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                <td>{t.bank_name || '—'}</td>
                <td><span className={`badge ${STATUS_BADGE[t.status] || 'badge-blue'}`}>{t.status}</span></td>
                <td className="text-muted">{t.reference_number || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
