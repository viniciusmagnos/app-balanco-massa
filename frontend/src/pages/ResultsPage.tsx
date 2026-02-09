import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { getResultDownloadUrl } from "../lib/api";
import {
  TrendingDown,
  TrendingUp,
  LayoutList,
  Download,
  RotateCcw,
  Table,
} from "lucide-react";
import type { CalculationResponse } from "../lib/api";
import { ProfileChart } from "../components/ProfileChart";

interface ResultsPageProps {
  result: CalculationResponse | null;
}

function KpiCard({
  label,
  value,
  unit,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  unit: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: "danger" | "success" | "manta";
}) {
  const colorMap = {
    danger: {
      bg: "bg-danger/10",
      border: "border-danger/20",
      text: "text-danger",
      icon: "text-danger",
    },
    success: {
      bg: "bg-success/10",
      border: "border-success/20",
      text: "text-success",
      icon: "text-success",
    },
    manta: {
      bg: "bg-manta/10",
      border: "border-manta/20",
      text: "text-manta",
      icon: "text-manta",
    },
  };
  const c = colorMap[color];

  return (
    <div
      className={`bg-surface border border-border rounded-xl p-5 relative overflow-hidden`}
    >
      <div
        className={`absolute top-0 right-0 w-20 h-20 ${c.bg} rounded-bl-[2rem] flex items-end justify-start p-3`}
      >
        <Icon size={20} className={c.icon} />
      </div>
      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-2">
        {label}
      </p>
      <p className={`text-3xl font-bold ${c.text}`}>{value}</p>
      <p className="text-xs text-muted-foreground mt-1">{unit}</p>
    </div>
  );
}

export function ResultsPage({ result }: ResultsPageProps) {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState(0);

  if (!result) {
    navigate("/");
    return null;
  }

  const sectionIds = useMemo(() => {
    const ids = new Set(result.bins.map((b) => b.section_id));
    return Array.from(ids).sort((a, b) => a - b);
  }, [result.bins]);

  const activeSectionId = sectionIds[activeSection] ?? sectionIds[0];

  const sectionBins = useMemo(
    () => result.bins.filter((b) => b.section_id === activeSectionId),
    [result.bins, activeSectionId],
  );

  const sectionProfile = useMemo(
    () => result.profiles?.find((p) => p.section_id === activeSectionId),
    [result.profiles, activeSectionId],
  );

  const previewBins = result.bins.slice(0, 20);

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-1">Resultados</h2>
        <p className="text-sm text-muted-foreground">
          Resumo do cálculo de corte e aterro por trecho.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <KpiCard
          label="Total Corte"
          value={result.total_cut.toFixed(2)}
          unit="m²"
          icon={TrendingDown}
          color="danger"
        />
        <KpiCard
          label="Total Aterro"
          value={result.total_fill.toFixed(2)}
          unit="m²"
          icon={TrendingUp}
          color="success"
        />
        <KpiCard
          label="Trechos"
          value={String(result.sections_processed)}
          unit="trechos processados"
          icon={LayoutList}
          color="manta"
        />
      </div>

      {/* Profile Chart */}
      {sectionProfile && sectionProfile.points.length > 0 && (
        <div className="mb-8">
          {sectionIds.length > 1 && (
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm text-muted-foreground">Trecho:</span>
              {sectionIds.map((id, idx) => (
                <button
                  key={id}
                  onClick={() => setActiveSection(idx)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    idx === activeSection
                      ? "bg-manta text-white"
                      : "bg-surface border border-border hover:bg-surface-hover"
                  }`}
                >
                  {id}
                </button>
              ))}
            </div>
          )}
          <ProfileChart points={sectionProfile.points} bins={sectionBins} />
        </div>
      )}

      {/* Data Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden mb-6">
        <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
          <Table size={15} className="text-manta" />
          <h3 className="text-sm font-semibold">
            Dados por Faixa de Análise
          </h3>
          <span className="text-xs text-muted-foreground ml-auto">
            {Math.min(20, result.bins.length)} de {result.bins.length} linhas
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-elevated/50">
                <th className="text-left py-2.5 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Trecho
                </th>
                <th className="text-right py-2.5 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  X Inicio
                </th>
                <th className="text-right py-2.5 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  X Fim
                </th>
                <th className="text-right py-2.5 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Est. Inicio
                </th>
                <th className="text-right py-2.5 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Est. Fim
                </th>
                <th className="text-right py-2.5 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Dist. (m)
                </th>
                <th className="text-right py-2.5 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Corte
                </th>
                <th className="text-right py-2.5 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Aterro
                </th>
              </tr>
            </thead>
            <tbody>
              {previewBins.map((bin, i) => (
                <tr
                  key={i}
                  className="border-t border-border-subtle hover:bg-surface-hover"
                >
                  <td className="py-2.5 px-4 font-medium">
                    {bin.section_id}
                  </td>
                  <td className="text-right py-2.5 px-4 tabular-nums text-muted-foreground">
                    {bin.x_start.toFixed(2)}
                  </td>
                  <td className="text-right py-2.5 px-4 tabular-nums text-muted-foreground">
                    {bin.x_end.toFixed(2)}
                  </td>
                  <td className="text-right py-2.5 px-4 tabular-nums text-muted-foreground">
                    {bin.station_start.toFixed(2)}
                  </td>
                  <td className="text-right py-2.5 px-4 tabular-nums text-muted-foreground">
                    {bin.station_end.toFixed(2)}
                  </td>
                  <td className="text-right py-2.5 px-4 tabular-nums text-muted-foreground">
                    {bin.dist_m.toFixed(2)}
                  </td>
                  <td className="text-right py-2.5 px-4 tabular-nums font-medium text-danger">
                    {bin.cut.toFixed(4)}
                  </td>
                  <td className="text-right py-2.5 px-4 tabular-nums font-medium text-success">
                    {bin.fill.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <a
          href={getResultDownloadUrl(result.result_id)}
          download
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-manta text-white text-sm font-medium hover:bg-manta-hover"
        >
          <Download size={15} />
          Download CSV
        </a>
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-border text-sm hover:bg-surface-hover"
        >
          <RotateCcw size={15} />
          Nova Análise
        </button>
      </div>
    </div>
  );
}
