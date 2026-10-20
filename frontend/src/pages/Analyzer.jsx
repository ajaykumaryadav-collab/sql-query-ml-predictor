import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { 
  analyzeQuery, 
  executeQuery, 
  simulateIndex, 
  rewriteQuery 
} from '../services/api';
import { 
  Play, 
  Database, 
  Activity, 
  AlertCircle, 
  Sparkles, 
  Copy, 
  Check, 
  DollarSign, 
  Cpu, 
  HardDrive, 
  Zap, 
  TrendingDown, 
  Layers, 
  RefreshCw, 
  Wand2, 
  ArrowRight, 
  CheckCircle2, 
  X,
  Gauge
} from 'lucide-react';
import PlanVisualizer from '../components/PlanVisualizer';

const QUERY_TEMPLATES = [
  {
    name: "30-Day City Revenue",
    query: `SELECT c.city, COUNT(o.id) AS total_orders, SUM(o.total_amount) AS revenue
FROM customers c
JOIN orders o ON c.id = o.customer_id
WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY c.city
ORDER BY revenue DESC;`
  },
  {
    name: "VIP Customers (CTE)",
    query: `WITH customer_totals AS (
    SELECT customer_id, 
           COUNT(id) AS order_count, 
           SUM(total_amount) AS total_spent
    FROM orders
    WHERE status = 'COMPLETED'
    GROUP BY customer_id
    HAVING SUM(total_amount) > 10000
)
SELECT c.name, c.email, c.city, ct.order_count, ct.total_spent
FROM customers c
JOIN customer_totals ct ON c.id = ct.customer_id
ORDER BY ct.total_spent DESC
LIMIT 10;`
  },
  {
    name: "Unindexed Status Scan",
    query: `SELECT * 
FROM orders 
WHERE total_amount > 1000 AND status = 'CANCELLED';`
  },
  {
    name: "Subquery Anti-Pattern",
    query: `SELECT c.name, c.city, c.email
FROM customers c
WHERE c.id IN (
    SELECT o.customer_id 
    FROM orders o 
    WHERE o.total_amount > 4000
)
ORDER BY c.name;`
  },
  {
    name: "Category Breakdown",
    query: `SELECT category, 
       COUNT(*) AS product_count, 
       ROUND(AVG(price), 2) AS avg_price, 
       MIN(price) AS min_price, 
       MAX(price) AS max_price
FROM products 
GROUP BY category;`
  }
];

