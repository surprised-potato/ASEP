# Bar Project — Structural Optimization Report

## 1. Truss Configuration

| Parameter | Value |
| --- | --- |
| Span | `21.0 m` |
| Depth at Ends | `1.5 m` |
| Depth at Midspan (Peak) | `3.0 m` |
| Bottom Chord | **Level at y = 0.0 m** |
| Column Height | `6.0 m` (Fixed base, all 4 columns) |
| Panels | `21 @ 1.0 m` |
| Type | **Two-Slope Top Chord Howe Truss** |
| Web Pattern | Howe — diagonals slope outward from center (compression) |
| Supports | **4 fixed-base steel columns**: 2 exterior + 2 interior |
| Interior Column Locations | Exactly at 7.0 m and 14.0 m |
| Steel Grade | `A36 (Fy = 36 ksi)` |

## 2. Applied Loads

### Gravity Loads

| Component | Value |
| --- | --- |
| Dead Load (Roof + Ceiling) | `3.0 kN/m` (0.5 kPa × 6m trib.) |
| Truss Self-Weight | `0.409 kN/m` (875.8 kg / 24m) |
| **Total Dead Load (D)** | **`3.409 kN/m`** |
| **Live Load (L)** | **`3.600 kN/m`** (0.6 kPa × 6m trib.) |

### Earthquake (Static Method — NSCP)

| Parameter | Value |
| --- | --- |
| Seismic Coefficient ($C_s$) | `0.2` (Zone 4, Soil Type D, R=8.5) |
| Seismic Weight ($W$) | `71.59 kN` |
| Base Shear ($V = C_s \times W$) | **`14.32 kN`** |
| Lateral q per exterior column ($V / 4 / h$) | `0.60 kN/m` |

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
| Top Chord | -25.56 | -20.00 | -10.95 | **0.00** |
| Bottom Chord | 24.39 | 19.31 | 14.96 | **0.00** |
| Vertical Webs | -41.79 | -32.70 | -17.88 | **0.00** |
| Diagonal Webs | -35.28 | -27.56 | -14.79 | **0.00** |
| Exterior Columns | 30.75 | 24.03 | 12.98 | **0.00** |
| Interior Columns | 74.27 | 58.07 | 31.50 | **0.00** |

### Support Reactions per Load Case

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Vertical ($F_y$) — Max | 74.27 | 58.07 | 31.50 | **0.00** |
| Vertical ($F_y$) — Exterior | 30.75 | 24.03 | 12.98 | **30.75** |
| Vertical ($F_y$) — Interior | 74.27 | 58.07 | 31.50 | **74.27** |
| Horizontal ($F_x$) — Max | 0.22 | 3.08 | 23.53 | **23.53** |

> **Governing Vertical Reaction (Exterior):** `30.75 kN`
> **Governing Vertical Reaction (Interior):** `74.27 kN`
> **Governing Horizontal Reaction:** `23.53 kN` ()

## 4. Deflection Check

- **Max Deflection:** `0.00 mm`
- **Deflection Ratio (L/d):** `6903816` (Target > 240) ✅ PASS

## 5. Optimized Member Selection (Governing Forces)

| Group | Selected Shape | Weight (plf) | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
| --- | --- | --- | --- | --- | --- | --- |
| Top Chord | `WT3X4.25` | 4.2 | 46.9 | -10.95 | 161.74 | Gravity Only |
| Bottom Chord | `WT3X4.25` | 4.2 | 46.4 | 24.39 | 181.59 | Gravity Only |
| Vertical Webs | `HSS2.500X0.125` | 3.2 | 139.9 | -17.88 | 44.59 | Gravity Only |
| Diagonal Webs | `HSS2.375X0.125` | 3.0 | 155.6 | -14.79 | 34.15 | Gravity Only |
| Exterior Columns | `W6X15` | 15.0 | 162.9 | 30.75 | 167.74 | Gravity Only |
| Interior Columns | `W6X15` | 15.0 | 162.9 | 74.27 | 167.74 | Gravity Only |

- **Total Steel Weight:** `875.8 kg`
- **Estimated Steel Cost:** `PHP 52,548.25` (@ PHP 60/kg)

## 6. Substructure Design

Design assumptions:

| Parameter | Value |
| --- | --- |
| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |
| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |
| Allowable Soil Bearing ($q_a$) | `100 kPa` |


### Exterior Column Foundation (×2)

**Column:** `W6X15`, Height: `6.00 m`, $P_u$ = `30.75 kN`

#### Steel Base Plate

| Parameter | Value |
| --- | --- |
| Base Plate (B × N) | `252 mm × 252 mm` |
| Thickness ($t_p$) | `10 mm` |
| Bearing Stress | `0.48 MPa` ≤ `11.60 MPa` (✅) |
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
| Bearing Pressure | `20.5 kPa` ≤ `100 kPa` ✅ |
| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |


### Interior Column Foundation (×2)

**Column:** `W6X15`, Height: `6.00 m`, $P_u$ = `74.27 kN`

#### Steel Base Plate

| Parameter | Value |
| --- | --- |
| Base Plate (B × N) | `252 mm × 252 mm` |
| Thickness ($t_p$) | `10 mm` |
| Bearing Stress | `1.17 MPa` ≤ `11.60 MPa` (✅) |
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
| Bearing Pressure | `49.5 kPa` ≤ `100 kPa` ✅ |
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
