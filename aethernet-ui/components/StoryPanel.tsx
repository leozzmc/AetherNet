"use client";

interface StoryPanelProps {
  step: any;
  index: number;
  total: number;
}

function getBadgeStyle(step: any) {
  const status = step?.status ?? "info";

  switch (status) {
    case "success":
      return "bg-emerald-500/20 text-emerald-300";
    case "error":
      return "bg-rose-500/20 text-rose-300";
    case "warning":
      return "bg-amber-500/20 text-amber-300";
    default:
      return "bg-slate-700 text-slate-300";
  }
}

export default function StoryPanel({ step, index, total }: StoryPanelProps) {
  if (!step) return null;

  return (
    <div className="p-5 border border-slate-700 rounded-lg bg-slate-900 text-white shadow-xl min-h-[120px] transition-all duration-300">
      <div className="flex items-center justify-between">
        <div className="text-xs font-mono text-slate-400 uppercase tracking-widest">
          Telemetry Frame [ {index + 1} / {total} ]
        </div>

        <div className={`text-xs px-2 py-1 rounded-full font-mono ${getBadgeStyle(step)}`}>
          {step.label}
        </div>
      </div>

      <div className="mt-3 text-lg font-medium tracking-wide">
        {step.message}
      </div>
    </div>
  );
}