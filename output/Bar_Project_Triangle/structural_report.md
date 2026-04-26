# Bar Project — Structural Optimization Report

## 1. Truss Configuration

| Parameter | Value |
| --- | --- |
| Span | `21.0 m` |
| Depth at Ends | `0.0 m` (Isosceles Triangle) |
| Depth at Midspan (Peak) | `3.0 m` |
| Bottom Chord | **Level at y = 0.0 m** |
| Column Height | `6.0 m` (Fixed base, all 4 columns) |
| Panels | `21 @ 1.0 m` |
| Type | **Isosceles Triangle Howe Truss** |
| Web Pattern | Howe — diagonals slope outward from center (compression) |
| Supports | **4 fixed-base steel columns**: 2 exterior + 2 interior |
| Interior Column Locations | Exactly at 7.0 m and 14.0 m |
| Steel Grade | `A36 (Fy = 36 ksi)` |

## 2. Applied Loads

### Gravity Loads

| Component | Value |
| --- | --- |
| Dead Load (Roof + Ceiling) | `3.0 kN/m` (0.5 kPa × 6m trib.) |
| Truss Self-Weight | `0.388 kN/m` (830.2 kg / 24m) |
| **Total Dead Load (D)** | **`3.388 kN/m`** |
| **Live Load (L)** | **`3.600 kN/m`** (0.6 kPa × 6m trib.) |

### Earthquake (Static Method — NSCP)

| Parameter | Value |
| --- | --- |
| Seismic Coefficient ($C_s$) | `0.2` (Zone 4, Soil Type D, R=8.5) |
| Seismic Weight ($W$) | `71.14 kN` |
| Base Shear ($V = C_s \times W$) | **`14.23 kN`** |
| Lateral q per exterior column ($V / 4 / h$) | `0.59 kN/m` |

### Wind Load

| Parameter | Value |
| --- | --- |
| Wind Pressure | `800 Pa` |
| Tributary Width | `6.0 m` |
| Lateral Load on Ext. Columns | **`4.8 kN/m`** (800 Pa × 6m) |

## 3. Load Case Summary

### Axial Forces (kN) per Load Case

| Member Group | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Top Chord | -73.04 | -57.12 | -31.36 | **0.00** |
| Bottom Chord | 68.62 | 53.45 | 32.32 | **0.00** |
| Vertical Webs | -52.10 | -40.76 | -22.51 | **0.00** |
| Diagonal Webs | 40.97 | 32.08 | 17.88 | **0.00** |
| Exterior Columns | 24.79 | 19.38 | 10.57 | **0.00** |
| Interior Columns | 82.75 | 64.68 | 35.19 | **0.00** |

### Support Reactions per Load Case

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Vertical ($F_y$) — Max | 82.75 | 64.68 | 35.19 | **0.00** |
| Vertical ($F_y$) — Exterior | 24.79 | 19.38 | 10.57 | **24.79** |
| Vertical ($F_y$) — Interior | 82.75 | 64.68 | 35.19 | **82.75** |
| Horizontal ($F_x$) — Max | 0.26 | 3.09 | 23.54 | **23.54** |

> **Governing Vertical Reaction (Exterior):** `24.79 kN`
> **Governing Vertical Reaction (Interior):** `82.75 kN`
> **Governing Horizontal Reaction:** `23.54 kN` ()

## 4. Deflection Check

- **Max Deflection:** `0.01 mm`
- **Deflection Ratio (L/d):** `4027734` (Target > 240) ✅ PASS

## 5. Optimized Member Selection (Governing Forces)

| Group | Selected Shape | Weight (plf) | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
| --- | --- | --- | --- | --- | --- | --- |
| Top Chord | `WT3X4.25` | 4.2 | 48.3 | -31.36 | 160.62 | Gravity Only |
| Bottom Chord | `WT3X4.25` | 4.2 | 46.4 | 68.62 | 181.59 | Gravity Only |
| Vertical Webs | `HSS2-1/4X2-1/4X1/8` | 3.5 | 136.9 | -22.51 | 51.29 | Gravity Only |
| Diagonal Webs | `HSS1-1/2X1-1/2X1/8` | 2.2 | 223.5 | 40.97 | 87.63 | Gravity Only |
| Exterior Columns | `W6X15` | 15.0 | 162.9 | 24.79 | 167.74 | Gravity Only |
| Interior Columns | `W6X15` | 15.0 | 162.9 | 82.75 | 167.74 | Gravity Only |

- **Total Steel Weight:** `830.2 kg`
- **Estimated Steel Cost:** `PHP 49,810.17` (@ PHP 60/kg)

## 6. Substructure Design

Design assumptions:

| Parameter | Value |
| --- | --- |
| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |
| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |
| Allowable Soil Bearing ($q_a$) | `100 kPa` |


### Exterior Column Foundation (×2)

**Column:** `W6X15`, Height: `6.00 m`, $P_u$ = `24.79 kN`

#### Steel Base Plate

| Parameter | Value |
| --- | --- |
| Base Plate (B × N) | `252 mm × 252 mm` |
| Thickness ($t_p$) | `10 mm` |
| Bearing Stress | `0.39 MPa` ≤ `11.60 MPa` (✅) |
| Anchor Bolts | `4 — 16mm Ø` |

#### Concrete Pedestal

| Parameter | Value |
| --- | --- |
| Dimensions | `400 mm × 400 mm × 600 mm` |
| Main Reinforcement | `4 — 16mm Ø bars` |
| Lateral Ties | `10mm Ø @ 200mm O.C.` |

#### Isolated Square Footing

| Parameter | Value |
| --- | --- |
| Dimensions | `1.0 m × 1.0 m × 0.30 m` |
| Bearing Pressure | `16.5 kPa` ≤ `100 kPa` ✅ |
| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |


### Interior Column Foundation (×2)

**Column:** `W6X15`, Height: `6.00 m`, $P_u$ = `82.75 kN`

#### Steel Base Plate

| Parameter | Value |
| --- | --- |
| Base Plate (B × N) | `252 mm × 252 mm` |
| Thickness ($t_p$) | `10 mm` |
| Bearing Stress | `1.30 MPa` ≤ `11.60 MPa` (✅) |
| Anchor Bolts | `4 — 16mm Ø` |

#### Concrete Pedestal

| Parameter | Value |
| --- | --- |
| Dimensions | `400 mm × 400 mm × 600 mm` |
| Main Reinforcement | `4 — 16mm Ø bars` |
| Lateral Ties | `10mm Ø @ 200mm O.C.` |

#### Isolated Square Footing

| Parameter | Value |
| --- | --- |
| Dimensions | `1.0 m × 1.0 m × 0.30 m` |
| Bearing Pressure | `55.2 kPa` ≤ `100 kPa` ✅ |
| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |

## 7. Structural Plots

#### Structure & Applied Loads (Gravity)
![Structure & Applied Loads (Gravity)](images/bar_structure.png)

#### Axial Forces (Gravity)
![Axial Forces (Gravity)](images/bar_axial.png)

#### Deflection (Gravity)
![Deflection (Gravity)](images/bar_displacement.png)

#### Support Reactions (Gravity)
![Support Reactions (Gravity)](images/bar_reactions.png)

#### Structure & Loads (Wind Case)
![Structure & Loads (Wind Case)](images/bar_wind_structure.png)

#### Axial Forces (Wind Case)
![Axial Forces (Wind Case)](images/bar_wind_axial.png)

#### Reactions (Wind Case)
![Reactions (Wind Case)](images/bar_wind_reactions.png)
