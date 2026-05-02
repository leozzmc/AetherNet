"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { usePresentation } from "@/hooks/usePresentation";
import { useStoryPlayer } from "@/hooks/useStoryPlayer";
import ScenarioSelector from "@/components/ScenarioSelector";
import DecisionPanel from "@/components/DecisionPanel";
import MetricsPanel from "@/components/MetricsPanel";
import FlowView from "@/components/FlowView";

function DashboardContent() {
  const { data, error } = usePresentation();
  const params = useSearchParams();

  const isRecording = params.get("recording") === "true";
  const isPresentation = params.get("mode") === "presentation" || isRecording;
  const isClean = params.get("clean") === "true" || isRecording;
  const urlScenario = params.get("scenario");

  const [selected, setSelected] = useState<string | null>(null);

  const scenarios = data?.scenarios || [];

  const urlScenarioExists =
    urlScenario &&
    scenarios.some((scenario: any) => scenario.scenario_id === urlScenario);

  const recordingDefault =
    isRecording && scenarios.some((scenario: any) => scenario.scenario_id === "jammed")
      ? "jammed"
      : null;

  const activeScenarioId = selected || (urlScenarioExists ? urlScenario : null) || recordingDefault;

  const current =
    scenarios.find((scenario: any) => scenario.scenario_id === activeScenarioId) ||
    scenarios[0];

  const story = useStoryPlayer(current?.story_script || [], isPresentation);

  useEffect(() => {
    if (!selected && current?.scenario_id) {
      setSelected(current.scenario_id);
    }
  }, [current?.scenario_id, selected]);

  if (error) {
    return <div className="p-6 text-red-500">Error loading data: {error}</div>;
  }

  if (!current) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 p-6 font-mono text-slate-500">
        Initializing Telemetry...
      </div>
    );
  }

  const isDiverged = current.metrics?.diverged;

  function handleExport() {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `aethernet-payload-${current.scenario_id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div
      className="min-h-screen bg-slate-950 p-6 font-sans text-slate-200 selection:bg-cyan-500/30 md:p-8"
      style={{
        backgroundImage:
          "radial-gradient(circle at 1px 1px, #1e293b 1px, transparent 0)",
        backgroundSize: "28px 28px",
      }}
    >
      <div className={`mx-auto space-y-6 ${isPresentation ? "max-w-[95%]" : "max-w-6xl"}`}>
        {!isPresentation && (
          <header className="flex flex-col items-start justify-between gap-4 border-b border-slate-800 pb-4 md:flex-row md:items-end">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-white drop-shadow-sm">
                AetherNet
              </h1>
              <p className="mt-1 font-mono text-xs uppercase tracking-widest text-cyan-500">
                Routing Intelligence Simulator
              </p>
            </div>

            <div className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-900/50 p-3 backdrop-blur-md">
              <ScenarioSelector
                scenarios={scenarios}
                selected={current.scenario_id}
                onChange={setSelected}
              />

              <div className="flex gap-2">
                <button
                  onClick={story.reset}
                  className="rounded bg-slate-800 px-3 py-1.5 font-mono text-xs text-slate-400 transition-colors hover:bg-slate-700"
                >
                  RESET
                </button>

                <button
                  onClick={story.next}
                  disabled={story.playing}
                  className="rounded bg-slate-800 px-3 py-1.5 font-mono text-xs text-slate-400 transition-colors hover:bg-slate-700 disabled:opacity-50"
                >
                  STEP
                </button>

                <button
                  onClick={() => story.setPlaying(!story.playing)}
                  className={`rounded px-4 py-1.5 font-mono text-xs font-bold shadow-lg transition-colors ${
                    story.playing
                      ? "border border-rose-500/50 bg-rose-500/20 text-rose-400"
                      : "border border-cyan-500/50 bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30"
                  }`}
                >
                  {story.playing ? "❚❚ PAUSE" : "▶ AUTO"}
                </button>

                {!isRecording && (
                  <button
                    onClick={handleExport}
                    className="ml-2 rounded border border-indigo-500/50 bg-indigo-500/20 px-3 py-1.5 font-mono text-xs text-slate-300 transition-colors hover:bg-indigo-500/30"
                  >
                    ↓ JSON
                  </button>
                )}
              </div>
            </div>
          </header>
        )}

        <section className="space-y-3">
          <div className="px-2">
            <p className="font-mono text-sm text-slate-400">
              Scenario Context:{" "}
              <span className="font-bold uppercase text-cyan-400">
                {current.scenario_id}
              </span>
              {" • "}
              <span className={isDiverged ? "text-emerald-400" : "text-slate-300"}>
                {isDiverged
                  ? "Phase-6 intercepted and avoided compromised route."
                  : "All routing modes converged to optimal path."}
              </span>
            </p>
          </div>

          <FlowView
            scenario={current}
            step={story.step}
            isPresentation={isPresentation}
          />
        </section>

        {!(isPresentation && isClean) && (
          <section className="grid grid-cols-1 gap-6 pt-2 md:grid-cols-3">
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
  );
}

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950 font-mono text-cyan-500">
          Initializing Systems...
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}