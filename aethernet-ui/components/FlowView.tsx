"use client";

import { useMemo } from "react";
import { ReactFlow, Background } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { mapToFlow } from "./flowMapper";

interface FlowViewProps {
  scenario: any;
  activeStep?: any;
}

export default function FlowView({ scenario, activeStep }: FlowViewProps) {
  const stepId = activeStep?.id;

  const { nodes, edges } = useMemo(() => {
    return mapToFlow(scenario, activeStep);
  }, [scenario, stepId]); // ⭐ 只用 stepId

  return (
    <div className="h-[450px] w-full bg-slate-950 rounded-lg overflow-hidden border border-slate-800">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.2, maxZoom: 1 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#334155" gap={20} size={2} />
      </ReactFlow>
    </div>
  );
}