# Theme Toggle Component

The improved `ThemeToggle` provides an explicit, accessible selection UI instead of cycling blindly through modes. It integrates with the animated cursor system for enhanced feedback.

## Features
- Explicit options: Light / Dark / System
- Accessible: listbox semantics, keyboard navigation (ArrowUp/Down, Home/End, Enter, Escape)
- Mount guard to avoid hydration flashes
- Animated popover panel with backdrop blur
- Cursor augmentation: hovering options sets `accent` variant and shows option label
- Small tooltip on hover over trigger showing current resolved theme

## Usage
Already integrated inside `navigation.tsx`:
```tsx
import { ThemeToggle } from '@/components/ui/theme-toggle'

<div className="hidden sm:block">
  <ThemeToggle />
</div>
```
For mobile inside menu container: `<ThemeToggle className="sm:hidden" />`

## Data Attributes / Cursor
The trigger wrapper uses:
- `data-cursor="button"`
- `data-cursor-text="Theme"`
Each option adds `data-cursor-variant="accent"` plus its own text label via `data-cursor-text`.

## Keyboard Behavior
- Enter/Space on trigger: open panel
- Arrow keys: move active focus between options
- Enter/Space on option: select & close
- Escape: close and restore focus to trigger
- Home/End: jump to first/last option

## Extending
To add a new mode:
1. Extend `Option` array in `theme-toggle.tsx`
2. Ensure `value` aligns with acceptable `next-themes` values (or implement custom logic)

## Styling
Uses existing glass utility classes. Additional customizations can be layered via parent `className` or global CSS.

## Fallback Behavior
If the animated cursor provider is not mounted, the component still functions; cursor hooks are safely no-ops.

## Accessibility
- Uses `aria-haspopup="listbox"`, `aria-expanded` on trigger
- Panel uses `role="listbox"`
- Options use `role="option"` + `aria-selected`
- Focus management on open/close

## Troubleshooting
| Issue | Cause | Resolution |
|-------|-------|------------|
| Panel flicker on first load | SSR vs client mismatch | Guard ensures mount; confirm no forced theme mismatch in `next-themes` config |
| Cursor not changing | AnimatedCursor not mounted | Verify `<AnimatedCursor>` wraps app in `layout.tsx` |
| Theme not persisting | Storage key collision or disabled storage | Check browser storage usage / private mode |

---
Feel free to adapt animations or integrate analytics for theme selection events.
