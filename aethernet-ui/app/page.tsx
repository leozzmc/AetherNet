"use client"

import { useState } from "react"
import { usePresentation } from "@/components/usePresentation"
import { useStoryPlayer } from "@/components/useStoryPlayer"
import ScenarioSelector from "@/components/ScenarioSelector"
import FlowView from "@/components/FlowView"

export default function Page() {
  const { data, error } = usePresentation()
  const [selected, setSelected] = useState<string | null>(null)

  const scenarios = data?.scenarios || []
  const current = scenarios.find((s: any) => s.scenario_id === selected) || scenarios[0]
  const story = useStoryPlayer(current?.story_script || [])

  if (error) return <div className="p-6 text-red-500">Error loading data: {error}</div>
  if (!current) return <div className="p-6 text-slate-500 flex h-screen items-center justify-center">Initializing Telemetry...</div>

  const isDiverged = current.metrics?.diverged;

  return (
    <div 
      className="min-h-screen bg-slate-950 text-slate-200 p-6 md:p-12 font-sans selection:bg-cyan-500/30"
      style={{
        backgroundImage: "radial-gradient(circle at 1px 1px, #1e293b 1px, transparent 0)",
        backgroundSize: "28px 28px",
      }}
    >
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header & Controls */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-slate-800 pb-6 gap-6">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight text-white drop-shadow-sm">AetherNet</h1>
            <p className="text-xs text-cyan-500 mt-2 font-mono uppercase tracking-widest">Routing Intelligence Simulator</p>
          </div>
          
          <div className="flex items-end gap-6 bg-slate-900/50 p-4 rounded-lg border border-slate-800 backdrop-blur-md">
            <ScenarioSelector
              scenarios={scenarios}
              selected={current.scenario_id}
              onChange={setSelected}
            />
            <div className="flex gap-2 mb-1">
              <button onClick={story.reset} className="px-3 py-1.5 text-xs font-mono text-slate-400 bg-slate-800 hover:bg-slate-700 rounded transition-colors">
                RESET
              </button>
              <button onClick={story.next} disabled={story.playing} className="px-3 py-1.5 text-xs font-mono text-slate-400 bg-slate-800 hover:bg-slate-700 rounded transition-colors disabled:opacity-50">
                STEP
              </button>
              <button onClick={() => story.setPlaying(!story.playing)} className={`px-5 py-1.5 text-xs font-mono font-bold rounded transition-colors shadow-lg ${story.playing ? "bg-rose-500/20 text-rose-400 border border-rose-500/50" : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 hover:bg-cyan-500/30"}`}>
                {story.playing ? "❚❚ PAUSE" : "▶ AUTO DEMO"}
              </button>
            </div>
          </div>
        </header>

        {/* Cinematic Flow Area */}
        <section className="space-y-4">
          <div className="px-2">
            <p className="text-sm font-mono text-slate-400">
              Simulation Context: <span className="text-cyan-400 uppercase font-bold">{current.scenario_id}</span>
              {" • "}
              <span className={isDiverged ? "text-emerald-400" : "text-slate-300"}>
                {isDiverged ? "Phase-6 intercepted and avoided compromised route." : "All routing modes converged to optimal path."}
              </span>
            </p>
          </div>

          {/* The Main Graph Window */}
          <FlowView scenario={current} step={story.step} />
        </section>

        {/* Data Panels (Wave-109 回歸) */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">

          {/* Routing Decisions */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-md">
            <h3 className="text-sm font-mono text-slate-400 mb-4 uppercase tracking-widest">
              Routing Decisions
            </h3>

            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xs text-slate-500">Legacy</div>
                <div className="text-xl font-bold text-rose-400">
                  {current.decisions?.legacy}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-500">Phase-6</div>
                <div className="text-xl font-bold text-emerald-400">
                  {current.decisions?.phase6_balanced}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-500">Adaptive</div>
                <div className="text-xl font-bold text-cyan-400">
                  {current.decisions?.phase6_adaptive}
                </div>
              </div>
            </div>
          </div>

          {/* Topology Metrics */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-md">
            <h3 className="text-sm font-mono text-slate-400 mb-4 uppercase tracking-widest">
              Topology Metrics
            </h3>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-slate-500">Nodes</div>
                <div className="text-lg font-bold text-white">
                  {current.metrics?.nodes}
                </div>
              </div>

              <div>
                <div className="text-slate-500">Edges</div>
                <div className="text-lg font-bold text-white">
                  {current.metrics?.edges}
                </div>
              </div>

              <div>
                <div className="text-slate-500">Modes</div>
                <div className="text-lg font-bold text-white">
                  {current.metrics?.modes}
                </div>
              </div>

              <div>
                <div className="text-slate-500">Divergence</div>
                <div className={`text-lg font-bold ${
                  current.metrics?.diverged ? "text-emerald-400" : "text-slate-300"
                }`}>
                  {current.metrics?.diverged ? "Detected" : "None"}
                </div>
              </div>
            </div>
          </div>

        </section>

      </div>
    </div>
  )
}