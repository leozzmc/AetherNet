"use client"

import { useState } from "react"
import { usePresentation } from "@/components/usePresentation"
import ScenarioSelector from "@/components/ScenarioSelector"
import DecisionPanel from "@/components/DecisionPanel"
import MetricsPanel from "@/components/MetricsPanel"

export default function Page() {
  const { data, error } = usePresentation()
  const [selected, setSelected] = useState<string | null>(null)

  if (error) return <div className="p-6 text-red-500">Error loading presentation data: {error}</div>
  if (!data) return <div className="p-6 flex items-center justify-center min-h-screen text-gray-500">Loading AetherNet Payload...</div>

  const scenarios = data.scenarios

  // Use selected scenario, or fallback to the first one available
  const current =
    scenarios.find((s: any) => s.scenario_id === selected) ||
    scenarios[0]

  return (
    <div className="min-h-screen bg-white text-gray-900 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        
        <header className="border-b border-gray-200 pb-4">
          <h1 className="text-3xl font-extrabold tracking-tight">AetherNet Dashboard</h1>
          <p className="text-sm text-gray-500 mt-2">Phase-6 Runtime Presentation Layer</p>
        </header>

        <section className="bg-gray-50 p-6 rounded-lg border border-gray-200">
          <ScenarioSelector
            scenarios={scenarios}
            selected={current.scenario_id}
            onChange={setSelected}
          />
        </section>

        <section>
          <DecisionPanel decisions={current.decisions} />
          <MetricsPanel metrics={current.metrics} />
        </section>
        
        {/* Placeholder for the upcoming Wave-110 */}
        <section className="mt-8 border-2 border-dashed border-gray-300 rounded-xl p-12 text-center text-gray-400">
          <p className="font-mono text-sm">React Flow Visualization Area (Pending Wave-110)</p>
          <p className="text-xs mt-2">Nodes prepared: {current.nodes.length} | Edges prepared: {current.edges.length}</p>
        </section>

      </div>
    </div>
  )
}