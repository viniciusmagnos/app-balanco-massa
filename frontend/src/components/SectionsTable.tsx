import { Plus, Trash2, Ruler } from "lucide-react";
import type { SectionParams } from "../lib/api";

interface SectionsTableProps {
  sections: SectionParams[];
  onChange: (sections: SectionParams[]) => void;
}

export function SectionsTable({ sections, onChange }: SectionsTableProps) {
  const updateField = (
    index: number,
    field: keyof SectionParams,
    value: number
  ) => {
    const updated = sections.map((s, i) =>
      i === index ? { ...s, [field]: value } : s
    );
    onChange(updated);
  };

  const addSection = () => {
    const lastSection = sections[sections.length - 1];
    onChange([
      ...sections,
      {
        id: sections.length + 1,
        x_start: lastSection?.x_end ?? 0,
        x_end: (lastSection?.x_end ?? 0) + 1000,
        initial_station: 1000,
        station_interval: 20,
        bin_width: 100,
        h_scale: 1,
        v_scale: 1,
      },
    ]);
  };

  const removeSection = (index: number) => {
    if (sections.length <= 1) return;
    onChange(sections.filter((_, i) => i !== index));
  };

  const fields: { key: keyof SectionParams; label: string; step?: number }[] =
    [
      { key: "x_start", label: "X Inicio" },
      { key: "x_end", label: "X Fim" },
      { key: "initial_station", label: "Estaca Ini." },
      { key: "station_interval", label: "Intervalo", step: 1 },
      { key: "bin_width", label: "Faixa Análise (m)", step: 10 },
      { key: "h_scale", label: "Esc. H", step: 0.1 },
      { key: "v_scale", label: "Esc. V", step: 0.1 },
    ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Ruler size={16} className="text-manta" />
          <h3 className="text-sm font-semibold">Trechos</h3>
          <span className="text-xs text-muted-foreground">
            ({sections.length})
          </span>
        </div>
        <button
          onClick={addSection}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-manta/10 text-manta font-medium hover:bg-manta/20"
        >
          <Plus size={13} />
          Adicionar
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr>
              <th className="text-left py-2 px-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                #
              </th>
              {fields.map((f) => (
                <th
                  key={f.key}
                  className="text-left py-2 px-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider"
                >
                  {f.label}
                </th>
              ))}
              <th className="py-2 px-2"></th>
            </tr>
          </thead>
          <tbody>
            {sections.map((section, idx) => (
              <tr
                key={section.id}
                className="border-t border-border-subtle group"
              >
                <td className="py-2 px-2 text-muted-foreground font-medium">
                  {section.id}
                </td>
                {fields.map((f) => (
                  <td key={f.key} className="py-1.5 px-1">
                    <input
                      type="number"
                      step={f.step ?? 1}
                      value={section[f.key]}
                      onChange={(e) =>
                        updateField(
                          idx,
                          f.key,
                          parseFloat(e.target.value) || 0
                        )
                      }
                      className="w-full border border-border rounded-md px-2.5 py-1.5 text-sm bg-background hover:border-manta/30 focus:border-manta tabular-nums"
                    />
                  </td>
                ))}
                <td className="py-2 px-2">
                  {sections.length > 1 && (
                    <button
                      onClick={() => removeSection(idx)}
                      className="p-1.5 rounded-md text-muted-foreground hover:text-danger hover:bg-danger/10 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Remover trecho"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
