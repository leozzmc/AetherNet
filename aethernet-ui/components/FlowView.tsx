"use client";

import { useMemo, useEffect, useRef } from "react";
import { ReactFlow, Background, Controls, useReactFlow, ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { mapToFlow } from "./flowMapper";
import DemoOverlay from "./DemoOverlay";

interface FlowViewProps {
  scenario: any;
  step?: any;
  isPresentation?: boolean;
}

function FlowContent({ scenario, step, isPresentation }: FlowViewProps) {
  const { nodes, edges } = useMemo(() => mapToFlow(scenario, step), [scenario, step]);
  const rf = useReactFlow();
  
  // Wave-113: Camera Jitter Fix
  const lastStepRef = useRef<string | null>(null);

  useEffect(() => {
    if (!step?.id || step.id === lastStepRef.current) return;
    lastStepRef.current = step.id;

    const targetNodeId = step?.focus_node || step?.highlight_nodes?.slice(-1)[0];
    if (!targetNodeId) return;

    const node = nodes.find((n) => n.id === targetNodeId);
    if (!node) return;

    rf.setCenter(node.position.x + 120, node.position.y + 40, {
      zoom: 1.15,
      duration: 800,
    });
  }, [step?.id, nodes, rf]);

  return (
    <>
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        fitView 
        fitViewOptions={{ padding: 0.2, maxZoom: 1.2 }}
        proOptions={{ hideAttribution: true }}
        className="bg-transparent"
        // Disable interactions during presentation mode for clean recording
        nodesDraggable={!isPresentation}
        nodesConnectable={false}
        elementsSelectable={!isPresentation}
      >
        <Background color="#334155" gap={24} size={1} />
        {!isPresentation && <Controls className="bg-slate-900 border-slate-700 fill-slate-300" />}
      </ReactFlow>
      <DemoOverlay step={step} />
    </>
  );
}

export default function FlowView(props: FlowViewProps) {
  // Wave-113: Expand height if in presentation mode
  const heightClass = props.isPresentation ? "h-[85vh]" : "h-[550px]";
  
  return (
    <div className={`${heightClass} w-full rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative bg-black/60 backdrop-blur-sm transition-all duration-700`}>
      <ReactFlowProvider>
        <FlowContent {...props} />
      </ReactFlowProvider>
    </div>
  );
}