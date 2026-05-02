"use client"

import { useState, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { usePresentation } from "@/hooks/usePresentation" // Update path if needed
import { useStoryPlayer } from "@/hooks/useStoryPlayer"   // Update path if needed
import ScenarioSelector from "@/components/ScenarioSelector"
import DecisionPanel from "@/components/DecisionPanel"
import MetricsPanel from "@/components/MetricsPanel"
import FlowView from "@/components/FlowView"

function DashboardContent() {
  const { data, error } = usePresentation()
  const [selected, setSelected] = useState<string | null>(null)
  
  // Wave-113: URL Params
  const params = useSearchParams()
  const isPresentation = params.get("mode") === "presentation"
  const isClean = params.get("clean") === "true"

  const scenarios = data?.scenarios || []
  const current = scenarios.find((s: any) => s.scenario_id === selected) || scenarios[0]
  
  // Pass presentation mode to auto-start
  const story = useStoryPlayer(current?.story_script || [], isPresentation)

  if (error) return <div className="p-6 text-red-500">Error loading data: {error}</div>
  if (!current) return <div className="p-6 text-slate-500 flex h-screen items-center justify-center">Initializing Telemetry...</div>

  const isDiverged = current.metrics?.diverged;

  // Wave-113: Export Artifact Function
  const handleExport = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `aethernet-payload-${current.scenario_id}.json`
    a.click()
  }

  return (
    <div 
      className="min-h-screen bg-slate-950 text-slate-200 p-6 md:p-8 font-sans selection:bg-cyan-500/30"
      style={{
        backgroundImage: "radial-gradient(circle at 1px 1px, #1e293b 1px, transparent 0)",
        backgroundSize: "28px 28px",
      }}
    >
      <div className={`mx-auto space-y-6 ${isPresentation ? 'max-w-[95%]' : 'max-w-6xl'}`}>
        
        {/* Render Header & Controls ONLY if not in presentation mode */}
        {!isPresentation && (
          <header className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-slate-800 pb-4 gap-4">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-white drop-shadow-sm">AetherNet</h1>
              <p className="text-xs text-cyan-500 mt-1 font-mono uppercase tracking-widest">Routing Intelligence Simulator</p>
            </div>
            
            <div className="flex items-center gap-4 bg-slate-900/50 p-3 rounded-lg border border-slate-800 backdrop-blur-md">
              <ScenarioSelector
                scenarios={scenarios}
                selected={current.scenario_id}
                onChange={setSelected}
              />
              <div className="flex gap-2">
                <button onClick={story.reset} className="px-3 py-1.5 text-xs font-mono text-slate-400 bg-slate-800 hover:bg-slate-700 rounded transition-colors">
                  RESET
                </button>
                <button onClick={story.next} disabled={story.playing} className="px-3 py-1.5 text-xs font-mono text-slate-400 bg-slate-800 hover:bg-slate-700 rounded transition-colors disabled:opacity-50">
                  STEP
                </button>
                <button onClick={() => story.setPlaying(!story.playing)} className={`px-4 py-1.5 text-xs font-mono font-bold rounded transition-colors shadow-lg ${story.playing ? "bg-rose-500/20 text-rose-400 border border-rose-500/50" : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 hover:bg-cyan-500/30"}`}>
                  {story.playing ? "❚❚ PAUSE" : "▶ AUTO"}
                </button>
                <button onClick={handleExport} className="px-3 py-1.5 text-xs font-mono text-slate-300 bg-indigo-500/20 border border-indigo-500/50 hover:bg-indigo-500/30 rounded transition-colors ml-2">
                  ↓ JSON
                </button>
              </div>
            </div>
          </header>
        )}

        {/* Cinematic Flow Area */}
        <section className="space-y-3">
          {/* Always show context banner to anchor the narrative */}
          <div className="px-2">
            <p className="text-sm font-mono text-slate-400">
              Scenario Context: <span className="text-cyan-400 uppercase font-bold">{current.scenario_id}</span>
              {" • "}
              <span className={isDiverged ? "text-emerald-400" : "text-slate-300"}>
                {isDiverged ? "Phase-6 intercepted and avoided compromised route." : "All routing modes converged to optimal path."}
              </span>
            </p>
          </div>

          <FlowView scenario={current} step={story.step} isPresentation={isPresentation} />
        </section>

        {/* Render Data Panels ONLY if clean mode is false */}
        {!(isPresentation && isClean) && (
          <section className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            <div className="md:col-span-1">
              <DecisionPanel decisions={current.decisions} />
            </div>
            <div className="md:col-span-2">
              <MetricsPanel metrics={current.metrics} />
            </div>
          </section>
        )}

      </div>
    </div>
  )
}

// Wrap in Suspense to satisfy Next.js static generation rules when using useSearchParams
export default function Page() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 flex items-center justify-center text-cyan-500 font-mono">Initializing Systems...</div>}>
      <DashboardContent />
    </Suspense>
  )
}