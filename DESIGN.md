# DESIGN.md — YOS Design System

> Premium dark-mode design system for a personal AI operating system dashboard.
> Stack: FastAPI, Jinja2 templates, Tailwind CSS (CDN), vanilla JS.

---

## 1. Design Parameters

| Parameter | Value | Rationale |
|---|---|---|
| DESIGN_VARIANCE | 7 | Asymmetric, editorial feel for a personal dashboard |
| MOTION_INTENSITY | 4 | CSS-only transitions — no JS animation libraries (Jinja2 stack) |
| VISUAL_DENSITY | 5 | Balanced — not too sparse, not cockpit-dense |

---

## 2. Color System

### Base Palette (Slate-based, cool-neutral dark)

| Token | CSS Variable | Value | Usage |
|---|---|---|---|
| Background | `--bg` | `#0f172a` (slate-900) | Page background |
| Surface 1 | `--surface-1` | `#1e293b` (slate-800) | Cards, sidebar |
| Surface 2 | `--surface-2` | `#334155` (slate-700) | Inputs, elevated UI |
| Border | `--border` | `#475569` (slate-600) | Default borders |
| Border Subtle | `--border-subtle` | `#334155` (slate-700) | Subtle dividers |
| Text Primary | `--text` | `#f8fafc` (slate-50) | Primary text |
| Text Secondary | `--text-secondary` | `#94a3b8` (slate-400) | Secondary text |
| Text Tertiary | `--text-tertiary` | `#64748b` (slate-500) | Muted/captions |

### Accent: Cyan (single accent, technical & clean)

| Token | Value | Usage |
|---|---|---|
| `--accent` | `#06b6d4` (cyan-500) | Primary actions, active nav, links |
| `--accent-hover` | `#0891b2` (cyan-600) | Hover state |
| `--accent-subtle` | `rgba(6,182,212,0.1)` | Accent backgrounds |

### Semantic Colors

| Token | Value | Usage |
|---|---|---|
| `--success` | `#22c55e` (green-500) | Done, positive |
| `--warning` | `#eab308` (yellow-500) | Warnings, scores |
| `--error` | `#ef4444` (red-500) | Errors, urgent |
| `--info` | `#06b6d4` (cyan-500) | Info states |

> **Rule:** No purple, no blue-600 buttons, no neon glows. Cyan is the only accent.

---

## 3. Typography

### Font Stack

