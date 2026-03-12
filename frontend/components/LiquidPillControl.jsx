"use client";

/**
 * Pill navigation and segmented-control primitives.
 *
 * This module encapsulates:
 * - grapheme-safe label splitting,
 * - per-glyph influence calculations,
 * - bubble spring positioning,
 * - and shared rendering for links/buttons.
 */
import Link from "next/link";
import { motion, useMotionValue, useMotionValueEvent, useSpring } from "framer-motion";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

/**
 * Splits text into grapheme clusters to ensure emoji/combined glyphs
 * animate as a single visual character.
 *
 * @param {string} text
 * @returns {string[]}
 */
function splitGraphemes(text) {
  if (typeof Intl !== "undefined" && Intl.Segmenter) {
    const seg = new Intl.Segmenter("en", { granularity: "grapheme" });
    return Array.from(seg.segment(text), (part) => part.segment);
  }
  return Array.from(text);
}

/**
 * Label renderer that applies per-glyph influence values based on the
 * bubble lens position to create progressive text response.
 *
 * @param {{
 *   label: string,
 *   bubbleX: import("framer-motion").MotionValue<number>,
 *   bubbleW: import("framer-motion").MotionValue<number>,
 *   railRef: import("react").MutableRefObject<HTMLElement | null>,
 *   itemRefs: import("react").MutableRefObject<Array<HTMLElement | null>>,
 *   itemIndex: number,
 *   active: boolean
 * }} props
 * @returns {JSX.Element}
 */
function GlyphLabel({ label, bubbleX, bubbleW, railRef, itemRefs, itemIndex, active }) {
  const glyphs = useMemo(() => splitGraphemes(label), [label]);
  const glyphRefs = useRef([]);
  const centersRef = useRef([]);

  /**
   * Captures glyph center positions relative to the shared rail so each
   * character can respond independently to bubble position updates.
   *
   * @returns {void}
   */
  function measureCenters() {
    const railEl = railRef.current;
    const itemEl = itemRefs.current[itemIndex];
    if (!railEl || !itemEl) return;

    const railRect = railEl.getBoundingClientRect();
    centersRef.current = glyphRefs.current.map((glyphEl) => {
      if (!glyphEl) return null;
      const rect = glyphEl.getBoundingClientRect();
      return rect.left - railRect.left + rect.width / 2;
    });
  }

  /**
   * Calculates per-glyph influence based on distance from the moving bubble
   * center and writes CSS custom properties for transform/filter styling.
   *
   * @returns {void}
   */
  function applyInfluence() {
    const centers = centersRef.current;
    if (!centers.length) return;

    const bx = bubbleX.get();
    const bw = bubbleW.get();
    const bubbleCenter = bx + bw / 2;
    const radius = bw * 0.58 + 12;

    glyphRefs.current.forEach((glyphEl, index) => {
      if (!glyphEl) return;
      const center = centers[index];
      if (center == null) return;

      const signedDistance = center - bubbleCenter;
      const distance = Math.abs(signedDistance);
      const raw = Math.max(0, 1 - distance / radius);
      const smooth = raw * raw * (3 - 2 * raw);

      glyphEl.style.setProperty("--glyph-influence", smooth.toFixed(4));
      glyphEl.style.setProperty("--glyph-side", (signedDistance / radius).toFixed(4));
    });
  }

  useLayoutEffect(() => {
    measureCenters();
    applyInfluence();

    const resizeObserver = new ResizeObserver(() => {
      measureCenters();
      applyInfluence();
    });

    if (railRef.current) resizeObserver.observe(railRef.current);
    if (itemRefs.current[itemIndex]) resizeObserver.observe(itemRefs.current[itemIndex]);
    glyphRefs.current.forEach((glyphEl) => {
      if (glyphEl) resizeObserver.observe(glyphEl);
    });

    return () => resizeObserver.disconnect();
  }, [label, itemIndex, itemRefs]);

  useMotionValueEvent(bubbleX, "change", applyInfluence);
  useMotionValueEvent(bubbleW, "change", applyInfluence);

  return (
    <span className={`pill-label ${active ? "active" : ""}`}>
      {glyphs.map((glyph, index) => (
        <span
          key={`${glyph}-${index}`}
          className="pill-glyph"
          ref={(el) => {
            glyphRefs.current[index] = el;
          }}
        >
          {glyph === " " ? "\u00A0" : glyph}
        </span>
      ))}
    </span>
  );
}

