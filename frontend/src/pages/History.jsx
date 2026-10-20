import React, { useState, useEffect } from 'react';
import { getHistory } from '../services/api';
import { Clock, Zap } from 'lucide-react';

const QueryHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getHistory();
        setHistory(data);
      } catch (error) {
        console.error("Failed to fetch history", error);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (loading) return <div>Loading history...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Query History</h1>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SQL Query</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Predicted (ms)</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actual (ms)</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {history.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(row.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 text-sm font-mono text-gray-800 max-w-xs truncate" title={row.query_text}>
                  {row.query_text}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {row.query_type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {row.ml_predicted_time_ms?.toFixed(2) || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {row.actual_execution_time_ms?.toFixed(2) || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    row.performance_category === 'LOW' ? 'bg-green-100 text-green-800' :
                    row.performance_category === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {row.performance_category || 'UNKNOWN'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {history.length === 0 && (
          <div className="p-6 text-center text-gray-500">No query history found.</div>
        )}
      </div>
    </div>
  );
};

export default QueryHistory;
