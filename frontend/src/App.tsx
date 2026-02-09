import { useState } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { UploadPage } from "./pages/UploadPage";
import { ValidationPage } from "./pages/ValidationPage";
import { ResultsPage } from "./pages/ResultsPage";
import { Upload, Settings, BarChart3 } from "lucide-react";
import type { AnalysisResult, CalculationResponse } from "./lib/api";

const steps = [
  { path: "/", label: "Upload", icon: Upload },
  { path: "/validation", label: "Validação", icon: Settings },
  { path: "/results", label: "Resultados", icon: BarChart3 },
];

function StepIndicator() {
  const location = useLocation();
  const currentIndex = steps.findIndex((s) => s.path === location.pathname);

  return (
    <div className="flex items-center gap-1">
      {steps.map((step, i) => {
        const Icon = step.icon;
        const isActive = i === currentIndex;
        const isDone = i < currentIndex;

        return (
          <div key={step.path} className="flex items-center">
            {i > 0 && (
              <div
                className={`w-8 h-px mx-1 ${
                  isDone ? "bg-manta" : "bg-border"
                }`}
              />
            )}
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                isActive
                  ? "bg-manta/15 text-manta border border-manta/30"
                  : isDone
                    ? "bg-manta/10 text-manta/70"
                    : "text-muted-foreground"
              }`}
            >
              <Icon size={13} />
              <span className="hidden sm:inline">{step.label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-manta to-manta-hover flex items-center justify-center">
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <div>
              <h1 className="text-sm font-semibold leading-tight">
                Balanço de Massa
              </h1>
              <p className="text-[10px] text-muted-foreground leading-tight">
                Manta Geo
              </p>
            </div>
          </div>
          <StepIndicator />
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}

function App() {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [calcResult, setCalcResult] =
    useState<CalculationResponse | null>(null);

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route
            path="/"
            element={<UploadPage onAnalysisComplete={setAnalysis} />}
          />
          <Route
            path="/validation"
            element={
              <ValidationPage
                analysis={analysis}
                onCalculationComplete={setCalcResult}
              />
            }
          />
          <Route
            path="/results"
            element={<ResultsPage result={calcResult} />}
          />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
