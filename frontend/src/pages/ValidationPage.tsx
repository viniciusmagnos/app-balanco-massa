import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LayerSelector } from "../components/LayerSelector";
import { SectionsTable } from "../components/SectionsTable";
import { calculateFile } from "../lib/api";
import {
  AlertTriangle,
  ArrowLeft,
  Calculator,
  Layers,
  Loader2,
} from "lucide-react";
import type {
  AnalysisResult,
  CalculationResponse,
  SectionParams,
} from "../lib/api";

interface ValidationPageProps {
  analysis: AnalysisResult | null;
  onCalculationComplete: (result: CalculationResponse) => void;
}

export function ValidationPage({
  analysis,
  onCalculationComplete,
}: ValidationPageProps) {
  const navigate = useNavigate();

  const [greideLayer, setGreideLayer] = useState(
    analysis?.greide_candidates[0]?.name ?? ""
  );
  const [terrenoLayer, setTerrenoLayer] = useState(
    analysis?.terreno_candidates[0]?.name ?? ""
  );
  const [sections, setSections] = useState<SectionParams[]>(
    analysis?.sections.map((s) => ({
      id: s.id,
      x_start: s.x_start,
      x_end: s.x_end,
      initial_station: s.initial_station,
      station_interval: s.station_interval,
      bin_width: s.bin_width,
      h_scale: s.h_scale,
      v_scale: s.v_scale,
    })) ?? []
  );
  const [status, setStatus] = useState<"idle" | "calculating" | "error">(
    "idle"
  );
  const [error, setError] = useState("");

  if (!analysis) {
    navigate("/");
    return null;
  }

  const handleCalculate = async () => {
    if (!greideLayer || !terrenoLayer) {
      setError("Selecione os layers de greide e terreno.");
      return;
    }
    if (sections.length === 0) {
      setError("Adicione pelo menos um trecho.");
      return;
    }

    setStatus("calculating");
    setError("");

    try {
      const result = await calculateFile(analysis.file_id, {
        greide_layer: greideLayer,
        terreno_layer: terrenoLayer,
        sections,
      });
      onCalculationComplete(result);
      navigate("/results");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Erro no cálculo");
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-1">Validar Parâmetros</h2>
        <p className="text-sm text-muted-foreground">
          Revise os layers detectados e parâmetros dos trechos antes de calcular.
        </p>
      </div>

      {analysis.overall_confidence < 0.5 && (
        <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-warning/10 border border-warning/20">
          <AlertTriangle size={18} className="text-warning mt-0.5 shrink-0" />
          <div className="text-sm">
            <p className="font-medium text-warning">Confiança baixa</p>
            <p className="text-warning/80 mt-0.5">
              A análise automática tem confiança de{" "}
              {Math.round(analysis.overall_confidence * 100)}%. Verifique os
              parâmetros com atenção.
            </p>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Layer Selection Card */}
        <div className="bg-surface border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Layers size={16} className="text-manta" />
            <h3 className="text-sm font-semibold">Seleção de Layers</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <LayerSelector
              label="Layer Greide (VT)"
              layers={analysis.layers}
              candidates={analysis.greide_candidates}
              value={greideLayer}
              onChange={setGreideLayer}
            />
            <LayerSelector
              label="Layer Terreno (Perfil)"
              layers={analysis.layers}
              candidates={analysis.terreno_candidates}
              value={terrenoLayer}
              onChange={setTerrenoLayer}
            />
          </div>
        </div>

        {/* Sections Card */}
        <div className="bg-surface border border-border rounded-xl p-5">
          <SectionsTable sections={sections} onChange={setSections} />
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm">
            <AlertTriangle size={15} className="shrink-0" />
            {error}
          </div>
        )}

        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-border text-sm hover:bg-surface-hover"
          >
            <ArrowLeft size={15} />
            Voltar
          </button>
          <button
            onClick={handleCalculate}
            disabled={status === "calculating"}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-manta text-white text-sm font-medium hover:bg-manta-hover disabled:opacity-50"
          >
            {status === "calculating" ? (
              <>
                <Loader2 size={15} className="animate-spin" />
                Calculando...
              </>
            ) : (
              <>
                <Calculator size={15} />
                Calcular
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
