"use client"

interface DecisionPanelProps {
  decisions: {
    legacy: string;
    balanced: string;
    adaptive: string;
  }
}

export default function DecisionPanel({ decisions }: DecisionPanelProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
      <h2 className="text-lg font-semibold mb-4 text-gray-800">Routing Decisions</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-3 rounded shadow-sm border border-gray-100">
          <div className="text-xs text-gray-500 font-medium uppercase mb-1">Legacy Baseline</div>
          <div className="font-mono text-lg">{decisions.legacy}</div>
        </div>
        <div className="bg-white p-3 rounded shadow-sm border border-gray-100">
          <div className="text-xs text-gray-500 font-medium uppercase mb-1">Phase-6 Balanced</div>
          <div className="font-mono text-lg">{decisions.balanced}</div>
        </div>
        <div className="bg-white p-3 rounded shadow-sm border border-gray-100">
          <div className="text-xs text-gray-500 font-medium uppercase mb-1">Phase-6 Adaptive</div>
          <div className="font-mono text-lg">{decisions.adaptive}</div>
        </div>
      </div>
    </div>
  )
}