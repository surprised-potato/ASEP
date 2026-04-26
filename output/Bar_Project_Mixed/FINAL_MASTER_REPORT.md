# Mixed-Frame Building — Comprehensive Structural Report

## Table of Contents
- [Project Overview](#project-overview)
- [Part A: Standard Frame Structural Analysis](#part-a-standard-frame-structural-analysis)
  - [1. Truss Configuration](#1-truss-configuration)
  - [2. Applied Loads](#2-applied-loads)
  - [3. Load Case Summary](#3-load-case-summary)
  - [4. Deflection Check](#4-deflection-check)
  - [5. Optimized Member Selection](#5-optimized-member-selection)
  - [6. Substructure Design (Standard Frame)](#6-substructure-design-standard-frame)
- [Part B: Long-Span Frame Structural Analysis](#part-b-long-span-frame-structural-analysis)
  - [1. Truss Configuration (Long Span)](#1-truss-configuration-long-span)
  - [2. Load Case Summary (Long Span)](#2-load-case-summary-long-span)
  - [3. Deflection Check (Long Span)](#3-deflection-check-long-span)
  - [4. Optimized Member Selection (Long Span)](#4-optimized-member-selection-long-span)
  - [5. Substructure Design (Long Span)](#5-substructure-design-long-span)
- [Part C: Consolidated Bill of Materials](#part-c-consolidated-bill-of-materials)
  - [1. Summary of Quantities](#1-summary-of-quantities)
  - [2. Estimated Costs](#2-estimated-costs)
  - [3. Detailed Member Schedules](#3-detailed-member-schedules)

---

## Project Overview
**Project Description:** 21m Span Industrial Building
**Configuration:** 6 Frames total (5 Standard Frames + 1 Long-Span Frame)
**Standard Frame:** 21m Isosceles Howe Truss with 2 interior RC columns.
**Long-Span Frame:** 21m Isosceles Howe Truss with NO interior columns.

#### Overall Building Visualization
![Mixed Building Structure](./images/mixed_building_structure.png)

---

# Part A: Standard Frame Structural Analysis
*Derived from Bar_Project_RC_Final*

## 1. Truss Configuration

| Parameter | Value |
|:---|:---|
| Span | 21.0 m |
| End Depth | 0.0 m (Isosceles Triangle) |
| Depth at Midspan (Peak) | 2.0 m |
| Bottom Chord | Level at y = 0.0 m |
| Column Height | 4.0 m (Fixed base, RC columns) |
| Panels | 21 @ 1.0 m |
| Type | Isosceles Triangle Howe Truss |
| Chord Construction | Double Angles (2L) — back-to-back for gusset plates |
| Web Construction | Square or Rectangular Pipe (Cold Rolled Tubular Steel) |
| Connections | Site-welded using 6mm or 10mm gusset plates |
| Supports | 4 fixed-base RC columns: 2 exterior + 2 interior |
| Interior Column Locations | Exactly at 7.0 m and 14.0 m |
| Steel Grade | A36 (Fy = 36 ksi) |
| Concrete Grade | 21 MPa (3000 psi) |

#### Standard Frame Truss Diagram
![Standard Frame Truss Diagram](./images/frame_structure.png)

## 2. Applied Loads

### Gravity Loads

| Component | Value |
|:---|:---|
| Dead Load (Roof + Ceiling) | 3.0 kN/m (0.5 kPa x 6m trib.) |
| Truss + RC Col Self-Weight | 3.057 kN/m |
| **Total Dead Load (D)** | **3.500 kN/m** |
| **Live Load (L)** | **3.600 kN/m** (0.6 kPa x 6m trib.) |

### Earthquake (Static Method — NSCP)

| Parameter | Value |
|:---|:---|
| Seismic Coefficient (Cs) | 0.2 (Zone 4, Soil Type D, R=8.5) |
| Seismic Weight (W) | 73.50 kN |
| Base Shear (V = Cs x W) | **14.70 kN** |
| Lateral q per exterior column (V / 4 / h) | 0.92 kN/m |

### Wind Load

| Parameter | Value |
|:---|:---|
| Wind Pressure | 800 Pa |
| Tributary Width | 6.0 m |
| Lateral Load on Ext. Columns | **4.8 kN/m** (800 Pa x 6m) |

## 3. Load Case Summary

### Axial Forces (kN) per Load Case

| Member Group | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | Governing |
|:---|:---|:---|:---|:---|
| Top Chord | -94.41 | -74.16 | -40.95 | -94.41 |
| Bottom Chord | 90.78 | 71.14 | 40.42 | 90.78 |
| Vertical Webs | -53.60 | -42.10 | -23.24 | -53.60 |
| Diagonal Webs | 47.54 | 37.36 | 20.75 | 47.54 |
| Exterior Columns | 22.56 | 17.71 | 9.73 | 22.56 |
| Interior Columns | 84.02 | 65.92 | 36.07 | 84.02 |

#### Axial Forces Diagram (Standard Frame)
![Axial Forces Diagram (Standard Frame)](./images/frame_axial.png)

### Support Reactions per Load Case

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | Governing |
|:---|:---|:---|:---|:---|
| Vertical (Fy) — Max | 84.02 | 65.92 | 36.07 | 84.02 |
| Vertical (Fy) — Exterior | 22.56 | 17.71 | 9.73 | 22.56 |
| Vertical (Fy) — Interior | 84.02 | 65.92 | 36.07 | 84.02 |
| Horizontal (Fx) — Max | 2.15 | 3.80 | 16.15 | 16.15 |

> Governing Vertical Reaction (Exterior): 22.56 kN
> Governing Vertical Reaction (Interior): 84.02 kN
> Governing Horizontal Reaction: 16.15 kN

#### Support Reactions Diagram (Standard Frame)
![Support Reactions Diagram (Standard Frame)](./images/frame_reactions.png)

## 4. Deflection Check

- **Max Deflection:** 0.01 mm
- **Deflection Ratio (L/d):** 1999505 (Target > 240) PASS

#### Deflection Diagram (Standard Frame)
![Deflection Diagram (Standard Frame)](./images/frame_displacement.png)

## 5. Optimized Member Selection (Governing Forces)

| Group | Selected Shape (Standard / Comm.) | Weight | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
|:---|:---|:---|:---|:---|:---|:---|
| Exterior Columns | 400x400 RC | 384.0 kg/m | 0.0 | 22.56 | 0.00 | Gravity Only |
| Interior Columns | 400x400 RC | 384.0 kg/m | 0.0 | 84.02 | 0.00 | Gravity Only |
| Top Chord | 2L2X2X1/8 | 3.3 plf | 64.6 | -94.41 | 98.24 | Gravity Only |
| Bottom Chord | 2L2X2X1/8 | 3.3 plf | 63.5 | 90.78 | 141.53 | Gravity Only |
| Vertical Webs | HSS2X2X1/8 / Square Pipe 51x51x3.2mm | 3.0 plf | 103.5 | -53.60 | 68.90 | Gravity Only |
| Diagonal Webs | HSS2X1X1/8 / Rect. Pipe 51x25x3.2mm | 2.2 plf | 225.7 | 47.54 | 87.63 | Gravity Only |

- Total Steel Weight: 401.0 kg
- Total Concrete Weight (Cols): 6144.0 kg

## 6. Substructure Design (Standard Frame)

### Exterior Column Foundation (x2)
Column: 400x400 RC, Height: 4.00 m, Pu = 22.56 kN

| Parameter | Value |
|:---|:---|
| RC Column Section | 400 mm x 400 mm |
| Vertical Reinforcement | 8 — 16mm bars (Grade 40) |
| Lateral Ties | 10mm @ 200mm O.C. |
| Isolated Footing | 1.0 m x 1.0 m x 0.40 m |
| Bottom Rebar | 12mm @ 200mm O.C. (Both Ways) |

### Interior Column Foundation (x2)
Column: 400x400 RC, Height: 4.00 m, Pu = 84.02 kN

| Parameter | Value |
|:---|:---|
| RC Column Section | 400 mm x 400 mm |
| Vertical Reinforcement | 8 — 16mm bars (Grade 40) |
| Lateral Ties | 10mm @ 200mm O.C. |
| Isolated Footing | 1.0 m x 1.0 m x 0.40 m |
| Bottom Rebar | 12mm @ 200mm O.C. (Both Ways) |

---

# Part B: Long-Span Frame Structural Analysis
*Derived from Bar_Project_Long_Span*

## 1. Truss Configuration (Long Span)

| Parameter | Value |
|:---|:---|
| Span | 21.0 m |
| End Depth | 0.0 m (Isosceles Triangle) |
| Depth at Midspan (Peak) | 2.0 m |
| Bottom Chord | Level at y = 0.0 m |
| Column Height | 4.0 m (Fixed base, RC columns) |
| Panels | 21 @ 1.0 m |
| Type | Isosceles Triangle Howe Truss |
| Chord Construction | Double Angles (2L) — back-to-back for gusset plates |
| Web Construction | Square or Rectangular Pipe (Cold Rolled Tubular Steel) |
| Connections | Site-welded using 6mm or 10mm gusset plates |
| Supports | 2 fixed-base RC columns: Exterior only (Long Span) |
| Steel Grade | A36 (Fy = 36 ksi) |

#### Long-Span Frame Truss Diagram
![Long-Span Frame Truss Diagram](./images/longitudinal_structure.png)

## 2. Load Case Summary (Long Span)

### Axial Forces (kN) per Load Case

| Member Group | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | Governing |
|:---|:---|:---|:---|:---|
| Top Chord | -542.34 | -424.73 | -228.70 | -542.34 |
| Bottom Chord | 512.54 | 401.39 | 216.13 | 512.54 |
| Vertical Webs | 45.63 | 35.73 | 19.24 | 45.63 |
| Diagonal Webs | 77.75 | 60.89 | 32.79 | 77.75 |
| Exterior Columns | 106.37 | 83.30 | 44.86 | 106.37 |

#### Axial Forces Diagram (Long-Span Frame)
![Axial Forces Diagram (Long-Span Frame)](./images/longitudinal_axial.png)

### Support Reactions (Long Span)

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | Governing |
|:---|:---|:---|:---|:---|
| Vertical (Fy) — Max | 106.37 | 83.30 | 44.86 | 106.37 |
| Vertical (Fy) — Exterior | 106.37 | 83.30 | 44.86 | 106.37 |

> Governing Vertical Reaction (Exterior): 106.37 kN
> Governing Horizontal Reaction: 27.33 kN

#### Support Reactions Diagram (Long-Span Frame)
![Support Reactions Diagram (Long-Span Frame)](./images/longitudinal_reactions.png)

## 3. Deflection Check (Long Span)

- **Max Deflection:** 0.07 mm
- **Deflection Ratio (L/d):** 302814 (Target > 240) PASS

#### Deflection Diagram (Long-Span Frame)
![Deflection Diagram (Long-Span Frame)](./images/longitudinal_displacement.png)

## 4. Optimized Member Selection (Long Span)

| Group | Selected Shape (Standard / Comm.) | Weight | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
|:---|:---|:---|:---|:---|:---|:---|
| Exterior Columns | 400x400 RC | 384.0 kg/m | 0.0 | 106.37 | 0.00 | Gravity Only |
| Top Chord | 2L3X3X3/8 | 14.4 plf | 44.0 | -542.34 | 549.16 | Gravity Only |
| Bottom Chord | 2L3-1/2X3-1/2X1/4 | 11.6 plf | 36.1 | 512.54 | 490.02 | Gravity Only |
| Vertical Webs | HSS2X1X1/8 / Rect. Pipe 51x25x3.2mm | 2.2 plf | 201.9 | 45.63 | 87.63 | Gravity Only |
| Diagonal Webs | HSS2X1X1/8 / Rect. Pipe 51x25x3.2mm | 2.2 plf | 225.7 | 77.75 | 87.63 | Gravity Only |

- Total Steel Weight: 986.7 kg
- Total Concrete Weight (Cols): 3072.0 kg

## 5. Substructure Design (Long Span)

### Exterior Column Foundation (x2)
Column: 400x400 RC, Height: 4.00 m, Pu = 106.37 kN

| Parameter | Value |
|:---|:---|
| RC Column Section | 400 mm x 400 mm |
| Vertical Reinforcement | 8 — 16mm bars (Grade 40) |
| Lateral Ties | 10mm @ 200mm O.C. |
| Isolated Footing | 1.0 m x 1.0 m x 0.40 m |
| Bottom Rebar | 12mm @ 200mm O.C. (Both Ways) |

#### Tie Beam Details
- Size: 300mm x 400mm RC Tie Beam
- Reinforcement: 4 - 16mm main bars with 10mm @ 200mm stirrups
- Purpose: Seismic connectivity between footings along building length.

---

# Part C: Consolidated Bill of Materials
*Derived from Bar_Project_Mixed and combined with Standard/Long-Span schedules*

**Project:** Bar building with 5 Standard Frames and 1 Long-Span Frame
**Configuration:** 6 Frames total, 21m Span, 4m Height.

- Standard Frames (1-5): Isosceles Howe with 2 interior columns.
- Long-Span Frame (6): Isosceles Howe with NO interior columns.
- Tie Beams: 300x400mm RC beams connecting all exterior footings (126m total length).

## 1. Summary of Quantities

| Material Type | Unit | 5x Standard | 1x Long-Span | Tie Beams | **Grand Total** |
|:---|:---|:---|:---|:---|:---|
| Structural Steel | kg | 2005.0 | 986.7 | - | **2991.7** |
| Concrete (21 MPa) | m3 | 20.80 | 2.08 | 15.12 | **38.00** |
| Reinforcement | kg | 1468.5 | 146.9 | 1343.2 | **2958.6** |

## 2. Estimated Costs

| Material | Total Qty | Unit | Unit Rate | Total (PHP) |
|:---|:---|:---|:---|:---|
| Steel | 2,991.7 | kg | 60.00 | 179,502.00 |
| Concrete | 38.00 | m3 | 5,500.00 | 209,000.00 |
| Rebar | 2,958.6 | kg | 55.00 | 162,723.00 |
| **TOTAL** | | | | **551,225.00** |

## 3. Detailed Member Schedules

### A. Standard Frame (Frames 1-5) - Per Frame
| Group | Shape | Total Length | Unit Weight | Total Weight |
|:---|:---|:---|:---|:---|
| Top Chord | `2L 2X2X1/8` | 21.36 m | 4.91 kg/m | 104.9 kg |
| Bottom Chord | `2L 2X2X1/8` | 21.00 m | 4.91 kg/m | 103.1 kg |
| Vertical Webs | `Square Pipe 51x51` | 20.95 m | 4.54 kg/m | 95.1 kg |
| Diagonal Webs | `Rect. Pipe 51x25` | 29.89 m | 3.27 kg/m | 97.9 kg |
| **Total per Frame** | | | | **401.0 kg** |

### B. Long-Span Frame (Frame 6 Only)
| Group | Shape | Total Length | Unit Weight | Total Weight |
|:---|:---|:---|:---|:---|
| Top Chord | `2L 3X3X3/8` | 21.36 m | 21.4 kg/m | 457.1 kg |
| Bottom Chord | `2L 3-1/2X3-1/2X1/4` | 21.00 m | 17.3 kg/m | 363.3 kg |
| Vertical Webs | `Rect. Pipe 51x25` | 21.00 m | 3.27 kg/m | 68.7 kg |
| Diagonal Webs | `Rect. Pipe 51x25` | 29.89 m | 3.27 kg/m | 97.7 kg |
| **Total per Frame** | | | | **986.7 kg** |

## 4. Discussion

- Frame 6 (Long Span) requires significantly heavier steel sections (`2L3x3x3/8` vs `2L2x2x1/8`) to bridge 21m without interior columns.
- Tie beams (300x400) connect all exterior footings along the building length (21m per bay/frame).
- All designs maintain L/240 deflection at service loads.
