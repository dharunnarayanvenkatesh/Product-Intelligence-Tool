'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [insights, setInsights] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchInsights();
    fetchMetrics();
  }, []);

  const fetchInsights = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/insights/`);
      setInsights(res.data.insights);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/metrics/all`);
      setMetrics(res.data.metrics);
    } catch (err) {
      console.error(err);
    }
  };

  const handleQuery = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/query/ask`, { question: query });
      setAnswer(res.data.answer);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <h1 className="text-3xl font-bold mb-8">Product Intelligence</h1>

      <div className="mb-8">
        <h2 className="text-xl mb-4">Ask a Question</h2>
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-gray-900 border border-gray-700 rounded px-4 py-2"
            placeholder="Why did trial users churn last week?"
          />
          <button
            onClick={handleQuery}
            disabled={loading}
            className="bg-blue-600 px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Ask'}
          </button>
        </div>
        {answer && (
          <div className="mt-4 bg-gray-900 p-4 rounded">
            <p>{answer}</p>
          </div>
        )}
      </div>

      <div className="mb-8">
        <h2 className="text-xl mb-4">Active Insights ({insights.length})</h2>
        <div className="space-y-2">
          {insights.slice(0, 10).map((insight: any) => (
            <div key={insight.id} className="bg-gray-900 p-4 rounded">
              <div className="flex justify-between items-start mb-2">
                <span className="font-semibold">{insight.title}</span>
                <span className={`text-xs px-2 py-1 rounded ${
                  insight.severity === 'critical' ? 'bg-red-900' :
                  insight.severity === 'high' ? 'bg-orange-900' :
                  'bg-yellow-900'
                }`}>
                  {insight.severity}
                </span>
              </div>
              {insight.llm_explanation && (
                <p className="text-sm text-gray-400">{insight.llm_explanation}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl mb-4">Recent Metrics</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left p-2">Metric</th>
                <th className="text-left p-2">Type</th>
                <th className="text-right p-2">Value</th>
                <th className="text-left p-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {metrics.slice(0, 20).map((metric: any) => (
                <tr key={metric.id} className="border-b border-gray-800">
                  <td className="p-2">{metric.metric_name}</td>
                  <td className="p-2 text-gray-400">{metric.metric_type}</td>
                  <td className="p-2 text-right">{metric.value.toFixed(2)}</td>
                  <td className="p-2 text-gray-400">{new Date(metric.date).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}