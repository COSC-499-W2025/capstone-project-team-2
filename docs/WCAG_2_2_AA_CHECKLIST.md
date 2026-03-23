# WCAG 2.2 AA Checklist (Frontend Scope)

Date: March 23, 2026  
System: `frontend/` (Next.js)  
Scope: `/`, `/config`, `/upload`, `/projects`, `/dashboard`, `/workspace`, `/representation`

Status legend:

- `PASS-AUTO`: validated by automated tests
- `PASS-ENG`: validated by code/UX engineering review
- `PASS-MANUAL`: validated by manual assistive-tech testing
- `MANUAL-REQUIRED`: requires manual assistive-tech verification for final sign-off
- `N/A`: not applicable to this product scope

## A/AA Criteria Snapshot

### Perceivable

| Criterion | Status | Evidence |
| --- | --- | --- |
| 1.1.1 Non-text Content | PASS-ENG | Thumbnail image has `alt`; decorative elements use `aria-hidden` in shell components. |
| 1.3.1 Info and Relationships | PASS-AUTO | No axe structural violations on scoped routes (`frontend/e2e/accessibility.spec.js`). |
| 1.3.2 Meaningful Sequence | PASS-ENG | DOM order follows visible sequence for primary forms and nav. |
| 1.3.3 Sensory Characteristics | PASS-ENG | Upload flow provides textual alternatives to drag-only actions. |
| 1.4.1 Use of Color | PASS-ENG | State conveyed by text + icons/labels, not color alone. |
| 1.4.3 Contrast (Minimum) | PASS-AUTO | Zero contrast violations after palette update in `frontend/app/globals.css`. |
| 1.4.4 Resize Text | PASS-MANUAL | Manual 200% zoom checks completed across scoped routes and key journeys. |
| 1.4.10 Reflow | PASS-MANUAL | Manual 320 CSS px reflow checks completed with no loss of core content/function in scoped flows. |
| 1.4.11 Non-text Contrast | PASS-AUTO | Focus and control states pass automated checks. |
| 1.4.12 Text Spacing | PASS-MANUAL | Text-spacing override behavior validated in sign-off and manual spot checks. |
| 1.4.13 Content on Hover or Focus | PASS-ENG | No persistent hover-only content blocking use. |

### Operable

| Criterion | Status | Evidence |
| --- | --- | --- |
| 2.1.1 Keyboard | PASS-MANUAL | Verified in manual keyboard-only flow across `/config`, `/upload`, `/projects`, `/workspace`. |
| 2.1.2 No Keyboard Trap | PASS-MANUAL | Verified manually; no traps found and Escape closes dialogs as expected. |
| 2.2.1 Timing Adjustable | N/A | No session timeout or time-limit UX in frontend scope. |
| 2.4.1 Bypass Blocks | MANUAL-REQUIRED | Add skip-link if required by your policy baseline. |
| 2.4.3 Focus Order | PASS-MANUAL | Verified manually; focus order is logical in tested core workflows. |
| 2.4.4 Link Purpose (In Context) | PASS-ENG | Action text is explicit for primary flows. |
| 2.4.7 Focus Visible | PASS-MANUAL | Verified manually during keyboard-only journey; focus is visible throughout tested flows. |
| 2.5.1 Pointer Gestures | N/A | No path-based gesture-only actions required. |
| 2.5.2 Pointer Cancellation | PASS-ENG | Standard click activation on controls. |
| 2.5.3 Label in Name | PASS-ENG | Button/link accessible names align with visible labels. |
| 2.5.4 Motion Actuation | N/A | No motion-gesture actuation required for core flows. |
| 2.5.7 Dragging Movements (2.2) | PASS-ENG | Drag-and-drop upload has click/browse alternative. |
| 2.5.8 Target Size Minimum (2.2) | PASS-ENG | Minimum 24px on critical icon target (thumbnail delete set to 24x24). |

### Understandable

| Criterion | Status | Evidence |
| --- | --- | --- |
| 3.1.1 Language of Page | PASS-ENG | Root layout sets `<html lang="en">`. |
| 3.2.1 On Focus | PASS-ENG | No unexpected context change on focus alone. |
| 3.2.2 On Input | PASS-ENG | Input changes do not auto-navigate unexpectedly. |
| 3.3.1 Error Identification | PASS-ENG | Explicit error text rendered in workflow cards/forms. |
| 3.3.2 Labels or Instructions | PASS-ENG | File inputs and settings forms have visible labels/instructions. |
| 3.3.3 Error Suggestion | MANUAL-REQUIRED | Validate all backend error states provide actionable suggestions. |
| 3.3.4 Error Prevention (Legal/Financial/Data) | N/A | No legal/financial irreversible submission in scope routes. |
| 3.3.7 Redundant Entry (2.2) | MANUAL-REQUIRED | Verify full multi-step journey for duplicate-entry avoidance. |
| 3.3.8 Accessible Authentication (2.2) | N/A | No authentication challenge flow in this frontend scope. |

### Robust

| Criterion | Status | Evidence |
| --- | --- | --- |
| 4.1.2 Name, Role, Value | PASS-MANUAL | Verified with VoiceOver + Safari and NVDA + Firefox: control names/roles announced correctly, no unlabeled controls found in scope routes. |
| 4.1.3 Status Messages | PASS-MANUAL | Verified during assistive-tech pass for tested routes and dialogs. |

## Automated Evidence

- Test file: `frontend/e2e/accessibility.spec.js`
- Command: `npm run test:a11y`
- Result (March 23, 2026): `7 passed, 0 failed`
- Test file: `frontend/e2e/wcag22-signoff.spec.js`
- Command: `npm run test:signoff`
- Result (March 23, 2026): `3 passed, 0 failed`
- CI gate: `.github/workflows/frontend-accessibility.yml`

## Manual Sign-off Status

Completed:

1. 200% zoom and 320 CSS px reflow verification.
2. Text-spacing override test.
3. Screen reader passes (VoiceOver + Safari, NVDA + Firefox) on scoped routes.
4. Keyboard-only journey pass on scoped workflows.

Remaining governance step:

1. Final review/sign-off by your accessibility owner for any external certification or legal claim language.
