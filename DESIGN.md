---
name: UrbanFlow
description: A city atlas for historical NYC taxi mobility.
colors:
  forest: "#216e55"
  forest-hover: "#15553e"
  navigation: "#123d32"
  navigation-hover: "#214c3e"
  navigation-text: "#c6d8cb"
  navigation-selected-text: "#173d2c"
  lime: "#e1ed92"
  terracotta: "#bf612b"
  mineral-blue: "#3878a3"
  plum: "#8f6d9f"
  ochre: "#a59943"
  slate-green: "#65837c"
  ground: "#f4f5f0"
  surface: "#ffffff"
  topbar: "#fbfcf8"
  ink: "#172b26"
  muted: "#52665e"
  line: "#dce3dc"
  field-text: "#344b40"
  outline: "#cbd5c9"
  hover: "#e9eee3"
  chip: "#e4ecd9"
  insight: "#e4ecd7"
  water: "#e7efed"
  error: "#a93632"
typography:
  headline:
    fontFamily: "'DM Sans Variable', sans-serif"
    fontSize: "clamp(25px, 2.2vw, 32px)"
    fontWeight: 600
    lineHeight: 1.22
    letterSpacing: "-0.85px"
  title:
    fontFamily: "'DM Sans Variable', sans-serif"
    fontSize: "14px"
    fontWeight: 600
    letterSpacing: "-0.15px"
  body:
    fontFamily: "'DM Sans Variable', sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "'DM Sans Variable', sans-serif"
    fontSize: "11px"
    fontWeight: 500
  metric:
    fontFamily: "'DM Sans Variable', sans-serif"
    fontSize: "clamp(22px, 2.25vw, 34px)"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-1px"
rounded:
  chip: "5px"
  control: "7px"
  workspace: "8px"
  banner: "10px"
  panel: "12px"
spacing:
  inline: "7px"
  filter-gap: "10px"
  compact-gap: "12px"
  responsive-gap: "16px"
  mobile-gap: "17px"
  panel-gap: "22px"
  section-gap: "25px"
  workspace-inset: "32px"
components:
  button-primary:
    backgroundColor: "{colors.forest}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "9px 13px"
  button-primary-hover:
    backgroundColor: "{colors.forest-hover}"
  button-outline:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.field-text}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "9px 13px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "9px 13px"
  filter-select:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.field-text}"
    rounded: "{rounded.control}"
    padding: "8px 28px 8px 12px"
  selection-chip:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
    padding: "6px 9px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
  navigation-item:
    textColor: "{colors.navigation-text}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  navigation-item-active:
    backgroundColor: "{colors.lime}"
    textColor: "{colors.navigation-selected-text}"
---

# Design System: UrbanFlow

## Overview

**Creative North Star: "City atlas"**

UrbanFlow is a clear, measured analytical workspace: an ink-green navigation rail anchors a warm ivory ground, while flat white surfaces hold charts, ranked lists and actual NYC taxi-zone geometry. Cartographic labels and restrained mineral data colours make the evidence the focal point.

This document merges the original city-atlas direction with the shipped implementation. Visual decisions were delegated by the user. Keep the established civic, precise character and compact analytical density as new screens are added.

**Key Characteristics:**

- Dark green navigation and a lime active destination.
- Warm ground, white panels and fine structural borders.
- Self-hosted DM Sans with clear numeric hierarchy.
- Coordinated geographic selection and ranked evidence.

## Colors

The palette pairs civic greens and warm neutrals with distinct mineral colours for data. Frontmatter is the normative source for reusable primitives.

### Primary

- **Forest:** primary actions, links and the first chart series; its deeper hover shade signals interaction.
- **Ink green navigation:** persistent orientation, with a lighter green hover and lime active destination.
- **Lime:** active navigation and text selection, rather than a general chart fill.

### Secondary

- **Terracotta:** second chart series and the selected map-zone outline.
- **Mineral blue:** third chart series.
- **Plum, ochre and slate green:** subsequent categorical series in that order.

### Neutral

- **Ivory ground:** the workspace canvas.
- **White surface:** chart panels, controls and tables; the top bar has a subtly tinted surface.
- **Ink and muted green:** primary text and supporting labels respectively.
- **Fine green-grey line:** panel boundaries and structural dividers.
- **Soft chip and insight greens:** selected-filter context and explanatory banners.
- **Water:** the map background, preserving legibility of real zone polygons.

Use error red alongside an icon, explanatory text and a retry action. Do not derive unimplemented warning states from the provisional design.

**The Shared Series Rule.** Reuse the chart palette in its established order; geographic intensity uses its separate sequential green scale.

## Typography

**Display and body font:** DM Sans Variable, self-hosted through Fontsource, with a sans-serif fallback. There is no separate display face or general monospace treatment; even the footer's run metadata uses the inherited family.

The type is compact and matter-of-fact. Page headlines lead, metrics are large but lighter, and chart titles stay modest. Use tabular numerals for metrics, ranks and numeric table columns.

### Hierarchy

- **Headline:** the frontmatter headline role; mobile fixes its size to (27px).
- **Panel title:** the title role, reduced to (13px) in the intermediate desktop layout and restored on mobile.
- **Body:** page descriptions use the body role; explanatory prose varies by context, with longer explanation blocks capped at (85ch).
- **Label:** controls and data rows use compact labels. Chart details and metadata use (9-10px), with units and qualifiers kept beside their measurements.
- **Metric:** the metric role; intermediate desktop uses (26px), mobile (29px).

