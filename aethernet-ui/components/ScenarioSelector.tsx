"use client"

interface ScenarioSelectorProps {
  scenarios: any[];
  selected: string;
  onChange: (value: string) => void;
}

export default function ScenarioSelector({ scenarios, selected, onChange }: ScenarioSelectorProps) {
  return (
    <div className="flex flex-col space-y-2">
      <label htmlFor="scenario-select" className="text-sm font-medium text-gray-500">
        Active Scenario Context
      </label>
      <select
        id="scenario-select"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        className="w-full max-w-xs border border-gray-300 bg-white p-2 text-sm rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {scenarios.map((s) => (
          <option key={s.scenario_id} value={s.scenario_id}>
            {s.scenario_id.toUpperCase()}
          </option>
        ))}
      </select>
    </div>
  )
}