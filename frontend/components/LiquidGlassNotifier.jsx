"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const MESSAGE_SELECTOR = "p.error, p.success, p.warning";
const DISPLAY_MS = 1600;
const EXIT_MS = 700;
const REDUCED_DISPLAY_MS = 2600;
const REDUCED_EXIT_MS = 180;
const SPLASH_CLEANUP_MS = 1600;
const SPLASH_LEAD_MS = 120;
const MAX_TOASTS = 6;

function kindFromNode(node) {
  if (node.classList.contains("error")) return "error";
  if (node.classList.contains("warning")) return "warning";
  return "success";
}

function dedupeKey(kind, text) {
  return `${kind}::${text}`;
}

function isA11yReducedMotionEnabled() {
  if (typeof document === "undefined") return false;
  return document.documentElement.classList.contains("a11y-reduced-motion");
}

export default function LiquidGlassNotifier() {
  const [toasts, setToasts] = useState([]);
  const [splashes, setSplashes] = useState([]);

  const scanScheduledRef = useRef(false);

  const addToast = useCallback((kind, text) => {
    const reducedMotion = isA11yReducedMotionEnabled();
    const displayMs = reducedMotion ? REDUCED_DISPLAY_MS : DISPLAY_MS;
    const exitMs = reducedMotion ? REDUCED_EXIT_MS : EXIT_MS;

    const now = Date.now();

    const id = `toast-${now}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => {
      const next = [...prev, { id, kind, text, phase: "enter" }];
      return next.length > MAX_TOASTS ? next.slice(next.length - MAX_TOASTS) : next;
    });

    window.setTimeout(() => {
      setToasts((prev) => prev.map((toast) => (
        toast.id === id ? { ...toast, phase: "exit" } : toast
      )));
    }, displayMs);

    if (!reducedMotion) {
      window.setTimeout(() => {
        if (isA11yReducedMotionEnabled()) return;
        const splashId = `splash-${now}-${Math.random().toString(36).slice(2, 8)}`;
        setSplashes((prev) => [...prev, { id: splashId, kind }]);

        window.setTimeout(() => {
          setSplashes((prev) => prev.filter((splash) => splash.id !== splashId));
        }, SPLASH_CLEANUP_MS);
      }, displayMs + Math.max(60, exitMs - SPLASH_LEAD_MS));
    }

    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, displayMs + exitMs);
  }, []);

  const scanMessages = useCallback(() => {
    scanScheduledRef.current = false;

    const nodes = document.querySelectorAll(MESSAGE_SELECTOR);

    for (const node of nodes) {
      if (!(node instanceof HTMLElement)) continue;
      if (node.closest(".liquid-notify-layer")) continue;

      const text = (node.textContent || "").trim();
      if (!text) {
        delete node.dataset.liquidGlassSignature;
        continue;
      }

      const kind = kindFromNode(node);
      const signature = dedupeKey(kind, text);
      if (node.dataset.liquidGlassSignature === signature) continue;

      addToast(kind, text);
      node.dataset.liquidGlassSignature = signature;
      node.setAttribute("aria-hidden", "true");
      node.style.display = "none";
    }
  }, [addToast]);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    scanMessages();

    const observer = new MutationObserver(() => {
      if (scanScheduledRef.current) return;
      scanScheduledRef.current = true;
      window.requestAnimationFrame(scanMessages);
    });

    observer.observe(document.body, {
      childList: true,
      characterData: true,
      subtree: true
    });

    return () => {
      observer.disconnect();
    };
  }, [scanMessages]);

  return (
    <div className="liquid-notify-layer" aria-live="polite" aria-atomic="false">
      <div className="liquid-notify-stack" role="status">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`liquid-toast liquid-toast--${toast.kind} ${toast.phase === "exit" ? "is-exit" : ""}`.trim()}
          >
            <span className="liquid-toast-dot" aria-hidden="true" />
            <span>{toast.text}</span>
          </div>
        ))}
      </div>

      <div className="liquid-splash-zone" aria-hidden="true">
        {splashes.map((splash) => (
          <div key={splash.id} className={`liquid-splash liquid-splash--${splash.kind}`.trim()}>
            <span className="drop drop-1" />
            <span className="drop drop-2" />
            <span className="drop drop-3" />
            <span className="drop drop-4" />
            <span className="drop drop-5" />
            <span className="drop drop-6" />
            <span className="drop drop-7" />
            <span className="drop drop-8" />
            <span className="drop drop-9" />
          </div>
        ))}
      </div>
    </div>
  );
}
