"use client";

import { useMemo } from "react";
import { ReactFlow, Background, Controls, MiniMap } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { mapToFlow } from "./flowMapper";

interface FlowViewProps {
  scenario: any;
}

export default function FlowView({ scenario }: FlowViewProps) {
  // 使用 useMemo 確保在切換 scenario 時才重新計算，優化 React Flow 效能
  const { nodes, edges } = useMemo(() => mapToFlow(scenario), [scenario]);

  return (
    <div className="h-[400px] w-full border border-gray-200 rounded-xl shadow-inner bg-slate-50 overflow-hidden relative">
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        fitView 
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background color="#cbd5e1" gap={16} />
        <Controls />
        <MiniMap nodeStrokeWidth={3} zoomable pannable />
      </ReactFlow>
    </div>
  );
}