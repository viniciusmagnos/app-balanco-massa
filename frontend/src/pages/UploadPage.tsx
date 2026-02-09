import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileDropzone } from "../components/FileDropzone";
import { uploadFile, analyzeFile } from "../lib/api";
import { FileText, Loader2 } from "lucide-react";
import type { AnalysisResult } from "../lib/api";

interface UploadPageProps {
  onAnalysisComplete: (result: AnalysisResult) => void;
}

export function UploadPage({ onAnalysisComplete }: UploadPageProps) {
  const navigate = useNavigate();
  const [status, setStatus] = useState<
    "idle" | "uploading" | "analyzing" | "error"
  >("idle");
  const [error, setError] = useState("");
  const [progress, setProgress] = useState("");

  const handleFile = async (file: File) => {
    setStatus("uploading");
    setError("");
    setProgress(`Enviando ${file.name}...`);

    try {
      const uploadResult = await uploadFile(file);
      setStatus("analyzing");
      setProgress("Analisando arquivo...");

      const analysis = await analyzeFile(uploadResult.file_id);
      onAnalysisComplete(analysis);
      navigate("/validation");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-16 px-4">
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-manta/10 border border-manta/20 mb-5">
          <FileText size={28} className="text-manta" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Upload de Arquivo</h2>
        <p className="text-muted-foreground text-sm max-w-md mx-auto">
          Envie um arquivo DWG ou DXF de perfil longitudinal para calcular as
          áreas de corte e aterro automaticamente.
        </p>
      </div>

      <FileDropzone
        onFileSelected={handleFile}
        disabled={status === "uploading" || status === "analyzing"}
      />

      {(status === "uploading" || status === "analyzing") && (
        <div className="mt-8 flex justify-center">
          <div className="inline-flex items-center gap-3 bg-surface border border-border rounded-lg px-5 py-3">
            <Loader2 size={18} className="text-manta animate-spin" />
            <span className="text-sm text-foreground">{progress}</span>
          </div>
        </div>
      )}

      {status === "error" && (
        <div className="mt-8 p-4 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
