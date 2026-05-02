"use client";

interface DecisionPanelProps {
  decisions: {
    legacy?: string;
    phase6_balanced?: string;
    phase6_adaptive?: string;
  };
}

export default function DecisionPanel({ decisions }: DecisionPanelProps) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-md">
      <h3 className="text-sm font-mono text-slate-400 mb-4 uppercase tracking-widest">
        Routing Decisions
      </h3>

      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-xs text-slate-500">Legacy</div>
          <div className="text-xl font-bold text-rose-400">
            {decisions?.legacy || "-"}
          </div>
        </div>

        <div>
          <div className="text-xs text-slate-500">Phase-6</div>
          <div className="text-xl font-bold text-emerald-400">
            {decisions?.phase6_balanced || "-"}
          </div>
        </div>

        <div>
          <div className="text-xs text-slate-500">Adaptive</div>
          <div className="text-xl font-bold text-cyan-400">
            {decisions?.phase6_adaptive || "-"}
          </div>
        </div>
      </div>
    </div>
  );
}