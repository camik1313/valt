"use client";

import { useRef, useState } from "react";

// The largest video we'll accept, in megabytes. Smartphone landing
// clips are short, so this is generous. Rejecting huge files early
// protects us from someone uploading a 2GB movie by mistake.
const MAX_MB = 200;

type VideoUploaderProps = {
  onFileSelected: (file: File) => void; // called with the chosen file once valid
  disabled?: boolean;                   // when true, the zone is inert
};

export default function VideoUploader({
  onFileSelected,
  disabled = false,
}: VideoUploaderProps) {
  const [isDragging, setIsDragging] = useState(false); // dragging over the zone?
  const [error, setError] = useState<string | null>(null); // validation message
  const inputRef = useRef<HTMLInputElement>(null); // handle to hidden file input

  // Is this actually an acceptable video file?
  function validate(file: File): string | null {
    if (!file.type.startsWith("video/")) {
      return "That doesn't look like a video file. Please choose an .mp4 or .mov clip.";
    }
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > MAX_MB) {
      return `That file is ${sizeMb.toFixed(0)} MB. Please keep videos under ${MAX_MB} MB.`;
    }
    return null;
  }

  // Validate, then either show an error or accept the file.
  function handleFile(file: File | undefined) {
    if (!file) return;
    const problem = validate(file);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    onFileSelected(file);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    handleFile(e.dataTransfer.files?.[0]);
  }

  function onDragOver(e: React.DragEvent) {
    e.preventDefault(); // required so the browser allows a drop
    if (!disabled) setIsDragging(true);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-disabled={disabled}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={() => setIsDragging(false)}
        className={[
          "flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed p-12 text-center transition-all",
          disabled
            ? "cursor-not-allowed border-line bg-surface opacity-60"
            : "cursor-pointer",
          isDragging
            ? "border-track bg-track-soft"
            : "border-line bg-white hover:border-track hover:bg-track-soft/30",
        ].join(" ")}
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-track-soft">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke="#0E7C86" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" stroke="#0E7C86"
                  strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>

        <div>
          <p className="font-display text-lg font-semibold text-ink">
            Drop a jump-landing video here
          </p>
          <p className="mt-1 text-sm text-muted">
            or <span className="font-medium text-track">click to browse</span> · .mp4 or .mov · up to {MAX_MB} MB
          </p>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      {error && (
        <p className="mt-3 text-sm text-risk" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}