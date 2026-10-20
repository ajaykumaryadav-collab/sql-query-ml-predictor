import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

const parsePlanToNodesAndEdges = (plan) => {
  const nodes = [];
  const edges = [];
  let idCounter = 0;

  const totalPlanCost = plan?.["Total Cost"] || 1;
  const totalPlanTime = plan?.["Actual Total Time"] || 0;

  const traverse = (node, parentId = null, x = 300, y = 50, level = 0) => {
    if (!node) return;
    
    const id = `node_${idCounter++}`;
    
    const nodeCost = node["Total Cost"] || 0;
    const nodeTime = node["Actual Total Time"] || 0;
    const nodeType = node["Node Type"] || "Node";
    const relation = node["Relation Name"] || "";
    
    // Calculate hotspot intensity percentage
    let intensityPct = 0;
    if (totalPlanTime > 0 && nodeTime > 0) {
      intensityPct = (nodeTime / totalPlanTime) * 100;
    } else if (totalPlanCost > 0) {
      intensityPct = (nodeCost / totalPlanCost) * 100;
    }

    // Determine color coding & hotspot badge
    let borderClass = "border-emerald-400 bg-emerald-50/60";
    let badgeClass = "bg-emerald-100 text-emerald-800";
    let badgeLabel = "Fast";

    if (intensityPct >= 40 || (nodeType === "Seq Scan" && (node["Plan Rows"] || 0) > 2000)) {
      borderClass = "border-red-500 bg-red-50 ring-2 ring-red-300 shadow-md";
      badgeClass = "bg-red-100 text-red-800 font-bold";
      badgeLabel = "Critical Hotspot";
    } else if (intensityPct >= 15) {
      borderClass = "border-amber-400 bg-amber-50/80 shadow-sm";
      badgeClass = "bg-amber-100 text-amber-800 font-semibold";
      badgeLabel = "Moderate Load";
    }

    const label = (
      <div className={`text-xs p-2.5 text-center border-2 rounded-xl shadow-sm w-48 transition-all ${borderClass}`}>
        <div className="flex justify-between items-center mb-1 pb-1 border-b border-gray-200">
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${badgeClass}`}>
            {badgeLabel}
          </span>
          <span className="text-[10px] text-gray-500 font-mono">
            {intensityPct.toFixed(0)}% load
          </span>
        </div>
        
        <div className="font-bold text-gray-800 text-sm truncate">
          {nodeType}
        </div>
        
        {relation && (
          <div className="text-[11px] text-blue-700 font-semibold truncate mb-1">
            on {relation}
          </div>
        )}
        
        <div className="grid grid-cols-2 gap-1 text-[11px] text-gray-600 mt-1 pt-1 border-t border-gray-200/60">
          <div>Cost: <span className="font-semibold text-gray-800">{nodeCost.toFixed(0)}</span></div>
          <div>Rows: <span className="font-semibold text-gray-800">{node["Plan Rows"]?.toLocaleString() || 0}</span></div>
        </div>

        {node["Actual Total Time"] !== undefined && (
          <div className="text-[11px] text-indigo-700 font-bold mt-1 bg-indigo-50/60 py-0.5 rounded">
            Time: {node["Actual Total Time"].toFixed(2)} ms
          </div>
        )}
      </div>
    );

    nodes.push({
      id,
      position: { x, y },
      data: { label },
      type: 'default'
    });

    if (parentId) {
      edges.push({
        id: `e_${parentId}_${id}`,
        source: parentId,
        target: id,
        animated: intensityPct >= 20,
        style: { stroke: intensityPct >= 40 ? '#ef4444' : intensityPct >= 15 ? '#f59e0b' : '#10b981', strokeWidth: 2 }
      });
    }

    const plans = node["Plans"] || [];
    const childWidth = 240;
    const startX = x - ((plans.length - 1) * childWidth) / 2;

    plans.forEach((child, idx) => {
      traverse(child, id, startX + idx * childWidth, y + 175, level + 1);
    });
  };

  traverse(plan);
  return { nodes, edges };
};

const PlanVisualizer = ({ plan }) => {
  const { nodes, edges } = useMemo(() => parsePlanToNodesAndEdges(plan), [plan]);

  return (
    <div className="relative h-full w-full">
      {/* Legend Badge Bar */}
      <div className="absolute top-2 right-2 z-10 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg p-2 text-xs flex items-center space-x-3 shadow-sm">
        <span className="font-semibold text-gray-600">Hotspot Intensity:</span>
        <span className="inline-flex items-center text-red-700">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 mr-1"></span> Critical (&gt;40%)
        </span>
        <span className="inline-flex items-center text-amber-700">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 mr-1"></span> Moderate (15-40%)
        </span>
        <span className="inline-flex items-center text-emerald-700">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 mr-1"></span> Efficient (&lt;15%)
        </span>
      </div>

      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        fitView 
        panOnScroll={true}
        zoomOnScroll={false}
      >
        <Background gap={16} size={1} color="#e5e7eb" />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default PlanVisualizer;