Load Satoshi via CDN and JetBrains Mono for code:
```html
<link href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

```css
--font-sans: 'Satoshi', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', monospace;
```

### Type Scale

| Role | Classes | Usage |
|---|---|---|
| Page title | `text-2xl font-bold tracking-tight` | Page headers |
| Section title | `text-lg font-medium` | Section headers |
| Card title | `text-sm font-medium` | Card headers |
| Body | `text-sm leading-relaxed` | Paragraphs |
| Caption | `text-xs` + muted color | Timestamps, metadata |
| Code/mono | `font-mono text-xs` | Technical data, bot commands |
| Label | `text-[11px] font-medium uppercase tracking-widest` + muted color | Section labels, column headers |

---

## 4. Spacing & Layout

### Sidebar
```
w-60 bg-slate-800/50 border-r border-slate-700/50
backdrop-blur-sm
flex flex-col py-6 px-4
```
- Fixed sidebar, scrollable main content
- Use `min-h-[100dvh]` on the flex container, NOT `h-screen`

### Main Content
```
flex-1 overflow-y-auto p-8
```

### Content Widths
- Full-width pages (backlog kanban): `max-w-6xl mx-auto`
- Reading pages (intel, PRD): `max-w-4xl mx-auto`

### Section Spacing
- Between sections: `space-y-8`
- Card groups: `gap-4`
- Card padding: `p-5`

---

## 5. Component Patterns

### Cards
```css
.card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 16px; /* rounded-2xl */
  padding: 20px;
  transition: border-color 0.2s ease;
}
.card:hover {
  border-color: var(--border);
}
```

Tailwind equivalent:
```
bg-slate-800 border border-slate-700/50 rounded-2xl p-5
hover:border-slate-600 transition-colors duration-200
```

### Navigation Links
```css
.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.15s ease;
}
.nav-link:hover {
  background: rgba(6,182,212,0.08);
  color: var(--text);
}
.nav-link.active {
  background: rgba(6,182,212,0.12);
  color: #06b6d4;
  border: 1px solid rgba(6,182,212,0.2);
}
```

- Use SVG icons (inline) instead of emoji for nav items
- Active state: subtle accent tint, NOT a solid color block

### Buttons

**Primary:**
```
bg-cyan-600 hover:bg-cyan-500 text-white
px-4 py-2 rounded-lg font-medium text-sm
transition-colors duration-150
```
With tactile press: `active:scale-[0.98] active:translate-y-[1px]`

**Secondary:**
```
bg-slate-700 hover:bg-slate-600 text-slate-200
border border-slate-600
px-4 py-2 rounded-lg font-medium text-sm
```

**Ghost:**
```
text-slate-400 hover:text-slate-200 hover:bg-slate-700/50
px-3 py-1.5 rounded-md text-sm
```

### Inputs
```
bg-slate-800 border border-slate-600 rounded-lg
px-4 py-2.5 text-sm text-white
placeholder:text-slate-500
focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20
```

### Status Indicators
- Use small colored dots (8px circles) instead of emoji for agent status
- `bg-green-400 rounded-full w-2 h-2` for active/running
- `bg-slate-500 rounded-full w-2 h-2` for idle

### Kanban Cards (Backlog)
```
bg-slate-800/80 border border-slate-700/50 rounded-xl p-4
hover:border-slate-600 transition-colors duration-200
```
- Column headers: uppercase tracking-widest label style
- Count badges: `bg-slate-700 text-slate-400 text-xs px-2 py-0.5 rounded-full`

### Empty States
```
border border-dashed border-slate-700 rounded-xl p-10 text-center
```
- Use a clean SVG illustration or icon, not emoji
- Subtitle with actionable hint

### Loading / Skeleton
```
bg-slate-700 rounded-md animate-pulse
```

---

## 6. Motion & Transitions

### Default Transition (CSS only, no JS libraries)
```css
transition: all 0.2s ease;
```

### Hover Effects
- Cards: border color shift
- Buttons: background shift + active press
- Nav links: background tint appearance

### Progress Bars
```css
.progress-bar {
  transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  border-radius: 999px;
  height: 6px;
}
```

### Page Content Load
```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
main > * {
  animation: fadeIn 0.3s ease-out both;
}
```

---

## 7. Navigation Sidebar

### Structure
- Logo: styled text with a small SVG bolt icon, not emoji
- Nav sections can be grouped with subtle `border-t border-slate-700/50` dividers
- Bottom: bot handle in `text-xs text-slate-600 font-mono`

### Nav Icons (inline SVG, replace all emoji)
Use simple 18x18 SVG icons. Recommended mappings:
- Intelligence: brain/circuit icon
- Backlog: inbox/stack icon
- Goals: target icon
- Career: briefcase icon
- Product OS: grid/layout icon

---

## 8. Forbidden Patterns

- No emoji anywhere in the UI (replace with SVG icons)
- No `#000000` pure black backgrounds
- No `bg-blue-600`/`bg-blue-700` solid accent blocks
- No `h-screen` (use `min-h-[100dvh]`)
- No Inter font (use Satoshi)
- No 3-column equal card grids for features
- No generic circular spinners
- No `location.reload()` after mutations (use DOM updates where practical)
- No purple/indigo accents
- No neon outer glows

---

## 9. Responsive Behavior

### Mobile (< 768px)
- Sidebar collapses to a top navigation bar or hamburger
- Kanban columns stack vertically
- Content uses `px-4` padding

### Desktop (>= 768px)
- Fixed sidebar + scrollable main content
- Kanban grid shows all columns

---

## 10. Dark Mode Refinements

The entire app is dark-only. Key refinements over generic gray:
- Use **slate** (blue-tinted dark) instead of **gray** (neutral dark) for a cooler, more premium feel
- Cards should feel like frosted glass: subtle border + slight backdrop differentiation
- Text hierarchy through 3 levels: `slate-50` (primary), `slate-400` (secondary), `slate-500` (tertiary)
- Borders are intentionally low-contrast (`slate-700/50`) to avoid harsh grid lines
