# Bar Project — Structural Optimization Report

## 1. Truss Configuration

| Parameter | Value |
| --- | --- |
| Span | `21.0 m` |
| End Depth | `0.0 m` (Isosceles Triangle) |
| Depth at Midspan (Peak) | `3.0 m` |
| Bottom Chord | **Level at y = 0.0 m** |
| Column Height | `6.0 m` (Fixed base, all 4 columns) |
| Panels | `21 @ 1.0 m` |
| Type | **Isosceles Triangle Howe Truss** |
| Chord Construction | **Double Angles (2L)** — back-to-back for gusset plates |
| Web Construction | **Single Angles (L) or Double Angles (2L)** |
| Connections | Site-welded using `6mm` or `10mm` gusset plates |
| Supports | **4 fixed-base steel columns**: 2 exterior + 2 interior |
| Interior Column Locations | Exactly at 7.0 m and 14.0 m |
| Steel Grade | `A36 (Fy = 36 ksi)` |

## 2. Applied Loads

### Gravity Loads

| Component | Value |
| --- | --- |
| Dead Load (Roof + Ceiling) | `3.0 kN/m` (0.5 kPa × 6m trib.) |
| Truss Self-Weight | `0.048 kN/m` (103.1 kg / 24m) |
| **Total Dead Load (D)** | **`3.048 kN/m`** |
| **Live Load (L)** | **`3.600 kN/m`** (0.6 kPa × 6m trib.) |

### Earthquake (Static Method — NSCP)

| Parameter | Value |
| --- | --- |
| Seismic Coefficient ($C_s$) | `0.2` (Zone 4, Soil Type D, R=8.5) |
| Seismic Weight ($W$) | `64.01 kN` |
| Base Shear ($V = C_s \times W$) | **`12.80 kN`** |
| Lateral q per exterior column ($V / 4 / h$) | `0.53 kN/m` |

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
| Top Chord | -76.29 | -58.79 | -29.63 | **-76.29** |
| Bottom Chord | 71.90 | 55.26 | 32.89 | **71.90** |
| Vertical Webs | -49.30 | -37.99 | -19.15 | **-49.30** |
| Diagonal Webs | 38.65 | 29.78 | 15.01 | **38.65** |
| Exterior Columns | 24.35 | 18.77 | 9.46 | **24.35** |
| Interior Columns | 78.86 | 60.77 | 30.63 | **78.86** |

### Support Reactions per Load Case

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Vertical ($F_y$) — Max | 78.86 | 60.77 | 30.63 | **78.86** |
| Vertical ($F_y$) — Exterior | 24.35 | 18.77 | 9.46 | **24.35** |
| Vertical ($F_y$) — Interior | 78.86 | 60.77 | 30.63 | **78.86** |
| Horizontal ($F_x$) — Max | 0.49 | 2.97 | 23.64 | **23.64** |

> **Governing Vertical Reaction (Exterior):** `24.35 kN`
> **Governing Vertical Reaction (Interior):** `78.86 kN`
> **Governing Horizontal Reaction:** `23.64 kN` ()

## 4. Deflection Check

- **Max Deflection:** `27.30 mm`
- **Deflection Ratio (L/d):** `769` (Target > 240) ✅ PASS

## 5. Optimized Member Selection (Governing Forces)

| Group | Selected Shape | Weight (plf) | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
| --- | --- | --- | --- | --- | --- | --- |
| Bottom Chord | `2L2X2X1/8` | 3.3 | 63.5 | 71.90 | 141.53 | Gravity Only |

- **Total Steel Weight:** `103.1 kg`
- **Estimated Steel Cost:** `PHP 6,187.78` (@ PHP 60/kg)

## 6. Substructure Design

Design assumptions:

| Parameter | Value |
| --- | --- |
| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |
| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |
| Allowable Soil Bearing ($q_a$) | `100 kPa` |


### Exterior Column Foundation (×2)

**Column:** `W6X15`, Height: `6.00 m`, $P_u$ = `24.35 kN`

#### Steel Base Plate

| Parameter | Value |
| --- | --- |
| Base Plate (B × N) | `252 mm × 252 mm` |
| Thickness ($t_p$) | `10 mm` |
| Bearing Stress | `0.38 MPa` ≤ `11.60 MPa` (✅) |
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
| Bearing Pressure | `16.2 kPa` ≤ `100 kPa` ✅ |
| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |


### Interior Column Foundation (×2)

**Column:** `W6X15`, Height: `6.00 m`, $P_u$ = `78.86 kN`

#### Steel Base Plate

| Parameter | Value |
| --- | --- |
| Base Plate (B × N) | `252 mm × 252 mm` |
| Thickness ($t_p$) | `10 mm` |
| Bearing Stress | `1.24 MPa` ≤ `11.60 MPa` (✅) |
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
| Bearing Pressure | `52.6 kPa` ≤ `100 kPa` ✅ |
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
