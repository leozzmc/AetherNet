"use client"

interface MetricsPanelProps {
  metrics: {
    node_count: number;
    edge_count: number;
    diverged: boolean;
    evaluated_modes: number;
  }
}

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 mt-4">
      <h2 className="text-lg font-semibold mb-4 text-gray-800">Topology Metrics</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-3 rounded shadow-sm border border-gray-100">
          <div className="text-xs text-gray-500 font-medium uppercase">Flow Nodes</div>
          <div className="text-xl font-bold text-blue-600">{metrics.node_count}</div>
        </div>
        <div className="bg-white p-3 rounded shadow-sm border border-gray-100">
          <div className="text-xs text-gray-500 font-medium uppercase">Flow Edges</div>
          <div className="text-xl font-bold text-blue-600">{metrics.edge_count}</div>
        </div>
        <div className="bg-white p-3 rounded shadow-sm border border-gray-100">
          <div className="text-xs text-gray-500 font-medium uppercase">Divergence</div>
          <div className={`text-xl font-bold ${metrics.diverged ? 'text-red-600' : 'text-green-600'}`}>
            {metrics.diverged ? "Detected" : "None"}
          </div>
        </div>
        <div className="bg-white p-3 rounded shadow-sm border border-gray-100">
          <div className="text-xs text-gray-500 font-medium uppercase">Modes</div>
          <div className="text-xl font-bold text-gray-800">{metrics.evaluated_modes}</div>
        </div>
      </div>
    </div>
  )
}