## Layout

The desktop shell is a sidebar plus a flexible main workspace. The rail is (238px), sticky and viewport-height. Main content is capped at (1660px), centered within its available space, with (23px) top padding and the frontmatter workspace inset on each side. Above it is a bordered, subtly tinted top bar. The global filters sit in normal document flow before the title; they are not sticky.

The common panel gap and padding anchor is the frontmatter panel-gap value. Panel headings use (22px 22px 6px); their content has context-specific insets rather than one universal card padding. The overview uses a (1.63:1) column relationship with a minimum (280px) supporting column; geography uses (1.9:1) with a minimum (230px) supporting column. Two-column comparisons use equal widths. The KPI strip is a divided row, not four separate cards.

Responsive behaviour follows the implemented breakpoints:

- At (1500px) and above, main horizontal insets grow to (42px).
- At (1200px) and below, the rail narrows to (206px), workspace insets to (23px), and selected panel typography tightens.
- At (960px) and below, overview and geography become single-column; KPIs become a two-by-two grid.
- At (700px) and below, the rail becomes a top header with horizontally scrollable navigation. Main insets become (16px), all chart grids stack, dates occupy a full filter row, and panel gaps become the frontmatter mobile-gap value.

Tables scroll within their own containers. Maps retain deliberate working heights: overview (369px), large geography (550px), changing to (380px) and (470px) on mobile. Preserve the body minimum width of (320px).

## Elevation & Depth

The workspace is flat at rest. Tonal differences, fine borders and whitespace separate content; panels do not cast shadows. The map's floating hover popup is the exception, using a restrained shadow (documented in the sidecar) to distinguish temporary information from the underlying geometry.

**The Flat Surface Rule.** Use borders and tonal separation for analytical panels; reserve the existing popup shadow for transient map information.

## Shapes

Gently curved rectangles are the recurring form: panels use the frontmatter panel radius, controls and navigation the control radius, filter chips the chip radius, and informational banners the banner radius. Panels clip their contents to the rounded boundary. Fine borders are (1px); small round status dots and the loading indicator provide the circular exceptions.

## Components

### Buttons

Compact, labelled actions have a minimum height of (37px), an inline icon gap of (7px), and the shared label role. Primary actions use forest and white; outline actions use white, a green-grey border and field text; ghost actions use muted text on a transparent ground. Primary hover deepens forest, while outline and ghost hover use the soft hover surface. Background transitions take (150ms). Disabled buttons and fields retain their shape at (0.5) opacity with a not-allowed cursor.

### Inputs / Fields

Date groups and selects are white with fine borders, the control radius and a minimum height of (39px). Selects use the frontmatter padding; date groups use (8px 12px). Date fields form one grouped range. All interactive elements receive a visible forest outline (2px) with an offset of (4px); sidebar links use lime for contrast. Comparison date inputs are a larger contextual variant, with (16px) text and (6px) corners.

### Chips

The selected-zone chip uses the soft chip ground, ink text, a small clear button and a compact label. It reflects the shared zone selection and provides a direct way to remove it.

### Cards / Containers

White panels contain a title, optional short qualifier, optional action and the visualization or table. Keep titles aligned to their content and use modest link actions. The KPI strip stays directly on the workspace with horizontal and vertical dividers. Explanatory banners and the processing strip use a soft green ground without added elevation.

### Navigation

The desktop rail uses compact (12px) labels, (44px) minimum-height links and muted green text. Hover lightens the green ground; active links become lime with dark text, increased weight and a small trailing dot. Mobile uses (35px) links and horizontal overflow; the trailing dot is omitted. Keep all destinations available.

### Charts and tables

Charts share DM Sans, muted labels and the categorical palette. The common line has a (2.5px) stroke and a restrained green area fill at (0.07) opacity; grid lines are pale and dashed. Charts resize with their containers. Default chart entry animation is (350ms); reduced-motion preference disables it and CSS transitions/animations. Tables use lightly tinted headers, fine row separators, subtle hover and right-aligned tabular measurements.

### Taxi-zone atlas

Use actual TLC geometry in geographic coordinates. The sequential map legend runs from fewer pickups to the current maximum. A selected polygon gains a terracotta outline (2.5px); zones outside the current filter fade. Hover labels report a zone and its values or out-of-selection status. Polygon selection, the ranked list, details and zone filter must agree. Keep the parallel zone list available when map rendering fails or a user selects by keyboard.

### Request states

Loading uses a circular forest-accent indicator with a clear status message; empty selection states explain how to recover. Failed analysis includes explanatory text and a labelled retry action. Preserve text and semantics alongside state colour.

## Do's and Don'ts

### Do:

- **Do** preserve the city-atlas hierarchy: dark navigation, warm ground, flat white evidence surfaces.
- **Do** reuse DM Sans and tabular numerals for comparable measurements.
- **Do** keep chart colours, geographic selection and filter context consistent across sections.
- **Do** retain visible keyboard focus, explanatory request states and reduced-motion behaviour.

### Don't:

- **Don't** replace actual taxi-zone geography with decorative or invented map shapes.
- **Don't** turn the divided KPI strip into a collection of elevated tiles.
- **Don't** add decorative panel shadows or unrelated display fonts to this restrained workspace.
- **Don't** communicate a selection, error or data category through colour alone.
