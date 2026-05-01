import { Node, Edge } from "@xyflow/react";

function isHighlighted(id: string, highlightList: string[] = []) {
  if (!highlightList || highlightList.length === 0) return true;
  return highlightList.includes(id);
}

function getStatusColor(status: string) {
  switch (status) {
    case "success": return "#22c55e"; // Green
    case "error": return "#ef4444";   // Red
    case "warning": return "#f59e0b"; // Amber
    case "info":
    default: return "#38bdf8";        // Cyan/Blue
  }
}

export function mapToFlow(presentation: any, activeStep: any = null) {
  const highlightNodes = activeStep?.highlight_nodes || [];
  const highlightEdges = activeStep?.highlight_edges || [];
  const legacyPath = activeStep?.legacy_path || [];
  const phase6Path = activeStep?.phase6_path || [];

  const nodes: Node[] = presentation.nodes.map((n: any) => {
    const status = n.data.status;
    const highlighted = isHighlighted(n.id, highlightNodes);

    return {
      id: n.id,
      position: n.position,
      data: n.data,
      type: n.type,
      style: {
        background: highlighted ? "#0f172a" : "#020617", // slate-900 / slate-950
        color: highlighted ? "#f8fafc" : "#475569", // slate-50 / slate-600
        border: `2px solid ${highlighted ? getStatusColor(status) : "#1e293b"}`,
        borderRadius: "8px",
        padding: "12px",
        fontWeight: highlighted ? "600" : "400",
        width: 240,
        boxShadow: highlighted ? `0 0 20px -5px ${getStatusColor(status)}80` : "none",
        opacity: highlighted ? 1 : 0.3,
        transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)", 
      },
    };
  });

  const edges: Edge[] = presentation.edges.map((e: any) => {
    const status = e.data.status;
    const highlighted = isHighlighted(e.id, highlightEdges);
    const isLegacy = legacyPath.includes(e.id);
    const isPhase6 = phase6Path.includes(e.id);

    let strokeColor = "#334155"; // Default dim gray
    let strokeWidth = 1.5;
    let animated = false;

    if (highlighted) {
      if (isPhase6) {
        strokeColor = "#22c55e"; // Phase-6 safe path
        strokeWidth = 3;
        animated = true;
      } else if (isLegacy) {
        strokeColor = "#ef4444"; // Legacy vulnerable path
        strokeWidth = 3;
        animated = false;
      } else {
        strokeColor = getStatusColor(status);
        strokeWidth = 2.5;
        animated = status !== "info";
      }
    }

    return {
      id: e.id,
      source: e.source,
      target: e.target,
      animated,
      style: {
        stroke: strokeColor,
        strokeWidth,
        opacity: highlighted ? 1 : 0.15,
        transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
      },
    };
  });

  return { nodes, edges };
}