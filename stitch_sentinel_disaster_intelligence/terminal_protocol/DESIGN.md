---
name: Terminal Protocol
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c4c7c8'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8e9192'
  outline-variant: '#444748'
  surface-tint: '#c6c6c7'
  primary: '#ffffff'
  on-primary: '#2f3131'
  primary-container: '#e2e2e2'
  on-primary-container: '#636565'
  inverse-primary: '#5d5f5f'
  secondary: '#ffb4a8'
  on-secondary: '#690100'
  secondary-container: '#ff5540'
  on-secondary-container: '#5c0000'
  tertiary: '#ffffff'
  on-tertiary: '#303030'
  tertiary-container: '#e4e2e1'
  on-tertiary-container: '#656464'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c7'
  on-primary-fixed: '#1a1c1c'
  on-primary-fixed-variant: '#454747'
  secondary-fixed: '#ffdad4'
  secondary-fixed-dim: '#ffb4a8'
  on-secondary-fixed: '#410000'
  on-secondary-fixed-variant: '#930100'
  tertiary-fixed: '#e4e2e1'
  tertiary-fixed-dim: '#c8c6c5'
  on-tertiary-fixed: '#1b1c1c'
  on-tertiary-fixed-variant: '#474746'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0.02em
  body-lg:
    fontFamily: JetBrains Mono
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: -0.01em
  body-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0em
  data-tabular:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.1em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.2'
spacing:
  unit: 4px
  container-margin: 24px
  gutter: 1px
  sidebar-width: 64px
  data-row-height: 32px
---

## Brand & Style

The design system is engineered for high-stakes environments where clarity and speed of data ingestion are paramount. The aesthetic is a fusion of **Military-Grade Brutalism** and **High-End Fintech Terminal** design. It prioritizes function over form, utilizing a strictly minimalist framework that eliminates all visual noise to focus on critical telemetry and disaster intelligence.

The emotional response is one of absolute authority, precision, and urgency. By utilizing a "Dark Mode First" approach with stark contrast, the interface minimizes eye strain during long-term monitoring while ensuring that critical alerts command immediate attention. The style avoids all decorative trends like gradients or soft shadows in favor of hard edges, fixed-width data points, and structural integrity.

## Colors

The palette is intentionally restricted to maintain a "heads-up display" (HUD) feel. 

- **Primary Background (#0A0A0A):** Deep black provides the foundation for high-contrast data visualization.
- **Surface & Layers (#1A1A1A, #262626):** Slate greys are used exclusively for structural separation and container backgrounds.
- **Typography & Details (#FFFFFF):** Crisp white is used for all primary content to ensure maximum legibility.
- **Critical Alert (#FF0000):** Stark crimson is reserved strictly for destructive actions, emergency state changes, or critical disaster alerts. It must never be used for decorative purposes.

## Typography

This design system utilizes a dual-typeface strategy. **Inter** provides a sterile, authoritative voice for headers and structural wayfinding. **JetBrains Mono** is utilized for all data, telemetry, and body content, ensuring that alphanumeric characters remain distinct and perfectly aligned in dense tables.

All labels and small headers should favor `uppercase` with increased letter spacing to emulate military hardware markings. High data density is achieved through the use of monospaced fonts, allowing users to scan columns of numbers with mathematical precision.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy rooted in a 4px base unit. Visual separation is achieved through thin 1px borders rather than wide gutters, maximizing the available "data real estate."

- **Sidebar:** An ultra-slim, 64px persistent sidebar houses icon-only navigation, prioritizing the workspace.
- **Data Density:** Rows in tables are kept to a rigid 32px or 40px height to maximize the information displayed on a single screen.
- **Breakpoints:**
    - **Desktop (1440px+):** Multi-column telemetry view with persistent inspector panels.
    - **Tablet (768px - 1439px):** Collapsible inspector panels; main data grid remains primary.
    - **Mobile (<767px):** Single column stack; data tables convert to horizontal-scroll lists or simplified cards.

## Elevation & Depth

In this design system, depth is conveyed through **Tonal Layering** and **Hard Outlines**. 

- **No Shadows:** Shadows are strictly prohibited. 
- **Z-Axis:** Elevation is represented by shifting background colors. The base background is `#0A0A0A`, while elevated modals or floating panels use `#1A1A1A`. 
- **Borders:** Every container must have a 1px or 2px solid border (`#262626`). This creates a "blueprint" or "technical drawing" feel. 
- **Contrast:** Focus states are indicated by swapping colors (e.g., a white background with black text) rather than traditional glows or lifts.

## Shapes

The shape language is **strictly geometric**. 

- **Corner Radius:** 0px (Sharp) for all primary containers, buttons, and input fields.
- **Exceptions:** A 2px radius may be used for internal status indicators or micro-chips to provide a subtle visual distinction from structural elements, but never for primary UI components.
- **Lines:** All lines are either 1px or 2px. No feathered edges or variable widths.

## Components

- **Buttons:** Rectangular, sharp-edged. Primary buttons use a white background with black text. Secondary buttons use a black background with a 1px white border. No hover transitions; state changes must be instantaneous.
- **Data Tables:** The core of the system. 1px borders between all cells. Header cells use `label-caps` typography with a `#1A1A1A` background.
- **Input Fields:** Flat, 1px white border on focus. Placeholders use `#555555`. No rounded corners.
- **Charts:** Stark grid lines using `#262626`. Data lines are 2px wide. Use white for primary data and red only for threshold breaches.
- **Chips/Status:** Small, rectangular boxes. "Active" status uses a white outline; "Critical" status uses a solid `#FF0000` background with white text.
- **Sidebar:** Persistent, dark grey (`#0A0A0A`) with a 1px right border (`#262626`). Icons are 20px, stroke-based, and pure white.