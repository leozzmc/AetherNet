import { Node, Edge } from "@xyflow/react";

export function mapToFlow(presentation: any) {
  const nodes: Node[] = (presentation.nodes || []).map((n: any, index: number) => {
    const status = n?.presentation?.status ?? n?.status ?? "info";

    return {
      id: n.id,
      position: n.position || { x: index * 280, y: 150 },
      data: {
        label: n?.presentation?.label ?? n?.label ?? n.id,
        status,
      },
      type: n.type === "input" || n.type === "output" ? n.type : "default",
      style: {
        background: "#ffffff",
        color: "#1e293b",
        border: `2px solid ${getColor(status)}`,
        borderRadius: "8px",
        padding: "12px",
        fontWeight: "500",
        width: 220,
      },
    };
  });

  const edges: Edge[] = (presentation.edges || []).map((e: any) => {
    // ⭐ 關鍵修正：兼容兩種 schema
    const status =
      e?.presentation?.status ??
      e?.status ??
      "info";

    return {
      id: e.id,
      source: e.source,
      target: e.target,
      animated: e.animated ?? (status === "success"),
      style: {
        stroke: getColor(status),
        strokeWidth: 2.5,
      },
    };
  });

  return { nodes, edges };
}

function getColor(status: string) {
  switch (status) {
    case "success":
      return "#10b981";
    case "error":
      return "#ef4444";
    case "warning":
      return "#f59e0b";
    default:
      return "#3b82f6";
  }
}