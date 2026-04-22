import React, { useRef, useState, useEffect, useCallback } from "react";
import type { CropRect } from "../api";

interface Props {
  imageUrl: string;
  onCropChange: (crop: CropRect | null) => void;
}

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export default function SelectionCanvas({ imageUrl, onCropChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const [dragging, setDragging] = useState(false);
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);
  const [rect, setRect] = useState<Rect | null>(null);
  // Scale from canvas coords to original image coords
  const scaleRef = useRef({ sx: 1, sy: 1 });

  const draw = useCallback((selection: Rect | null) => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img) return;
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    if (selection) {
      ctx.strokeStyle = "#4A90D9";
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      ctx.strokeRect(selection.x, selection.y, selection.w, selection.h);
      ctx.fillStyle = "rgba(74,144,217,0.15)";
      ctx.fillRect(selection.x, selection.y, selection.w, selection.h);
      ctx.setLineDash([]);
    }
  }, []);

  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      imgRef.current = img;
      const canvas = canvasRef.current;
      if (!canvas) return;
      // Fit image into max 600px wide
      const maxW = 600;
      const scale = Math.min(1, maxW / img.naturalWidth);
      canvas.width = img.naturalWidth * scale;
      canvas.height = img.naturalHeight * scale;
      scaleRef.current = {
        sx: img.naturalWidth / canvas.width,
        sy: img.naturalHeight / canvas.height,
      };
      draw(null);
    };
    img.src = imageUrl;
    setRect(null);
    onCropChange(null);
  }, [imageUrl, draw, onCropChange]);

  const getPos = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current!;
    const r = canvas.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };

  const onMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getPos(e);
    setStart(pos);
    setDragging(true);
    setRect(null);
    onCropChange(null);
  };

  const onMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!dragging || !start) return;
    const pos = getPos(e);
    const r: Rect = {
      x: Math.min(start.x, pos.x),
      y: Math.min(start.y, pos.y),
      w: Math.abs(pos.x - start.x),
      h: Math.abs(pos.y - start.y),
    };
    setRect(r);
    draw(r);
  };

  const onMouseUp = () => {
    setDragging(false);
    if (rect && rect.w > 5 && rect.h > 5) {
      const { sx, sy } = scaleRef.current;
      onCropChange({
        x: rect.x * sx,
        y: rect.y * sy,
        w: rect.w * sx,
        h: rect.h * sy,
      });
    } else {
      setRect(null);
      draw(null);
      onCropChange(null);
    }
  };

  const clearSelection = () => {
    setRect(null);
    draw(null);
    onCropChange(null);
  };

  return (
    <div>
      <p style={{ margin: "0 0 6px", fontSize: 13, color: "#555" }}>
        Drag to select a region (optional — leave empty to use full image)
      </p>
      <canvas
        ref={canvasRef}
        style={{ cursor: "crosshair", border: "1px solid #ddd", borderRadius: 8, display: "block" }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      />
      {rect && (
        <button
          onClick={clearSelection}
          style={{ marginTop: 6, fontSize: 12, padding: "3px 10px", cursor: "pointer" }}
        >
          Clear selection
        </button>
      )}
    </div>
  );
}
