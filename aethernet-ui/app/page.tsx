"use client"

import { useState } from "react"
import { usePresentation } from "@/components/usePresentation"
import ScenarioSelector from "@/components/ScenarioSelector"
import DecisionPanel from "@/components/DecisionPanel"
import MetricsPanel from "@/components/MetricsPanel"
import FlowView from "@/components/FlowView" // ⭐ 新增引入

export default function Page() {
  const { data, error } = usePresentation()
  const [selected, setSelected] = useState<string | null>(null)

  if (error) return <div className="p-6 text-red-500">Error loading presentation data: {error}</div>
  if (!data) return <div className="p-6 flex items-center justify-center min-h-screen text-gray-500">Loading AetherNet Payload...</div>

  const scenarios = data.scenarios

  const current =
    scenarios.find((s: any) => s.scenario_id === selected) ||
    scenarios[0]

  return (
    <div className="min-h-screen bg-white text-gray-900 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
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

        {/* ⭐ Wave-110: 替換掉原本的 Placeholder，放入真正的動態視覺化畫布 */}
        <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-2">
          <h2 className="text-lg font-semibold px-4 pt-2 pb-4 text-gray-800">Routing Decision Pipeline</h2>
          <FlowView scenario={current} />
        </section>

        <section>
          <DecisionPanel decisions={current.decisions} />
          <MetricsPanel metrics={current.metrics} />
        </section>
        
      </div>
    </div>
  )
}