"use client"

import { useState } from "react"
import { usePresentation } from "@/components/usePresentation"
import { useStoryPlayer } from "@/components/useStoryPlayer"
import ScenarioSelector from "@/components/ScenarioSelector"
import DecisionPanel from "@/components/DecisionPanel"
import MetricsPanel from "@/components/MetricsPanel"
import FlowView from "@/components/FlowView"
import StoryPanel from "@/components/StoryPanel"

export default function Page() {
  const { data, error } = usePresentation()
  const [selected, setSelected] = useState<string | null>(null)

  const scenarios = data?.scenarios || []
  const current = scenarios.find((s: any) => s.scenario_id === selected) || scenarios[0]

  // Hook up the Story Player
  const story = useStoryPlayer(current?.story_script || [])

  if (error) return <div className="p-6 text-red-500">Error loading presentation data: {error}</div>
  if (!current) return <div className="p-6 text-gray-500">Loading Mission Control...</div>

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-8 font-sans selection:bg-blue-200">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="flex justify-between items-end border-b border-slate-300 pb-4">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">AetherNet</h1>
            <p className="text-sm text-slate-500 mt-1 font-mono uppercase tracking-widest">Routing Intelligence Simulator</p>
          </div>
          <ScenarioSelector
            scenarios={scenarios}
            selected={current.scenario_id}
            onChange={setSelected}
          />
        </header>

        {/* 🎬 Wave-111: Cinematic Story Mode Layout */}
        <section className="bg-slate-900 rounded-xl shadow-2xl border border-slate-800 p-6 space-y-4">
          
          <div className="flex justify-between items-center px-2">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Live Pipeline Monitor
            </h2>
            
            {/* Playback Controls */}
            <div className="flex gap-2">
              <button 
                onClick={story.reset}
                className="px-4 py-1.5 text-xs font-mono text-slate-300 bg-slate-800 hover:bg-slate-700 rounded transition-colors"
              >
                Reset
              </button>
              <button 
                onClick={story.next}
                disabled={story.playing || story.index >= story.total - 1}
                className="px-4 py-1.5 text-xs font-mono text-slate-300 bg-slate-800 hover:bg-slate-700 rounded transition-colors disabled:opacity-50"
              >
                Step
              </button>
              <button 
                onClick={() => story.setPlaying(!story.playing)}
                className={`px-6 py-1.5 text-xs font-mono font-bold rounded transition-colors ${
                  story.playing 
                    ? "bg-rose-500/20 text-rose-400 hover:bg-rose-500/30" 
                    : "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"
                }`}
              >
                {story.playing ? "❚❚ PAUSE" : "▶ PLAY"}
              </button>
            </div>
          </div>

          {/* Interactive Graph & Narrative Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-3">
              <FlowView scenario={current} activeStep={story.step} />
            </div>
            <div className="lg:col-span-1 flex flex-col justify-end">
              <StoryPanel step={story.step} index={story.index} total={story.total} />
            </div>
          </div>

        </section>

        <section>
          <DecisionPanel decisions={current.decisions} />
          <MetricsPanel metrics={current.metrics} />
        </section>

      </div>
    </div>
  )
}