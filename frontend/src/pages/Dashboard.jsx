import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboardAnalytics } from '../services/api';
import { 
  Activity, 
  Clock, 
  Zap, 
  AlertTriangle, 
  TrendingUp, 
  BarChart3, 
  CheckCircle2, 
  RefreshCw, 
  ExternalLink,
  Flame,
  ArrowUpRight,
  ShieldCheck,
  Server
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Cell,
  AreaChart,
  Area
} from 'recharts';

const StatCard = ({ title, value, subtext, icon: Icon, colorClass, borderClass }) => (
  <div className={`bg-white p-5 rounded-2xl shadow-sm border ${borderClass || 'border-gray-100'} flex items-start justify-between`}>
    <div>
      <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">{title}</p>
      <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
      {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
    </div>
    <div className={`p-3 rounded-xl ${colorClass}`}>
      <Icon className="w-5 h-5 text-white" />
    </div>
  </div>
);

const Dashboard = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAnalytics = async () => {
    try {
      const res = await getDashboardAnalytics();
      setData(res);
    } catch (error) {
      console.error("Failed to fetch dashboard analytics", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAnalytics();
  };

  const handleAnalyzeQuery = (sqlText) => {
    navigate('/analyzer', { state: { query: sqlText } });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <RefreshCw className="w-6 h-6 animate-spin mr-2 text-indigo-600" />
        <span>Loading system analytics...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 bg-white rounded-xl shadow-sm border border-red-100 text-red-600">
        Failed to load dashboard analytics. Ensure backend is running.
      </div>
    );
  }

  const { summary, latency_distribution, accuracy_trends, slowest_queries, category_breakdown } = data;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            Database Performance Dashboard
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
              Live Monitoring
            </span>
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Real-time execution latency, ML prediction accuracy tracking, and bottleneck identification.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-3.5 py-2 bg-white hover:bg-gray-50 border border-gray-200 text-gray-700 rounded-xl text-sm font-semibold flex items-center gap-2 shadow-sm transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh Stats
        </button>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Queries" 
          value={summary.total_queries.toLocaleString()} 
          subtext={`${summary.executed_queries.toLocaleString()} executed with plan telemetry`}
          icon={Activity} 
          colorClass="bg-blue-600" 
          borderClass="border-blue-100"
        />
        <StatCard 
          title="Avg Actual Latency" 
          value={`${summary.average_actual_time_ms} ms`} 
          subtext={`ML prediction avg: ${summary.average_predicted_time_ms} ms`}
          icon={Clock} 
          colorClass="bg-indigo-600" 
          borderClass="border-indigo-100"
        />
        <StatCard 
          title="Model Error Rate" 
          value={`${summary.average_prediction_error_percent}%`} 
          subtext="Normalized microsecond metric"
          icon={Zap} 
          colorClass="bg-emerald-600" 
          borderClass="border-emerald-100"
        />
        <StatCard 
          title="High Latency Queries" 
          value={summary.high_cost_queries} 
          subtext="Queries running > 500 ms"
          icon={Flame} 
          colorClass="bg-rose-600" 
          borderClass="border-rose-100"
        />
      </div>

      {/* Two Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Latency Distribution */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col h-[380px]">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                Query Execution Latency Distribution
              </h2>
              <p className="text-xs text-gray-400">Frequency of queries across execution speed buckets</p>
            </div>
          </div>

          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={latency_distribution} margin={{ top: 15, right: 20, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="range" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} allowDecimals={false} />
                <Tooltip 
                  formatter={(val, name, item) => [`${val} queries`, item.payload.description]}
                  contentStyle={{ backgroundColor: '#111827', color: '#f3f4f6', borderRadius: '8px', border: 'none', fontSize: '12px' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {latency_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Accuracy & Calibration Trend Line */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col h-[380px]">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-600" />
                ML Prediction vs. Actual Database Latency
              </h2>
              <p className="text-xs text-gray-400">Sequential calibration tracking across recent executed queries</p>
            </div>
          </div>

          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={accuracy_trends} margin={{ top: 15, right: 20, left: -10, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="id" stroke="#6b7280" fontSize={11} label={{ value: 'Query ID', position: 'insideBottom', offset: -2, fontSize: 10 }} />
                <YAxis stroke="#6b7280" fontSize={11} unit="ms" />
                <Tooltip 
                  formatter={(value, name) => [`${value} ms`, name === 'actual_ms' ? 'Actual Time' : 'ML Predicted']}
                  labelFormatter={(id) => `Query #${id}`}
                  contentStyle={{ backgroundColor: '#111827', color: '#f3f4f6', borderRadius: '8px', border: 'none', fontSize: '12px' }}
                />
                <Legend />
                <Area type="monotone" dataKey="actual_ms" name="Actual (ms)" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorActual)" />
                <Area type="monotone" dataKey="predicted_ms" name="ML Predicted (ms)" stroke="#6366f1" strokeWidth={2} strokeDasharray="4 4" fillOpacity={1} fill="url(#colorPred)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Latency Risk Tier Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {category_breakdown.map((cat, idx) => (
          <div key={idx} className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: cat.color }}></span>
              <span className="text-sm font-semibold text-gray-800">{cat.name}</span>
            </div>
            <span className="text-base font-bold text-gray-900">{cat.count.toLocaleString()}</span>
          </div>
        ))}
      </div>

      {/* Top 5 Slowest Queries Leaderboard with 1-Click Action */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Flame className="w-5 h-5 text-rose-600" />
              Top Slowest Queries Leaderboard
            </h2>
            <p className="text-xs text-gray-500">
              Identify the most resource-intensive historical queries and jump straight to index tuning.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-xs uppercase font-bold text-gray-400">
                <th className="pb-3 w-12">Rank</th>
                <th className="pb-3">Query Snippet</th>
                <th className="pb-3 text-right">Actual Time</th>
                <th className="pb-3 text-right">ML Prediction</th>
                <th className="pb-3 text-right">Error</th>
                <th className="pb-3 text-center">Latency Risk</th>
                <th className="pb-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {slowest_queries.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50/80 transition-colors">
                  <td className="py-3.5 font-bold text-gray-500 text-xs">
                    <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full font-bold ${
                      item.rank === 1 ? 'bg-amber-100 text-amber-800' :
                      item.rank === 2 ? 'bg-gray-200 text-gray-800' :
                      item.rank === 3 ? 'bg-amber-50 text-amber-900' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      #{item.rank}
                    </span>
                  </td>
                  <td className="py-3.5 font-mono text-xs text-gray-800 max-w-md truncate">
                    {item.query_text}
                  </td>
                  <td className="py-3.5 text-right font-mono font-bold text-rose-600 text-xs">
                    {item.actual_time_ms} ms
                  </td>
                  <td className="py-3.5 text-right font-mono text-indigo-600 text-xs font-semibold">
                    {item.predicted_time_ms} ms
                  </td>
                  <td className="py-3.5 text-right font-mono text-gray-600 text-xs">
                    {item.error_pct}%
                  </td>
                  <td className="py-3.5 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${
                      item.performance_category === 'HIGH' ? 'bg-red-100 text-red-800' :
                      item.performance_category === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                      'bg-emerald-100 text-emerald-800'
                    }`}>
                      {item.performance_category}
                    </span>
                  </td>
                  <td className="py-3.5 text-right">
                    <button
                      onClick={() => handleAnalyzeQuery(item.query_text)}
                      className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold flex items-center gap-1 ml-auto transition-all"
                      title="Load this query in Analyzer editor to view execution plan and get index recommendations"
                    >
                      <span>Analyze</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
