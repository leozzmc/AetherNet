"use client";

interface DemoOverlayProps {
  step: any;
}

export default function DemoOverlay({ step }: DemoOverlayProps) {
  if (!step) return null;

  return (
    <div className="absolute bottom-8 left-8 bg-slate-900/85 backdrop-blur-md border border-slate-700 rounded-lg px-6 py-4 max-w-lg shadow-2xl z-10 pointer-events-none transition-opacity duration-500 opacity-100">
      <div className="flex items-center gap-2 mb-2">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
        <div className="text-xs text-cyan-400/90 font-mono tracking-widest uppercase">
          System Narrative
        </div>
      </div>
      <div className="text-[15px] text-slate-100 font-medium leading-relaxed drop-shadow-md">
        {step.message || step.label}
      </div>
    </div>
  );
}