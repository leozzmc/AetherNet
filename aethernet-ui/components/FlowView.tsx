"use client";

import { useMemo, useEffect } from "react";
import { ReactFlow, Background, Controls, useReactFlow, ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { mapToFlow } from "./flowMapper";
import DemoOverlay from "./DemoOverlay";

interface FlowViewProps {
  scenario: any;
  step?: any;
}

function FlowContent({ scenario, step }: FlowViewProps) {
  const { nodes, edges } = useMemo(() => mapToFlow(scenario, step), [scenario, step]);
  const rf = useReactFlow();

  // Wave-112: Cinematic Camera Movement
  useEffect(() => {
    // Backend can specify a focus_node, otherwise fallback to the most recently highlighted node
    const targetNodeId = step?.focus_node || step?.highlight_nodes?.slice(-1)[0];
    if (!targetNodeId) return;

    const node = nodes.find((n) => n.id === targetNodeId);
    if (!node) return;

    // Smoothly pan camera to the active node
    rf.setCenter(node.position.x + 120, node.position.y + 40, {
      zoom: 1.15,
      duration: 800,
    });
  }, [step, nodes, rf]);

  return (
    <>
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        fitView 
        fitViewOptions={{ padding: 0.2, maxZoom: 1.2 }}
        proOptions={{ hideAttribution: true }}
        className="bg-transparent"
      >
        <Background color="#334155" gap={24} size={1} />
        <Controls className="bg-slate-900 border-slate-700 fill-slate-300" />
      </ReactFlow>
      <DemoOverlay step={step} />
    </>
  );
}

// Wrapper necessary to provide ReactFlow context to the useReactFlow hook inside
export default function FlowView(props: FlowViewProps) {
  return (
    <div className="h-[550px] w-full rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative bg-black/60 backdrop-blur-sm">
      <ReactFlowProvider>
        <FlowContent {...props} />
      </ReactFlowProvider>
    </div>
  );
}