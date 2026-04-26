# Bar Project — Structural Optimization Report

## 1. Truss Configuration

| Parameter | Value |
| --- | --- |
| Span | `24.0 m` |
| Depth | `2.0 m` (constant between chords) |
| Center Rise | `3.0 m` |
| Column Height (ground to truss) | `6.0 m` (exterior), `7.875 m` (interior at chord elevation) |
| Panels | `16 @ 1.5 m` |
| Type | **Two-Slope (Gable) Standard Howe Truss** |
| Web Pattern | Howe — diagonals slope outward from center (compression) |
| Supports | **4 fixed-base steel columns**: 2 exterior + 2 interior |
| Interior Column Locations | Panel 5 (x = 7.5 m) and Panel 11 (x = 16.5 m) |
| Steel Grade | `A36 (Fy = 36 ksi)` |

## 2. Applied Loads

### Gravity Loads

| Component | Value |
| --- | --- |
| Dead Load (Roof + Ceiling) | `3.0 kN/m` (0.5 kPa × 6m trib.) |
| Truss Self-Weight | `0.272 kN/m` (1496.9 kg / 24m) |
| **Total Dead Load (D)** | **`3.272 kN/m`** |
| **Live Load (L)** | **`3.600 kN/m`** (0.6 kPa × 6m trib.) |

### Earthquake (Static Method — NSCP)

| Parameter | Value |
| --- | --- |
| Seismic Coefficient ($C_s$) | `0.2` (Zone 4, Soil Type D, R=8.5) |
| Seismic Weight ($W$) | `78.54 kN` |
| Base Shear ($V = C_s \times W$) | **`15.71 kN`** |
| Lateral q per exterior column ($V / 4 / h$) | `0.65 kN/m` |

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
| Top Chord | 32.72 | 25.52 | 13.92 | **32.72** |
| Bottom Chord | -31.65 | -24.68 | -13.49 | **-31.65** |
| Vertical Webs | -52.24 | -40.63 | -21.46 | **-52.24** |
| Diagonal Webs | -41.96 | -32.63 | -17.20 | **-41.96** |
| Exterior Columns | 90.23 | 70.29 | 37.85 | **90.23** |
| Interior Columns | 90.23 | 70.29 | 37.85 | **90.23** |

### Support Reactions per Load Case

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Vertical ($F_y$) — Max | 90.23 | 70.29 | 37.85 | **90.23** |
| Vertical ($F_y$) — Exterior | 29.59 | 23.13 | 12.99 | **29.59** |
| Vertical ($F_y$) — Interior | 90.23 | 70.29 | 37.85 | **90.23** |
| Horizontal ($F_x$) — Max | 0.56 | 3.92 | 25.73 | **25.73** |

> **Governing Vertical Reaction (Exterior):** `29.59 kN`
> **Governing Vertical Reaction (Interior):** `90.23 kN`
> **Governing Horizontal Reaction:** `25.73 kN` (LC3: Gravity + Wind)

## 4. Deflection Check

- **Max Deflection:** `0.00 mm`
- **Deflection Ratio (L/d):** `6686267` (Target > 240) ✅ PASS

## 5. Optimized Member Selection (Governing Forces)

| Group | Selected Shape | Weight (plf) | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
| --- | --- | --- | --- | --- | --- | --- |
| Top Chord | `WT3X4.25` | 4.2 | 71.8 | 32.72 | 181.59 | Gravity Only |
| Bottom Chord | `WT3X4.25` | 4.2 | 71.8 | -31.65 | 138.45 | Gravity Only |
| Vertical Webs | `HSS2.375X0.125` | 3.0 | 98.4 | -52.24 | 71.23 | Gravity Only |
| Diagonal Webs | `HSS2.375X0.125` | 3.0 | 138.2 | -41.96 | 43.28 | Gravity Only |
| Exterior Columns | `W6X15` | 15.0 | 162.9 | 90.23 | 167.74 | Gravity Only |
| Interior Columns | `W8X24` | 24.0 | 192.6 | 90.23 | 191.86 | Gravity Only |

- **Total Steel Weight:** `1496.9 kg`
- **Estimated Steel Cost:** `PHP 89,816.67` (@ PHP 60/kg)

## 6. Substructure Design

Design assumptions:

| Parameter | Value |
| --- | --- |
| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |
| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |
| Allowable Soil Bearing ($q_a$) | `100 kPa` |


### Exterior Column Foundation (×2)

**Column:** `W6X15`, Height: `6.00 m`, $P_u$ = `29.59 kN`

#### Steel Base Plate

| Parameter | Value |
| --- | --- |
| Base Plate (B × N) | `252 mm × 252 mm` |
| Thickness ($t_p$) | `10 mm` |
| Bearing Stress | `0.47 MPa` ≤ `11.60 MPa` (✅) |
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
| Bearing Pressure | `19.7 kPa` ≤ `100 kPa` ✅ |
| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |


### Interior Column Foundation (×2)

**Column:** `W8X24`, Height: `7.88 m`, $P_u$ = `90.23 kN`

#### Steel Base Plate

| Parameter | Value |
| --- | --- |
| Base Plate (B × N) | `252 mm × 252 mm` |
| Thickness ($t_p$) | `10 mm` |
| Bearing Stress | `1.42 MPa` ≤ `11.60 MPa` (✅) |
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
| Bearing Pressure | `60.2 kPa` ≤ `100 kPa` ✅ |
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
