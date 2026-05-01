import { Node, Edge } from "@xyflow/react";

function isHighlighted(id: string, highlightList: string[] = []) {
  // If no highlight list is provided, default to showing everything (static mode)
  if (!highlightList || highlightList.length === 0) return true;
  return highlightList.includes(id);
}

function getColor(status: string) {
  switch (status) {
    case "success": return "#10b981"; // Emerald
    case "error": return "#ef4444";   // Rose
    case "warning": return "#f59e0b"; // Amber
    case "info":
    default: return "#3b82f6";        // Blue
  }
}

export function mapToFlow(presentation: any, activeStep: any = null) {
  const highlightNodes = activeStep?.highlight_nodes || [];
  const highlightEdges = activeStep?.highlight_edges || [];

  const nodes: Node[] = presentation.nodes.map((n: any) => {
    const status = n.data.status;
    const highlighted = isHighlighted(n.id, highlightNodes);
    
    return {
      id: n.id,
      position: n.position,
      data: n.data,
      type: n.type,
      style: {
        background: highlighted ? "#ffffff" : "#f1f5f9",
        color: highlighted ? "#1e293b" : "#94a3b8",
        border: `2px solid ${highlighted ? getColor(status) : "#cbd5e1"}`,
        borderRadius: "8px",
        padding: "12px",
        fontWeight: highlighted ? "600" : "400",
        width: 240,
        boxShadow: highlighted ? "0 10px 15px -3px rgb(0 0 0 / 0.1)" : "none",
        opacity: highlighted ? 1 : 0.4,
        transition: "all 0.5s ease-in-out", // Cinematic smooth transition
      },
    };
  });

  const edges: Edge[] = presentation.edges.map((e: any) => {
    const status = e.data.status;
    const highlighted = isHighlighted(e.id, highlightEdges);
    
    return {
      id: e.id,
      source: e.source,
      target: e.target,
      // Only animate edges if they are highlighted AND actively showing a routing action
      animated: highlighted && (status !== "info"),
      style: {
        stroke: highlighted ? getColor(status) : "#e2e8f0",
        strokeWidth: highlighted ? 3 : 1.5,
        opacity: highlighted ? 1 : 0.2,
        transition: "all 0.5s ease-in-out",
      },
    };
  });

  return { nodes, edges };
}