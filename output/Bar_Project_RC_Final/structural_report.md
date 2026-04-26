# Bar Project — Structural Optimization Report

## 1. Truss Configuration

| Parameter | Value |
| --- | --- |
| Span | `21.0 m` |
| End Depth | `0.0 m` (Isosceles Triangle) |
| Depth at Midspan (Peak) | `2.0 m` |
| Bottom Chord | **Level at y = 0.0 m** |
| Column Height | `4.0 m` (Fixed base, RC columns) |
| Panels | `21 @ 1.0 m` |
| Type | **Isosceles Triangle Howe Truss** |
| Chord Construction | **Double Angles (2L)** — back-to-back for gusset plates |
| Web Construction | **Square or Rectangular Pipe (Cold Rolled Tubular Steel)** |
| Connections | Site-welded using `6mm` or `10mm` gusset plates |
| Supports | **4 fixed-base RC columns**: 2 exterior + 2 interior |
| Interior Column Locations | Exactly at 7.0 m and 14.0 m |
| Steel Grade | `A36 (Fy = 36 ksi)` |

| Concrete Grade | `21 MPa (3000 psi)` |

## 2. Applied Loads

### Gravity Loads

| Component | Value |
| --- | --- |
| Dead Load (Roof + Ceiling) | `3.0 kN/m` (0.5 kPa × 6m trib.) |
| Truss + RC Col Self-Weight | `3.057 kN/m` |
| **Total Dead Load (D)** | **`3.500 kN/m`** |
| **Live Load (L)** | **`3.600 kN/m`** (0.6 kPa × 6m trib.) |

### Earthquake (Static Method — NSCP)

| Parameter | Value |
| --- | --- |
| Seismic Coefficient ($C_s$) | `0.2` (Zone 4, Soil Type D, R=8.5) |
| Seismic Weight ($W$) | `73.50 kN` |
| Base Shear ($V = C_s \times W$) | **`14.70 kN`** |
| Lateral q per exterior column ($V / 4 / h$) | `0.92 kN/m` |

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
| Top Chord | -94.41 | -74.16 | -40.95 | **-94.41** |
| Bottom Chord | 90.78 | 71.14 | 40.42 | **90.78** |
| Vertical Webs | -53.60 | -42.10 | -23.24 | **-53.60** |
| Diagonal Webs | 47.54 | 37.36 | 20.75 | **47.54** |
| Exterior Columns | 22.56 | 17.71 | 9.73 | **22.56** |
| Interior Columns | 84.02 | 65.92 | 36.07 | **84.02** |

### Support Reactions per Load Case

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Vertical ($F_y$) — Max | 84.02 | 65.92 | 36.07 | **84.02** |
| Vertical ($F_y$) — Exterior | 22.56 | 17.71 | 9.73 | **22.56** |
| Vertical ($F_y$) — Interior | 84.02 | 65.92 | 36.07 | **84.02** |
| Horizontal ($F_x$) — Max | 2.15 | 3.80 | 16.15 | **16.15** |

> **Governing Vertical Reaction (Exterior):** `22.56 kN`
> **Governing Vertical Reaction (Interior):** `84.02 kN`
> **Governing Horizontal Reaction:** `16.15 kN` ()

## 4. Deflection Check

- **Max Deflection:** `0.01 mm`
- **Deflection Ratio (L/d):** `1999505` (Target > 240) ✅ PASS

## 5. Optimized Member Selection (Governing Forces)

| Group | Selected Shape (Standard / Comm.) | Weight | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
| --- | --- | --- | --- | --- | --- | --- |
| Exterior Columns | `400x400 RC` | 384.0 kg/m | 0.0 | 22.56 | 0.00 | Gravity Only |
| Interior Columns | `400x400 RC` | 384.0 kg/m | 0.0 | 84.02 | 0.00 | Gravity Only |
| Top Chord | `2L2X2X1/8` | 3.3 plf | 64.6 | -94.41 | 98.24 | Gravity Only |
| Bottom Chord | `2L2X2X1/8` | 3.3 plf | 63.5 | 90.78 | 141.53 | Gravity Only |
| Vertical Webs | `HSS2X2X1/8` / **Square Pipe 51x51x3.2mm** | 3.0 plf | 103.5 | -53.60 | 68.90 | Gravity Only |
| Diagonal Webs | `HSS2X1X1/8` / **Rect. Pipe 51x25x3.2mm** | 2.2 plf | 225.7 | 47.54 | 87.63 | Gravity Only |

- **Total Steel Weight:** `401.0 kg`
- **Total Concrete Weight (Cols):** `6144.0 kg`
- **Estimated Steel Cost:** `PHP 24,059.48` (@ PHP 60/kg)

## 6. Substructure Design

Design assumptions:

| Parameter | Value |
| --- | --- |
| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |
| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |
| Allowable Soil Bearing ($q_a$) | `100 kPa` |


### Exterior Column Foundation (×2)

**Column:** `400x400 RC`, Height: `4.00 m`, $P_u$ = `22.56 kN`

> [!NOTE]
> RC Columns are cast monolithically with the pedestal/footing. Steel base plates and anchor bolts are not required.

#### Column & Pedestal Details

| Parameter | Value |
| --- | --- |
| RC Column Section | `400 mm × 400 mm` |
| Vertical Reinforcement | `8 — 16mm Ø bars` (Grade 40) |
| Lateral Ties | `10mm Ø @ 200mm O.C.` |
| Concrete Cover | `40 mm` |

#### Isolated Square Footing

| Parameter | Value |
| --- | --- |
| Dimensions | `1.0 m × 1.0 m × 0.40 m` |
| Bearing Pressure | `15.0 kPa` ≤ `100 kPa` ✅ |
| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |


### Interior Column Foundation (×2)

**Column:** `400x400 RC`, Height: `4.00 m`, $P_u$ = `84.02 kN`

> [!NOTE]
> RC Columns are cast monolithically with the pedestal/footing. Steel base plates and anchor bolts are not required.

#### Column & Pedestal Details

| Parameter | Value |
| --- | --- |
| RC Column Section | `400 mm × 400 mm` |
| Vertical Reinforcement | `8 — 16mm Ø bars` (Grade 40) |
| Lateral Ties | `10mm Ø @ 200mm O.C.` |
| Concrete Cover | `40 mm` |

#### Isolated Square Footing

| Parameter | Value |
| --- | --- |
| Dimensions | `1.0 m × 1.0 m × 0.40 m` |
| Bearing Pressure | `56.0 kPa` ≤ `100 kPa` ✅ |
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