const Analyzer = () => {
  const location = useLocation();
  const [query, setQuery] = useState(QUERY_TEMPLATES[0].query);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Feature 2: What-If Index Simulator State
  const [simulatingIdx, setSimulatingIdx] = useState(null);
  const [simResults, setSimResults] = useState({});
  const [simErrors, setSimErrors] = useState({});

  // Feature 3: AI Query Rewriter State
  const [rewriting, setRewriting] = useState(false);
  const [rewriteModalOpen, setRewriteModalOpen] = useState(false);
  const [rewriteData, setRewriteData] = useState(null);
  const [rewriteError, setRewriteError] = useState(null);

  // If navigated from Dashboard with a selected query
  useEffect(() => {
    if (location.state?.query) {
      setQuery(location.state.query);
    }
  }, [location.state]);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setExecutionResult(null);
    setSimResults({});
    setSimErrors({});
    try {
      const res = await analyzeQuery(query);
      setResult(res);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    setExecutionResult(null);
    setSimResults({});
    setSimErrors({});
    try {
      const res = await executeQuery(query);
      setExecutionResult(res);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Feature 2: Execute What-If Index Simulation
  const handleSimulateIndex = async (rec, idx) => {
    setSimulatingIdx(idx);
    setSimErrors(prev => ({ ...prev, [idx]: null }));
    try {
      const res = await simulateIndex(query, rec.sql);
      setSimResults(prev => ({ ...prev, [idx]: res }));
    } catch (err) {
      setSimErrors(prev => ({
        ...prev,
        [idx]: err.response?.data?.detail || err.message
      }));
    } finally {
      setSimulatingIdx(null);
    }
  };

  // Feature 3: Request AI SQL Rewrite
  const handleOpenRewrite = async () => {
    setRewriting(true);
    setRewriteError(null);
    setRewriteData(null);
    setRewriteModalOpen(true);
    try {
      const res = await rewriteQuery(query);
      setRewriteData(res);
    } catch (err) {
      setRewriteError(err.response?.data?.detail || err.message);
    } finally {
      setRewriting(false);
    }
  };

  const handleApplyRewrite = (optimizedSql) => {
    setQuery(optimizedSql);
    setRewriteModalOpen(false);
  };

  const opt = executionResult?.optimization || result?.optimization;

  return (
    <div className="flex flex-col h-full space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            SQL Query Analyzer & ML Predictor
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 font-semibold">
              Deep Features AI
            </span>
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Predict execution time, simulate index speedups in rollback transactions, and optimize queries with AI.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Feature 3 Trigger */}
          <button
            onClick={handleOpenRewrite}
            className="px-3.5 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-lg flex items-center text-sm font-semibold transition-all shadow-sm"
            title="Automatically rewrite and optimize SQL query anti-patterns"
          >
            <Wand2 className="w-4 h-4 mr-1.5 text-purple-600" />
            AI Optimize SQL
          </button>

          <button 
            onClick={handleAnalyze}
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center font-medium shadow-sm transition-all text-sm"
          >
            <Activity className="w-4 h-4 mr-1.5" />
            Predict Time
          </button>
          <button 
            onClick={handleExecute}
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 flex items-center font-medium shadow-sm transition-all text-sm"
          >
            <Play className="w-4 h-4 mr-1.5" />
            Execute & Validate
          </button>
        </div>
      </div>

      {/* Quick Templates Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-gray-400 font-semibold flex items-center gap-1">
          <Zap className="w-3.5 h-3.5 text-amber-500" /> Templates:
        </span>
        {QUERY_TEMPLATES.map((tmpl, idx) => (
          <button
            key={idx}
            onClick={() => setQuery(tmpl.query)}
            className="px-2.5 py-1 bg-gray-100 hover:bg-indigo-50 hover:text-indigo-600 text-gray-600 rounded-md border border-gray-200 transition-all whitespace-nowrap"
          >
            {tmpl.name}
          </button>
        ))}
      </div>

      {/* Monaco SQL Editor */}
      <div className="h-64 border border-gray-300 rounded-xl overflow-hidden shadow-sm">
        <Editor
          height="100%"
          defaultLanguage="sql"
          value={query}
          onChange={(val) => setQuery(val || '')}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            padding: { top: 12, bottom: 12 }
          }}
        />
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 flex items-start shadow-sm">
          <AlertCircle className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0 text-red-500" />
          <p>{error}</p>
        </div>
      )}

      {/* Primary Analytics Cards */}
      {(result || executionResult) && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Postgres Planner Cost */}
          <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-3 text-gray-500">
              <span className="text-xs font-bold uppercase tracking-wider">PostgreSQL Planner</span>
              <Database className="w-4 h-4 text-gray-400" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {(result?.postgres_estimated_cost || executionResult?.postgres_estimated_cost || 0).toLocaleString()}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Estimated rows: {(result?.postgres_estimated_rows || executionResult?.postgres_estimated_rows || 0).toLocaleString()}
            </p>
          </div>

          {/* Card 2: ML Predicted Time */}
          <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-3 text-indigo-600">
              <span className="text-xs font-bold uppercase tracking-wider">ML Prediction</span>
              <Activity className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold text-indigo-600">
              {(result?.predicted_execution_time_ms || executionResult?.ml_prediction_ms || 0).toFixed(2)} ms
            </div>
            <div className="mt-2">
              <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded-full ${
                (result?.performance_category || executionResult?.performance_category) === 'LOW' ? 'bg-emerald-100 text-emerald-800' :
                (result?.performance_category || executionResult?.performance_category) === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                'bg-red-100 text-red-800'
              }`}>
                {result?.performance_category || executionResult?.performance_category || 'UNKNOWN'} Latency
              </span>
            </div>
          </div>

          {/* Card 3: Actual Execution & Accuracy */}
          <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-3 text-emerald-600">
              <span className="text-xs font-bold uppercase tracking-wider">Actual Database Run</span>
              <Play className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-emerald-700">
              {executionResult ? `${executionResult.actual_execution_time_ms.toFixed(2)} ms` : '--'}
            </div>
            {executionResult ? (
              <div className="flex items-center gap-1.5 mt-2 text-xs">
                <span className="text-gray-500">Error:</span>
                <span className={`font-bold px-1.5 py-0.5 rounded ${
                  executionResult.prediction_error_percent <= 10 ? 'bg-emerald-100 text-emerald-800' :
                  executionResult.prediction_error_percent <= 25 ? 'bg-blue-100 text-blue-800' :
                  'bg-amber-100 text-amber-800'
                }`}>
                  {executionResult.prediction_error_percent.toFixed(2)}%
                </span>
                {executionResult.prediction_error_percent <= 10 && (
                  <span className="text-emerald-600 font-semibold">(&lt;10% target met!)</span>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-400 mt-2">Click "Execute & Validate" to benchmark</p>
            )}
          </div>

          {/* Card 4: Buffer Cache & RAM Hits */}
          <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-3 text-sky-600">
              <span className="text-xs font-bold uppercase tracking-wider">Cache & Memory Hit</span>
              <HardDrive className="w-4 h-4 text-sky-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {opt?.cache_metrics ? `${opt.cache_metrics.cache_hit_ratio_percent}%` : '100%'}
            </div>
            <div className="mt-2 text-xs text-gray-500 truncate">
              {opt?.cache_metrics?.storage_source || 'RAM Buffer Cache'}
            </div>
          </div>
        </div>
      )}

      {/* Advanced Optimization & Index Advisor Section */}
      {opt && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Index Recommendations Column with Feature 2 Simulator */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
            <div className="flex justify-between items-center border-b pb-3">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-600" />
                Automated Index & Tuning Advisor
              </h2>
              <span className="text-xs text-gray-400 font-medium">What-If Transactional Simulator Enabled</span>
            </div>

            {opt.recommendations && opt.recommendations.length > 0 ? (
              <div className="space-y-4">
                {opt.recommendations.map((rec, idx) => {
                  const sim = simResults[idx];
                  const isSimulating = simulatingIdx === idx;
                  const simErr = simErrors[idx];

                  return (
                    <div key={idx} className="p-4 rounded-xl border border-indigo-100 bg-indigo-50/40 space-y-3">
                      <div className="flex justify-between items-start gap-2">
                        <div>
                          <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-200 text-indigo-800 uppercase">
                            {rec.severity} Priority
                          </span>
                          <p className="text-sm font-semibold text-gray-900 mt-1">
                            {rec.description}
                          </p>
                        </div>
                        <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded whitespace-nowrap">
                          {rec.estimated_speedup}
                        </span>
                      </div>

                      {/* SQL Code Box with Action Buttons */}
                      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 bg-gray-900 text-gray-100 p-2.5 rounded-lg text-xs font-mono">
                        <code className="truncate">{rec.sql}</code>
                        <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-auto">
                          {/* Feature 2: Simulate Button */}
                          {rec.sql.startsWith("CREATE INDEX") && (
                            <button
                              onClick={() => handleSimulateIndex(rec, idx)}
                              disabled={isSimulating}
                              className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-gray-950 font-sans font-bold text-[11px] rounded flex items-center transition-all disabled:opacity-50"
                              title="Test this index in a non-destructive rollback transaction to measure real speedup"
                            >
                              {isSimulating ? (
                                <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                              ) : (
                                <Zap className="w-3 h-3 mr-1 fill-current" />
                              )}
                              {isSimulating ? "Simulating..." : "Simulate Speedup"}
                            </button>
                          )}

                          <button
                            onClick={() => handleCopy(rec.sql, idx)}
                            className="p-1 text-gray-400 hover:text-white transition-colors"
                            title="Copy SQL to Clipboard"
                          >
                            {copiedIndex === idx ? (
                              <Check className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Feature 2: Inline Simulation Results Card */}
                      {simErr && (
                        <div className="p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200 flex items-center gap-1.5">
                          <AlertCircle className="w-4 h-4 text-red-500" />
                          <span>Simulation failed: {simErr}</span>
                        </div>
                      )}

                      {sim && (
                        <div className="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 border-2 border-emerald-300 rounded-xl space-y-3 shadow-sm animate-fadeIn">
                          <div className="flex justify-between items-center">
                            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> What-If Simulation Result
                            </span>
                            <span className="text-xs px-2 py-0.5 bg-emerald-600 text-white font-bold rounded-full">
                              ⚡ {sim.speedup_ratio} FASTER ({sim.percentage_drop}% Latency Drop)
                            </span>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                            <div className="bg-white/80 p-2 rounded border border-emerald-100">
                              <span className="text-gray-500 block">Before Index</span>
                              <span className="font-bold text-gray-800">{sim.before_time_ms} ms</span>
                              <span className="text-[10px] text-gray-400 block font-mono">({sim.before_node_type})</span>
                            </div>
                            <div className="bg-white/80 p-2 rounded border border-emerald-200 bg-emerald-50/50">
                              <span className="text-emerald-700 font-semibold block">With Index</span>
                              <span className="font-bold text-emerald-800">{sim.after_time_ms} ms</span>
                              <span className="text-[10px] text-emerald-600 block font-mono">({sim.after_node_type})</span>
                            </div>
                            <div className="bg-white/80 p-2 rounded border border-emerald-100">
                              <span className="text-gray-500 block">Time Saved</span>
                              <span className="font-bold text-indigo-700">{sim.time_saved_ms} ms</span>
                            </div>
                            <div className="bg-white/80 p-2 rounded border border-emerald-100">
                              <span className="text-gray-500 block">Planner Cost</span>
                              <span className="font-bold text-gray-800">{sim.before_cost} → {sim.after_cost}</span>
                            </div>
                          </div>

                          <p className="text-[11px] text-emerald-700 italic">
                            ✓ Verified inside an isolated test transaction and automatically rolled back. Schema remains clean.
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-100 text-sm flex items-center gap-2">
                <Check className="w-5 h-5 text-emerald-600" />
                <span>No missing indexes detected. The query already makes optimal use of existing indexes.</span>
              </div>
            )}

            {/* Anti-Patterns & Bottlenecks */}
            {opt.anti_patterns && opt.anti_patterns.length > 0 && (
              <div className="pt-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-amber-700 mb-2 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600" /> Detected SQL Anti-Patterns
                </h3>
                <div className="space-y-2">
                  {opt.anti_patterns.map((ap, idx) => (
                    <div key={idx} className="p-3 bg-amber-50/60 border border-amber-200 rounded-lg text-xs text-amber-900">
                      <div className="font-semibold">{ap.title}</div>
                      <div className="text-amber-700 mt-0.5">{ap.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Cloud Compute Cost & ROI Calculator Column */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 border-b pb-3">
              <DollarSign className="w-5 h-5 text-emerald-600" />
              Cloud Cost & ROI at Scale
            </h2>
            <p className="text-xs text-gray-500">
              Projected AWS RDS / GCP Cloud SQL compute charges based on 100,000 queries per day.
            </p>

            <div className="space-y-3 pt-1">
              <div className="p-3 bg-gray-50 rounded-lg flex justify-between items-center">
                <span className="text-xs text-gray-600">Monthly Run Cost:</span>
                <span className="text-base font-bold text-gray-900">
                  ${opt.cost_estimation?.monthly_cloud_cost_100k_daily || '0.00'}/mo
                </span>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg flex justify-between items-center">
                <span className="text-xs text-gray-600">Annual Projection:</span>
                <span className="text-base font-bold text-gray-900">
                  ${opt.cost_estimation?.annual_cloud_cost || '0.00'}/yr
                </span>
              </div>

              {opt.cost_estimation?.potential_monthly_savings > 0 && (
                <div className="p-3.5 bg-emerald-50 border border-emerald-100 rounded-xl">
                  <div className="flex items-center justify-between text-xs font-semibold text-emerald-800">
                    <span className="flex items-center gap-1">
                      <TrendingDown className="w-4 h-4 text-emerald-600" /> Potential Savings:
                    </span>
                    <span className="text-sm font-bold text-emerald-700">
                      ${opt.cost_estimation.potential_monthly_savings}/mo ({opt.cost_estimation.savings_percentage}%)
                    </span>
                  </div>
                  <p className="text-[11px] text-emerald-600 mt-1">
                    Applying recommended indexes will reduce query execution to sub-5ms, slashing database CPU credits.
                  </p>
                </div>
              )}
            </div>

            {/* Deep Feature Highlights */}
            <div className="pt-2 border-t border-gray-100">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2 flex items-center gap-1">
                <Layers className="w-3.5 h-3.5" /> Scanned vs Materialized Data
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-gray-50 p-2 rounded">
                  <span className="text-gray-500 block">Total Scanned:</span>
                  <span className="font-bold text-gray-800">
                    {(executionResult?.features?.total_scanned_rows || result?.features?.total_scanned_rows || 0).toLocaleString()} rows
                  </span>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <span className="text-gray-500 block">Max Intermediate:</span>
                  <span className="font-bold text-gray-800">
                    {(executionResult?.features?.max_intermediate_rows || result?.features?.max_intermediate_rows || 0).toLocaleString()} rows
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Visual Execution Plan Tree with Hotspot Highlighting */}
      {executionResult?.plan && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-[480px] flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-600" />
                Interactive Visual Query Plan & Hotspots
              </h2>
              <p className="text-xs text-gray-500">
                Nodes are color-coded in real time: red indicates CPU/IO bottlenecks taking &gt;40% of runtime.
              </p>
            </div>
          </div>
          <div className="flex-1 border border-gray-200 rounded-xl overflow-hidden">
            <PlanVisualizer plan={executionResult.plan} />
          </div>
        </div>
      )}

      {/* Feature 3: AI Query Rewriter Modal / Drawer */}
      {rewriteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4">
          <div className="bg-white w-full max-w-4xl rounded-2xl shadow-2xl border border-gray-200 overflow-hidden flex flex-col max-h-[90vh] animate-fadeIn">
            {/* Modal Header */}
            <div className="p-5 border-b border-gray-200 flex justify-between items-center bg-gray-50">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-purple-100 text-purple-700">
                  <Wand2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900">AI Intelligent SQL Query Rewriter</h3>
                  <p className="text-xs text-gray-500">
                    Rule-based query transformer removing anti-patterns, eliminating redundant sorts, and optimizing projections.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setRewriteModalOpen(false)}
                className="p-1.5 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {rewriting ? (
                <div className="py-16 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-purple-600 animate-spin mx-auto" />
                  <p className="text-sm font-semibold text-gray-700">Analyzing syntax and generating optimized SQL...</p>
                </div>
              ) : rewriteError ? (
                <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm">
                  {rewriteError}
                </div>
              ) : rewriteData ? (
                <div className="space-y-6">
                  {/* Improvements List */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">
                      Optimizations Applied ({rewriteData.improvements.length})
                    </h4>
                    {rewriteData.improvements.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {rewriteData.improvements.map((imp, idx) => (
                          <div key={idx} className="p-3 bg-purple-50/60 border border-purple-200 rounded-xl text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-purple-900">{imp.rule}</span>
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                imp.impact === 'HIGH' ? 'bg-red-100 text-red-800' :
                                imp.impact === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {imp.impact} Impact
                              </span>
                            </div>
                            <p className="text-gray-600 leading-relaxed">{imp.description}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 bg-emerald-50 text-emerald-800 rounded-xl border border-emerald-200 text-sm flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                        <span>This query already adheres to optimal SQL patterns! No anti-patterns detected.</span>
                      </div>
                    )}
                  </div>

                  {/* Cost Speedup Indicator if present */}
                  {rewriteData.estimated_speedup && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs">
                      <span className="text-emerald-800 font-semibold flex items-center gap-1.5">
                        <Gauge className="w-4 h-4 text-emerald-600" /> Planner Cost Reduction:
                      </span>
                      <span className="font-bold text-emerald-700">
                        {rewriteData.original_cost} → {rewriteData.optimized_cost} ({rewriteData.estimated_speedup})
                      </span>
                    </div>
                  )}

                  {/* Side-by-Side Comparison */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs font-bold text-gray-500 uppercase mb-2 flex items-center justify-between">
                        <span>Original SQL</span>
                        <span className="text-[11px] text-gray-400">Before</span>
                      </div>
                      <pre className="p-3 bg-gray-900 text-gray-300 font-mono text-xs rounded-xl overflow-x-auto h-48 border border-gray-800">
                        <code>{rewriteData.original_query}</code>
                      </pre>
                    </div>

                    <div>
                      <div className="text-xs font-bold text-purple-700 uppercase mb-2 flex items-center justify-between">
                        <span>Optimized SQL</span>
                        <span className="text-[11px] text-purple-600 font-bold">Recommended</span>
                      </div>
                      <pre className="p-3 bg-purple-950/90 text-purple-100 font-mono text-xs rounded-xl overflow-x-auto h-48 border border-purple-800/80">
                        <code>{rewriteData.optimized_query}</code>
                      </pre>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setRewriteModalOpen(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-100 font-medium"
              >
                Close
              </button>
              {rewriteData?.has_changes && (
                <button
                  onClick={() => handleApplyRewrite(rewriteData.optimized_query)}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 shadow-sm transition-all"
                >
                  <Sparkles className="w-4 h-4" /> Apply Optimized SQL to Editor
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analyzer;
