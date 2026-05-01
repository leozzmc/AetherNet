"use client";

interface DemoOverlayProps {
  step: any;
}

export default function DemoOverlay({ step }: DemoOverlayProps) {
  if (!step) return null;

  return (
    <div className="absolute bottom-6 left-6 bg-slate-900/80 backdrop-blur-md border border-slate-700 rounded-lg px-5 py-3 max-w-md shadow-2xl z-10 pointer-events-none transition-all duration-500">
      <div className="flex items-center gap-2 mb-1">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
        <div className="text-xs text-cyan-400/80 font-mono tracking-widest uppercase">
          System Narrative
        </div>
      </div>
      <div className="text-sm text-slate-100 font-medium leading-relaxed drop-shadow-md">
        {step.message || step.label}
      </div>
    </div>
  );
}