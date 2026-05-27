import { Scenario } from "../api";

interface Props {
  scenarios: Scenario[];
  onSelect: (scenario: Scenario) => void;
  disabled: boolean;
}

export default function ScenarioChips({ scenarios, onSelect, disabled }: Props) {
  return (
    <div className="scenario-chips">
      {scenarios.map((s) => (
        <button
          key={s.id}
          className="chip"
          disabled={disabled}
          onClick={() => onSelect(s)}
          title={s.query}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}
