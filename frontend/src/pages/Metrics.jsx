import React, { useState, useEffect } from 'react';
import { getModelMetrics, retrainFromHistory } from '../services/api';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { 
  Sparkles, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  Database, 
  Cpu, 
  TrendingUp 
} from 'lucide-react';

const Metrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [retrainResult, setRetrainResult] = useState(null);
  const [retrainError, setRetrainError] = useState(null);

  const fetchMetrics = async () => {
    try {
      const data = await getModelMetrics();
      setMetrics(data);
    } catch (error) {
      console.error("Failed to fetch metrics", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainResult(null);
    setRetrainError(null);
    try {
      const res = await retrainFromHistory();
      setRetrainResult(res.message);
      await fetchMetrics();
    } catch (err) {
      setRetrainError(err.response?.data?.detail || err.message);
    } finally {
      setRetraining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" />
        Loading model metrics...
      </div>
    );
  }

  if (!metrics || !metrics.results) {
    return (
      <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100 text-gray-600">
        No metrics available. Model may not be trained yet.
      </div>
    );
  }

  const chartData = Object.keys(metrics.results).map(modelName => ({
    name: modelName,
    MAE: metrics.results[modelName].MAE,
    RMSE: metrics.results[modelName].RMSE,
    R2_Score: Number((metrics.results[modelName].R2 * 10).toFixed(2)) // Scaled for chart visibility
  }));

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            Model Performance & Active Learning
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
              Champion Deployed
            </span>
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Real-time evaluation statistics, R² accuracy scores, and online continuous retraining.
          </p>
        </div>

        {/* Self-Tuning Button */}
        <button
          onClick={handleRetrain}
          disabled={retraining}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm disabled:opacity-50 flex items-center font-medium transition-all"
        >
          {retraining ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4 mr-2 text-indigo-200" />
          )}
          {retraining ? "Tuning on History..." : "Self-Tune from History"}
        </button>
      </div>

      {/* Retrain Alert Message */}
      {retrainResult && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl flex items-center gap-2 text-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{retrainResult}</span>
        </div>
      )}

      {retrainError && (
        <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl flex items-center gap-2 text-sm">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>{retrainError}</span>
        </div>
      )}

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Champion Algorithm</span>
          <p className="text-xl font-bold text-indigo-600 truncate">{metrics.best_model}</p>
          <span className="text-xs text-gray-400 mt-1 block">
            {metrics.is_log_target ? 'Target: Log-Scale (log1p)' : 'Target: Linear'}
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">R² Accuracy Score</span>
          <p className="text-xl font-bold text-emerald-600">
            {(metrics.results?.[metrics.best_model]?.R2 * 100).toFixed(1)}%
          </p>
          <span className="text-xs text-emerald-600 mt-1 block font-medium">State-of-the-art fit</span>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Training Dataset</span>
          <p className="text-xl font-bold text-gray-900">
            {(metrics.total_dataset_samples || metrics.training_samples + metrics.testing_samples || 0).toLocaleString()} samples
          </p>
          <span className="text-xs text-gray-400 mt-1 block">
            Split: {metrics.training_samples?.toLocaleString()} train / {metrics.testing_samples?.toLocaleString()} test
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Deep Features</span>
          <p className="text-xl font-bold text-gray-900">
            {metrics.number_of_features || metrics.features?.length || 24} metrics
          </p>
          <span className="text-xs text-gray-400 mt-1 block truncate">
            Scanned rows, joins, costs
          </span>
        </div>
      </div>

      {/* Model Leaderboard Table */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-indigo-600" />
          Model Tournament Leaderboard
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-xs uppercase font-bold text-gray-500">
                <th className="pb-3">Model</th>
                <th className="pb-3">MAE (Lower is Better)</th>
                <th className="pb-3">RMSE</th>
                <th className="pb-3">R² Score (Higher is Better)</th>
                <th className="pb-3">Training Time</th>
                <th className="pb-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {Object.keys(metrics.results).map((name, idx) => {
                const res = metrics.results[name];
                const isChampion = name === metrics.best_model;
                return (
                  <tr key={idx} className={isChampion ? "bg-indigo-50/40 font-medium" : ""}>
                    <td className="py-3 text-gray-900 flex items-center gap-1.5">
                      {isChampion && <span className="text-amber-500">🏆</span>}
                      {name}
                    </td>
                    <td className="py-3 font-mono text-gray-700">{res.MAE.toFixed(4)} ms</td>
                    <td className="py-3 font-mono text-gray-700">{res.RMSE.toFixed(4)} ms</td>
                    <td className="py-3 font-mono font-bold text-emerald-600">
                      {(res.R2 * 100).toFixed(2)}%
                    </td>
                    <td className="py-3 font-mono text-gray-500">{res.FitTimeSec ? `${res.FitTimeSec}s` : '< 1s'}</td>
                    <td className="py-3">
                      {isChampion ? (
                        <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 text-xs font-semibold">
                          Active In Production
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">Evaluated</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recharts Bar Chart */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-96">
        <h2 className="text-lg font-bold text-gray-900 mb-2">Error Comparison (Lower is Better)</h2>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} />
            <Tooltip />
            <Legend />
            <Bar dataKey="MAE" fill="#4f46e5" name="Mean Absolute Error (ms)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="RMSE" fill="#06b6d4" name="Root Mean Squared Error (ms)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Extracted Deep Features Grid */}
      {metrics.features && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            Active Plan Tree Feature Vectors ({metrics.features.length})
          </h2>
          <div className="flex flex-wrap gap-1.5">
            {metrics.features.map((feat, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 bg-gray-50 border border-gray-200 text-gray-700 text-xs font-mono rounded-md"
              >
                {feat}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Metrics;
