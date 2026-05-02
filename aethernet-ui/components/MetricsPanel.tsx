"use client";

interface MetricsPanelProps {
  metrics: {
    nodes?: number;
    edges?: number;
    modes?: number;
    diverged?: boolean;
  };
}

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-md">
      <h3 className="text-sm font-mono text-slate-400 mb-4 uppercase tracking-widest">
        Topology Metrics
      </h3>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-slate-500">Nodes</div>
          <div className="text-lg font-bold text-white">
            {metrics?.nodes ?? "-"}
          </div>
        </div>

        <div>
          <div className="text-slate-500">Edges</div>
          <div className="text-lg font-bold text-white">
            {metrics?.edges ?? "-"}
          </div>
        </div>

        <div>
          <div className="text-slate-500">Modes</div>
          <div className="text-lg font-bold text-white">
            {metrics?.modes ?? "-"}
          </div>
        </div>

        <div>
          <div className="text-slate-500">Divergence</div>
          <div
            className={`text-lg font-bold ${
              metrics?.diverged ? "text-emerald-400" : "text-slate-300"
            }`}
          >
            {metrics?.diverged ? "Detected" : "None"}
          </div>
        </div>
      </div>
    </div>
  );
}