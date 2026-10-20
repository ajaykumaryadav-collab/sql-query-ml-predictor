import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Analyzer from './pages/Analyzer';
import QueryHistory from './pages/History';
import Metrics from './pages/Metrics';

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-50 font-sans">
        <Sidebar />
        <div className="flex-1 ml-64 overflow-auto">
          <div className="p-8 max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/analyzer" element={<Analyzer />} />
              <Route path="/history" element={<QueryHistory />} />
              <Route path="/metrics" element={<Metrics />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default App;
