# WCAG 2.2 Scope Statement

Date: March 23, 2026

## Scope Statement

"Within the audited frontend scope, we meet WCAG 2.2 A/AA checks based on passing automated audits and documented manual assistive-technology and reflow/zoom validation across core user routes."

## Scope

- Frontend routes: `/`, `/config`, `/upload`, `/projects`, `/dashboard`, `/workspace`, `/representation`
- Shared navbar and common controls included in all route checks.

## Evidence

- Automated audit: Playwright + axe (`wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22a`, `wcag22aa`)
- Command: `npm run test:a11y`
- Latest run: `7 passed, 0 failed`
- Command: `npm run test:signoff`
- Latest run: `3 passed, 0 failed`
- Supporting quality checks: `npm test` and `npm run build` passed.
- CI enforcement added: `.github/workflows/frontend-accessibility.yml`
- Detailed checklist: `docs/WCAG_2_2_AA_CHECKLIST.md`
- Manual assistive-tech checks completed: VoiceOver+Safari, NVDA+Firefox, and keyboard-only core journey pass.
- Manual zoom/reflow/text-spacing checks completed, including high-zoom responsive behavior validation.

## Summary Statement

"For our scoped frontend routes, automated WCAG 2.2 A/AA audits are clean and our manual screen-reader, keyboard, and zoom/reflow checks are documented as passing."
