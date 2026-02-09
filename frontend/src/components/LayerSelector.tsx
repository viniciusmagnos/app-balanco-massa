import type { LayerCandidate } from "../lib/api";

interface LayerSelectorProps {
  label: string;
  layers: string[];
  candidates: LayerCandidate[];
  value: string;
  onChange: (value: string) => void;
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  let color = "bg-danger/15 text-danger";
  if (confidence >= 0.7) color = "bg-success/15 text-success";
  else if (confidence >= 0.4) color = "bg-warning/15 text-warning";

  return (
    <span
      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${color}`}
    >
      {Math.round(confidence * 100)}%
    </span>
  );
}

export function LayerSelector({
  label,
  layers,
  candidates,
  value,
  onChange,
}: LayerSelectorProps) {
  const candidateNames = new Set(candidates.map((c) => c.name));

  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 border border-border rounded-lg px-3 py-2.5 text-sm bg-background hover:border-manta/40 focus:border-manta"
        >
          <option value="">-- Selecionar layer --</option>
          {candidates.length > 0 && (
            <optgroup label="Sugeridos">
              {candidates.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} ({Math.round(c.confidence * 100)}%)
                </option>
              ))}
            </optgroup>
          )}
          <optgroup label="Todos os layers">
            {layers
              .filter((l) => !candidateNames.has(l))
              .map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
          </optgroup>
        </select>
        {value && candidates.find((c) => c.name === value) && (
          <ConfidenceBadge
            confidence={candidates.find((c) => c.name === value)!.confidence}
          />
        )}
      </div>
    </div>
  );
}
