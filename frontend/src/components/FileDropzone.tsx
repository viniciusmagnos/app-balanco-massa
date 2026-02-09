import { useCallback, useState, type DragEvent } from "react";
import { CloudUpload } from "lucide-react";

interface FileDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function FileDropzone({ onFileSelected, disabled }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      if (!disabled) setIsDragging(true);
    },
    [disabled]
  );

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (
        file &&
        (file.name.endsWith(".dwg") || file.name.endsWith(".dxf"))
      ) {
        onFileSelected(file);
      }
    },
    [onFileSelected, disabled]
  );

  const handleClick = useCallback(() => {
    if (disabled) return;
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".dwg,.dxf";
    input.onchange = () => {
      const file = input.files?.[0];
      if (file) onFileSelected(file);
    };
    input.click();
  }, [onFileSelected, disabled]);

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        group relative border-2 border-dashed rounded-xl p-14 text-center cursor-pointer
        bg-surface/50
        ${
          isDragging
            ? "border-manta bg-manta/5"
            : "border-border hover:border-manta/40 hover:bg-surface"
        }
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      <div className="flex flex-col items-center gap-4">
        <div
          className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-colors ${
            isDragging
              ? "bg-manta/15 text-manta"
              : "bg-muted text-muted-foreground group-hover:bg-manta/10 group-hover:text-manta"
          }`}
        >
          <CloudUpload size={26} />
        </div>
        <div>
          <p className="text-base font-medium">
            Arraste um arquivo DWG ou DXF aqui
          </p>
          <p className="text-sm text-muted-foreground mt-1.5">
            ou{" "}
            <span className="text-manta font-medium">
              clique para selecionar
            </span>
          </p>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground">
            .dwg
          </span>
          <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground">
            .dxf
          </span>
        </div>
      </div>
    </div>
  );
}
