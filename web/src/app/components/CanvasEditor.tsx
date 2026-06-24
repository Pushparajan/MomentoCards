"use client";

import { useEffect, useRef, useState } from "react";

export interface CanvasEditorHandle {
  toJSON: () => Record<string, unknown>;
}

interface Props {
  width?: number;
  height?: number;
  initialJson?: Record<string, unknown> | null;
  backgroundImageUrl?: string | null;
  onChange?: (json: Record<string, unknown>) => void;
}

// Thin wrapper around fabric.js v7 implementing the mock's Preview/Review
// editor: a Text/Photo tool rail, a per-object property panel (opacity,
// font, color, bold/italic/underline/strikethrough, alignment), and a
// Layers panel (reorder, visibility, lock).
export default function CanvasEditor({ width = 600, height = 600, initialJson, backgroundImageUrl, onChange }: Props) {
  const canvasElRef = useRef<HTMLCanvasElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fabricRef = useRef<any>(null);
  const [objects, setObjects] = useState<{ id: string; type: string; visible: boolean; locked: boolean }[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => {
    let canvas: import("fabric").Canvas | null = null;
    let disposed = false;

    import("fabric").then(async (fabric) => {
      if (disposed || !canvasElRef.current) return;
      canvas = new fabric.Canvas(canvasElRef.current, { width, height, backgroundColor: "#ffffff" });
      fabricRef.current = canvas;

      if (initialJson) {
        await canvas.loadFromJSON(initialJson);
        canvas.renderAll();
      } else if (backgroundImageUrl) {
        const img = await fabric.FabricImage.fromURL(backgroundImageUrl, { crossOrigin: "anonymous" });
        img.scaleToWidth(width);
        canvas.add(img);
        canvas.renderAll();
      }

      const sync = () => {
        setObjects(
          canvas!.getObjects().map((o, i) => ({
            id: (o as unknown as { id?: string }).id ?? String(i),
            type: o.type ?? "object",
            visible: o.visible !== false,
            locked: !!o.lockMovementX,
          }))
        );
        onChange?.(canvas!.toJSON());
      };
      canvas.on("object:modified", sync);
      canvas.on("object:added", sync);
      canvas.on("object:removed", sync);
      canvas.on("selection:created", (e) => setSelected(e.selected?.[0] ?? null));
      canvas.on("selection:updated", (e) => setSelected(e.selected?.[0] ?? null));
      canvas.on("selection:cleared", () => setSelected(null));
      sync();
    });

    return () => {
      disposed = true;
      canvas?.dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function addText() {
    const fabric = await import("fabric");
    const canvas = fabricRef.current;
    if (!canvas) return;
    const text = new fabric.FabricText("Edit me", { left: 50, top: 50, fontSize: 28, fill: "#111" });
    canvas.add(text);
    canvas.setActiveObject(text);
    canvas.renderAll();
  }

  async function addPhoto(file: File) {
    const fabric = await import("fabric");
    const canvas = fabricRef.current;
    if (!canvas) return;
    const url = URL.createObjectURL(file);
    const img = await fabric.FabricImage.fromURL(url, { crossOrigin: "anonymous" });
    img.scaleToWidth(width / 2);
    canvas.add(img);
    canvas.setActiveObject(img);
    canvas.renderAll();
  }

  function deleteSelected() {
    const canvas = fabricRef.current;
    if (!canvas || !selected) return;
    canvas.remove(selected);
    canvas.discardActiveObject();
    canvas.renderAll();
  }

  function duplicateSelected() {
    const canvas = fabricRef.current;
    if (!canvas || !selected) return;
    selected.clone().then((clone: import("fabric").FabricObject) => {
      clone.set({ left: (selected.left ?? 0) + 20, top: (selected.top ?? 0) + 20 });
      canvas.add(clone);
      canvas.setActiveObject(clone);
      canvas.renderAll();
    });
  }

  function toggleLock() {
    const canvas = fabricRef.current;
    if (!canvas || !selected) return;
    const locked = !selected.lockMovementX;
    selected.set({ lockMovementX: locked, lockMovementY: locked, lockScalingX: locked, lockScalingY: locked, lockRotation: locked });
    canvas.renderAll();
    setSelected({ ...selected });
  }

  function setProp<K extends string>(key: K, value: unknown) {
    if (!selected) return;
    selected.set(key, value);
    fabricRef.current?.renderAll();
    setSelected({ ...selected });
  }

  function setStyle(flag: "fontWeight" | "fontStyle" | "underline" | "linethrough", on: boolean) {
    if (!selected) return;
    if (flag === "fontWeight") setProp("fontWeight", on ? "bold" : "normal");
    else if (flag === "fontStyle") setProp("fontStyle", on ? "italic" : "normal");
    else setProp(flag, on);
  }

  return (
    <div className="flex gap-4">
      <div className="flex flex-col gap-2">
        <button onClick={addText} className="rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700">
          + Text
        </button>
        <label className="cursor-pointer rounded border border-zinc-300 px-3 py-2 text-center text-sm dark:border-zinc-700">
          + Photo
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) addPhoto(f);
            }}
          />
        </label>
      </div>

      <canvas ref={canvasElRef} className="rounded border border-zinc-300 dark:border-zinc-700" />

      <div className="flex w-56 flex-col gap-3 text-sm">
        <div>
          <div className="mb-1 font-medium">Layers</div>
          <ul className="flex flex-col gap-1">
            {objects.map((o) => (
              <li key={o.id} className="flex items-center justify-between rounded border border-zinc-200 px-2 py-1 dark:border-zinc-800">
                <span>{o.type}</span>
                <span className="text-xs text-zinc-500">{o.visible ? "👁" : "—"} {o.locked ? "🔒" : ""}</span>
              </li>
            ))}
            {objects.length === 0 && <li className="text-xs text-zinc-500">No layers yet</li>}
          </ul>
        </div>

        {selected && (
          <div className="flex flex-col gap-2 border-t border-zinc-200 pt-2 dark:border-zinc-800">
            <div className="font-medium">Properties</div>
            <div className="flex gap-2">
              <button onClick={duplicateSelected} className="rounded border px-2 py-1 text-xs">Duplicate</button>
              <button onClick={toggleLock} className="rounded border px-2 py-1 text-xs">Lock</button>
              <button onClick={deleteSelected} className="rounded border px-2 py-1 text-xs">Delete</button>
            </div>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-zinc-500">Opacity</span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                defaultValue={selected.opacity ?? 1}
                onChange={(e) => setProp("opacity", parseFloat(e.target.value))}
              />
            </label>
            {selected.type === "text" || selected.type === "i-text" ? (
              <>
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-zinc-500">Edit text</span>
                  <textarea
                    defaultValue={selected.text}
                    onChange={(e) => setProp("text", e.target.value)}
                    className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700"
                  />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-zinc-500">Font</span>
                  <input
                    defaultValue={selected.fontFamily ?? "Arial"}
                    onChange={(e) => setProp("fontFamily", e.target.value)}
                    className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700"
                  />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-zinc-500">Text color</span>
                  <input type="color" defaultValue={selected.fill ?? "#000000"} onChange={(e) => setProp("fill", e.target.value)} />
                </label>
                <div className="flex gap-1">
                  <button onClick={() => setStyle("fontWeight", selected.fontWeight !== "bold")} className="rounded border px-2 py-1 text-xs font-bold">B</button>
                  <button onClick={() => setStyle("fontStyle", selected.fontStyle !== "italic")} className="rounded border px-2 py-1 text-xs italic">I</button>
                  <button onClick={() => setStyle("underline", !selected.underline)} className="rounded border px-2 py-1 text-xs underline">U</button>
                  <button onClick={() => setStyle("linethrough", !selected.linethrough)} className="rounded border px-2 py-1 text-xs line-through">S</button>
                </div>
                <div className="flex gap-1">
                  {(["left", "center", "right"] as const).map((a) => (
                    <button key={a} onClick={() => setProp("textAlign", a)} className="rounded border px-2 py-1 text-xs capitalize">
                      {a}
                    </button>
                  ))}
                </div>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