/**
 * Shared bubble motion controller for navigation/segmented rails.
 *
 * @param {Array<{label?: string}>} items
 * @param {number | null} selectedIndex
 * @returns {{
 *   railRef: import("react").MutableRefObject<HTMLElement | null>,
 *   itemRefs: import("react").MutableRefObject<Array<HTMLElement | null>>,
 *   bubbleX: import("framer-motion").MotionValue<number>,
 *   bubbleW: import("framer-motion").MotionValue<number>,
 *   leadEdge: import("framer-motion").MotionValue<number>,
 *   trailEdge: import("framer-motion").MotionValue<number>,
 *   hoverIndex: number | null,
 *   onPointerMove: (event: PointerEvent) => void,
 *   onPointerLeave: () => void,
 *   setHoverIndex: (index: number | null) => void
 * }}
 */
function useBubbleController(items, selectedIndex) {
  const railRef = useRef(null);
  const itemRefs = useRef([]);
  const hoverIndexRef = useRef(null);
  const previousXRef = useRef(0);

  const targetX = useMotionValue(0);
  const targetW = useMotionValue(56);
  const bubbleX = useSpring(targetX, { stiffness: 420, damping: 38, mass: 0.62 });
  const bubbleW = useSpring(targetW, { stiffness: 420, damping: 38, mass: 0.62 });
  const leadEdge = useMotionValue(0.5);
  const trailEdge = useMotionValue(0.5);

  const [hoverIndex, setHoverIndex] = useState(null);
  const [isPositioned, setIsPositioned] = useState(false);

  /**
   * Moves spring targets to match a given item index.
   * `immediate` uses jump() to avoid initial animation on mount.
   *
   * @param {number} index
   * @param {boolean} [immediate=false]
   * @returns {void}
   */
  const moveToIndex = (index, immediate = false) => {
    const itemEl = itemRefs.current[index];
    if (!itemEl) return;

    const left = itemEl.offsetLeft;
    const width = itemEl.offsetWidth;
    if (immediate) {
      targetX.jump(left);
      targetW.jump(width);
      bubbleX.jump(left);
      bubbleW.jump(width);
      setIsPositioned(true);
    } else {
      targetX.set(left);
      targetW.set(width);
    }
  };

  useLayoutEffect(() => {
    setIsPositioned(false);
    if (selectedIndex == null) return;
    moveToIndex(selectedIndex, true);
    previousXRef.current = targetX.get();
  }, [selectedIndex, items.length]);

  useEffect(() => {
    if (selectedIndex == null) return;
    const targetIndex = hoverIndex == null ? selectedIndex : hoverIndex;
    moveToIndex(targetIndex, false);
  }, [hoverIndex, selectedIndex]);

  /**
   * Tracks pointer position across the rail and chooses nearest item center
   * as hover target for continuous bubble interpolation.
   *
   * @param {PointerEvent} event
   * @returns {void}
   */
  const onPointerMove = (event) => {
    const railEl = railRef.current;
    if (!railEl) return;

    const x = event.clientX - railEl.getBoundingClientRect().left;
    let nearest = selectedIndex ?? 0;
    let nearestDistance = Number.POSITIVE_INFINITY;

    itemRefs.current.forEach((itemEl, index) => {
      if (!itemEl) return;
      const center = itemEl.offsetLeft + itemEl.offsetWidth / 2;
      const distance = Math.abs(center - x);
      if (distance < nearestDistance) {
        nearestDistance = distance;
        nearest = index;
      }
    });

    if (hoverIndexRef.current !== nearest) {
      hoverIndexRef.current = nearest;
      setHoverIndex(nearest);
    }
  };

  /**
   * Clears hover state so bubble springs back to selected item when
   * pointer leaves the rail.
   *
   * @returns {void}
   */
  const onPointerLeave = () => {
    hoverIndexRef.current = null;
    setHoverIndex(null);
  };

  useMotionValueEvent(bubbleX, "change", (latest) => {
    const delta = latest - previousXRef.current;
    previousXRef.current = latest;
    const signed = Math.max(-1, Math.min(1, delta / 6));
    const lead = Math.max(0, signed);
    const trail = Math.max(0, -signed);
    leadEdge.set(0.35 + lead * 0.65);
    trailEdge.set(0.35 + trail * 0.65);
  });

  return {
    railRef,
    itemRefs,
    bubbleX,
    bubbleW,
    leadEdge,
    trailEdge,
    isPositioned,
    hoverIndex,
    onPointerMove,
    onPointerLeave,
    setHoverIndex
  };
}

