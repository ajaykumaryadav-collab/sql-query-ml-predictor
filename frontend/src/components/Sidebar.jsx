import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Database, Activity, History } from 'lucide-react';

const SidebarItem = ({ to, icon: Icon, label }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <Link
      to={to}
      className={`flex items-center px-4 py-3 mb-2 rounded-lg transition-colors ${
        isActive 
          ? 'bg-blue-600 text-white' 
          : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      <Icon className="w-5 h-5 mr-3" />
      <span className="font-medium">{label}</span>
    </Link>
  );
};

const Sidebar = () => {
  return (
    <div className="w-64 h-screen bg-white border-r border-gray-200 flex flex-col fixed left-0 top-0">
      <div className="p-6">
        <h1 className="text-xl font-bold text-gray-800 flex items-center">
          <Database className="w-6 h-6 mr-2 text-blue-600" />
          SQL ML Predictor
        </h1>
      </div>
      <div className="flex-1 px-4 mt-6">
        <SidebarItem to="/" icon={LayoutDashboard} label="Dashboard" />
        <SidebarItem to="/analyzer" icon={Activity} label="Query Analyzer" />
        <SidebarItem to="/history" icon={History} label="History" />
        <SidebarItem to="/metrics" icon={Database} label="Model Metrics" />
      </div>
    </div>
  );
};

export default Sidebar;
