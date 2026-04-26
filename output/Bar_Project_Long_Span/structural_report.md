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
| Supports | **2 fixed-base RC columns**: Exterior only (Long Span) |
| Steel Grade | `A36 (Fy = 36 ksi)` |

| Concrete Grade | `21 MPa (3000 psi)` |

## 2. Applied Loads

### Gravity Loads

| Component | Value |
| --- | --- |
| Dead Load (Roof + Ceiling) | `3.0 kN/m` (0.5 kPa × 6m trib.) |
| Truss + RC Col Self-Weight | `1.896 kN/m` |
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
| Top Chord | -542.34 | -424.73 | -228.70 | **-542.34** |
| Bottom Chord | 512.54 | 401.39 | 216.13 | **512.54** |
| Vertical Webs | 45.63 | 35.73 | 19.24 | **45.63** |
| Diagonal Webs | 77.75 | 60.89 | 32.79 | **77.75** |
| Exterior Columns | 106.37 | 83.30 | 44.86 | **106.37** |

### Support Reactions per Load Case

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Vertical ($F_y$) — Max | 106.37 | 83.30 | 44.86 | **106.37** |
| Vertical ($F_y$) — Exterior | 106.37 | 83.30 | 44.86 | **106.37** |

> **Governing Vertical Reaction (Exterior):** `106.37 kN`
> **Governing Horizontal Reaction:** `27.33 kN` ()

## 4. Deflection Check

- **Max Deflection:** `0.07 mm`
- **Deflection Ratio (L/d):** `302814` (Target > 240) PASS

## 5. Optimized Member Selection (Governing Forces)

| Group | Selected Shape (Standard / Comm.) | Weight | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
| --- | --- | --- | --- | --- | --- | --- |
| Exterior Columns | `400x400 RC` | 384.0 kg/m | 0.0 | 106.37 | 0.00 | Gravity Only |
| Top Chord | `2L3X3X3/8` | 14.4 plf | 44.0 | -542.34 | 549.16 | Gravity Only |
| Bottom Chord | `2L3-1/2X3-1/2X1/4` | 11.6 plf | 36.1 | 512.54 | 490.02 | Gravity Only |
| Vertical Webs | `HSS2X1X1/8` / **Rect. Pipe 51x25x3.2mm** | 2.2 plf | 201.9 | 45.63 | 87.63 | Gravity Only |
| Diagonal Webs | `HSS2X1X1/8` / **Rect. Pipe 51x25x3.2mm** | 2.2 plf | 225.7 | 77.75 | 87.63 | Gravity Only |

- **Total Steel Weight:** `986.7 kg`
- **Total Concrete Weight (Cols):** `3072.0 kg`
- **Estimated Steel Cost:** `PHP 59,202.24` (@ PHP 60/kg)

## 6. Substructure Design

Design assumptions:

| Parameter | Value |
| --- | --- |
| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |
| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |
| Allowable Soil Bearing ($q_a$) | `100 kPa` |


### Exterior Column Foundation (×2)

**Column:** `400x400 RC`, Height: `4.00 m`, $P_u$ = `106.37 kN`

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
| Bearing Pressure | `70.9 kPa` ≤ `100 kPa` ✅ |
| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |

#### Tie Beam Details
- **Size:** `300mm x 400mm` RC Tie Beam
- **Reinforcement:** `4 - 16mm Ø` main bars with `10mm Ø @ 200mm` stirrups
- **Purpose:** Seismic connectivity between footings at ends

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