/**
 * Primary navigation rail with moving selection bubble and optional
 * trailing content (mode toggle, theme button, etc.).
 *
 * @param {{
 *   items: Array<{href: string, label: string}>,
 *   activeHref: string,
 *   trailingContent?: import("react").ReactNode,
 *   className?: string
 * }} props
 * @returns {JSX.Element}
 */
export function LiquidPillNav({ items, activeHref, trailingContent = null, className = "" }) {
  const matchedIndex = items.findIndex((item) => item.href === activeHref);
  const selectedIndex = matchedIndex >= 0 ? matchedIndex : null;
  const { railRef, itemRefs, bubbleX, bubbleW, leadEdge, trailEdge, isPositioned, onPointerMove, onPointerLeave, setHoverIndex } = useBubbleController(items, selectedIndex);

  return (
    <nav className={`liquid-pill-rail liquid-nav ${className}`.trim()}>
      <div className="liquid-nav-main" ref={railRef} onPointerMove={onPointerMove} onPointerLeave={onPointerLeave}>
        <motion.span
          className="liquid-pill-bubble"
          style={{ x: bubbleX, width: bubbleW, opacity: selectedIndex == null || !isPositioned ? 0 : 1, "--lead-edge": leadEdge, "--trail-edge": trailEdge }}
          aria-hidden="true"
        />
        {items.map((item, index) => (
          <Link
            key={item.href}
            href={item.href}
            className={`liquid-pill-item ${selectedIndex != null && index === selectedIndex ? "active" : ""}`}
            ref={(el) => {
              itemRefs.current[index] = el;
            }}
            onPointerEnter={() => setHoverIndex(index)}
          >
            <GlyphLabel
              label={item.label}
              bubbleX={bubbleX}
              bubbleW={bubbleW}
              railRef={railRef}
              itemRefs={itemRefs}
              itemIndex={index}
              active={index === selectedIndex}
            />
          </Link>
        ))}
      </div>
      {trailingContent ? <div className="liquid-nav-tail">{trailingContent}</div> : null}
    </nav>
  );
}

/**
 * Generic segmented control using the same bubble/lens behavior as
 * the main navigation rail.
 *
 * @param {{
 *   options: Array<{value: string, label: string}>,
 *   value: string,
 *   onChange: (value: string) => void,
 *   className?: string
 * }} props
 * @returns {JSX.Element}
 */
export function LiquidSegmentedControl({ options, value, onChange, className = "" }) {
  const matchedIndex = options.findIndex((item) => item.value === value);
  const selectedIndex = matchedIndex >= 0 ? matchedIndex : 0;
  const { railRef, itemRefs, bubbleX, bubbleW, leadEdge, trailEdge, isPositioned, onPointerMove, onPointerLeave, setHoverIndex } = useBubbleController(options, selectedIndex);

  return (
    <div className={`liquid-pill-rail liquid-segmented ${className}`.trim()} ref={railRef} onPointerMove={onPointerMove} onPointerLeave={onPointerLeave}>
      <motion.span
        className="liquid-pill-bubble"
        style={{ x: bubbleX, width: bubbleW, opacity: isPositioned ? 1 : 0, "--lead-edge": leadEdge, "--trail-edge": trailEdge }}
        aria-hidden="true"
      />
      {options.map((item, index) => (
        <button
          key={item.value}
          type="button"
          className={`liquid-pill-item ${index === selectedIndex ? "active" : ""}`}
          ref={(el) => {
            itemRefs.current[index] = el;
          }}
          onPointerEnter={() => setHoverIndex(index)}
          onClick={() => onChange(item.value)}
        >
          <GlyphLabel
            label={item.label}
            bubbleX={bubbleX}
            bubbleW={bubbleW}
            railRef={railRef}
            itemRefs={itemRefs}
            itemIndex={index}
            active={index === selectedIndex}
          />
        </button>
      ))}
    </div>
  );
}
