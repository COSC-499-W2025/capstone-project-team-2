# Accessibility Evidence

Date: March 23, 2026  
Project: `capstone-project-team-2` frontend (`Next.js`)

## Executive Summary

As of March 23, 2026, the frontend passes automated accessibility checks for WCAG 2.0/2.1/2.2 A/AA on core routes, including shared navbar flows.

Scope statement:

- "Our frontend currently has zero violations in automated WCAG 2.2 A/AA axe audits across key user journeys."

## Scope Audited

Routes tested:

- `/`
- `/config`
- `/upload`
- `/projects`
- `/dashboard`
- `/workspace`
- `/representation`

Shared components covered by these routes include:

- Top navigation/navbar
- Segmented controls
- Upload controls
- Modal dialogs
- Action buttons and status surfaces

## Method and Tooling

Automated accessibility test:

- Playwright + axe-core (`@axe-core/playwright`)
- Tags enforced:
  - `wcag2a`, `wcag2aa`
  - `wcag21a`, `wcag21aa`
  - `wcag22a`, `wcag22aa`

Test file:

- `frontend/e2e/accessibility.spec.js`
- CI workflow: `.github/workflows/frontend-accessibility.yml`

## Reproducible Commands

Run from `frontend/`:

```bash
npm run test:a11y
```

Latest result (March 23, 2026):

- `7 passed (0 failed)` for the route set above.
- Sign-off checks (`npm run test:signoff`): `3 passed (0 failed)`.

Supporting quality checks also passed:

```bash
npm test
npm run build
```

## Key Accessibility Fixes Implemented

- Added semantic and keyboard-accessible segmented controls (`radiogroup`/`radio`, checked state).
- Restored visible focus styling for segmented controls.
- Made file-upload drop zones keyboard reachable and focus-visible.
- Replaced clickable non-semantic thumbnail container with a real `<button>`.
- Added dialog semantics and modal focus management (focus trap, Escape close, focus restore).
- Resolved color contrast failures detected by axe.
- Increased small icon control target size to 24x24 for WCAG 2.2 target-size expectations.

## Manual Validation Status

Manual checks completed (March 23, 2026):

- VoiceOver + Safari and NVDA + Firefox passes completed for core routes; control labels/roles, dialog behavior, and unlabeled-control checks passed.
- Keyboard-only end-to-end journey checks completed and passed for core workflows.
- High-zoom/responsive checks completed and passed, including:
  - 200% zoom and 320 CSS px reflow behavior.
  - 250% large-zoom navigation/flow usability tuning.
  - Floating accessibility control reduced/compacted for high-zoom sessions to avoid blocking critical content.

## Remaining Risk / Next Step

Automation plus manual testing provides strong implementation evidence for the audited scope.  
Final wording for external use should match your team/instructor sign-off process.
