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
| Web Construction | **Single Angles (L)** — welded to gusset plates |
| Connections | Site-welded using `6mm` or `10mm` gusset plates |
| Supports | **4 fixed-base RC columns**: 2 exterior + 2 interior |
| Interior Column Locations | Exactly at 7.0 m and 14.0 m |
| Steel Grade | `A36 (Fy = 36 ksi)` |

| Concrete Grade | `21 MPa (3000 psi)` |

## 2. Applied Loads

### Gravity Loads

| Component | Value |
| --- | --- |
| Dead Load (Roof + Ceiling) | `2.5 kN/m` (0.5 kPa × 5m trib.) |
| Truss + RC Col Self-Weight | `3.051 kN/m` |
| **Total Dead Load (D)** | **`3.000 kN/m`** |
| **Live Load (L)** | **`3.000 kN/m`** (0.6 kPa × 5m trib.) |

### Earthquake (Static Method — NSCP)

| Parameter | Value |
| --- | --- |
| Seismic Coefficient ($C_s$) | `0.2` (Zone 4, Soil Type D, R=8.5) |
| Seismic Weight ($W$) | `63.00 kN` |
| Base Shear ($V = C_s \times W$) | **`12.60 kN`** |
| Lateral q per exterior column ($V / 4 / h$) | `0.79 kN/m` |

### Wind Load

| Parameter | Value |
| --- | --- |
| Wind Pressure | `800 Pa` |
| Tributary Width | `5 m` |
| Lateral Load on Ext. Columns | **`4.0 kN/m`** (800 Pa × 5m) |

## 3. Load Case Summary

### Axial Forces (kN) per Load Case

| Member Group | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Top Chord | -79.67 | -62.78 | -35.08 | **-79.67** |
| Bottom Chord | 76.55 | 60.25 | 34.63 | **76.55** |
| Vertical Webs | -45.17 | -35.59 | -19.88 | **-45.17** |
| Diagonal Webs | 40.05 | 31.58 | 17.74 | **40.05** |
| Exterior Columns | 19.03 | 14.99 | 8.33 | **19.03** |
| Interior Columns | 70.82 | 55.75 | 30.88 | **70.82** |

### Support Reactions per Load Case

| Reaction | LC1 — Gravity Only | LC2 — Gravity + EQ | LC3 — Gravity + Wind | **Governing** |
| --- | --- | --- | --- | --- |
| Vertical ($F_y$) — Max | 70.82 | 55.75 | 30.88 | **70.82** |
| Vertical ($F_y$) — Exterior | 19.03 | 14.99 | 8.33 | **19.03** |
| Vertical ($F_y$) — Interior | 70.82 | 55.75 | 30.88 | **70.82** |

> **Governing Vertical Reaction (Exterior):** `19.03 kN`
> **Governing Vertical Reaction (Interior):** `70.82 kN`
> **Governing Horizontal Reaction:** `13.49 kN` ()

## 4. Deflection Check

- **Max Deflection:** `0.01 mm`
- **Deflection Ratio (L/d):** `2273116` (Target > 240) PASS

## 5. Optimized Member Selection (Governing Forces)

| Group | Selected Shape (Standard / Comm.) | Weight | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |
| --- | --- | --- | --- | --- | --- | --- |
| Exterior Columns | `250x250 RC` | 150.0 kg/m | 0.0 | 19.03 | 663.70 | Gravity Only |
| Interior Columns | `250x250 RC` | 150.0 kg/m | 0.0 | 70.82 | 663.70 | Gravity Only |
| Top Chord | `2L2X2X1/8` | 3.3 plf | 64.6 | -79.67 | 98.24 | Gravity Only |
| Bottom Chord | `2L2X2X1/8` | 3.3 plf | 63.5 | 76.55 | 141.53 | Gravity Only |
| Vertical Webs | `L3X2-1/2X3/16` | 3.4 plf | 151.1 | -45.17 | 44.00 | Gravity Only |
| Diagonal Webs | `L2X2X1/8` | 1.6 plf | 225.2 | 40.05 | 70.76 | Gravity Only |

- **Total Steel Weight:** `387.1 kg`
- **Total Concrete Weight (Cols):** `6144.0 kg`

## 6. Substructure Design

Design assumptions:

| Parameter | Value |
| --- | --- |
| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |
| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |
| Allowable Soil Bearing ($q_a$) | `144 kPa` (from soil test) |
| Foundation Depth | `1.0 m` below grade |


### Exterior Column Foundation (×2)

**Column:** `250x250 RC`, Height: `4.00 m`, $P_u$ = `19.03 kN`

> [!NOTE]
> RC Columns are cast monolithically with the pedestal/footing. Steel base plates and anchor bolts are not required.

#### Column & Pedestal Details

| Parameter | Value |
| --- | --- |
| RC Column Section | `250 mm × 250 mm` |
| Vertical Reinforcement | `4 — 12mm Ø bars` (Grade 40) |
| Lateral Ties | `10mm Ø @ 192mm O.C.` |
| Concrete Cover | `40 mm` |
| Slenderness ($kL_u/r$) | `55.4` (Slender) ✅ |
| Axial Capacity ($\phi P_n$) | `663.7 kN` ≥ `19.0 kN` ✅ |
| Moment Magnification ($\delta_{ns}$) | `1.024` |
| Magnified Moment ($M_c$) | `0.29 kN·m` |

#### Isolated Square Footing

| Parameter | Value |
| --- | --- |
| Foundation Depth | `1.0 m` below grade |
| Dimensions | `0.45 m × 0.45 m × 0.20 m` |
| Bearing Pressure | `62.7 kPa` ≤ `144 kPa` ✅ |
| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |

#### Tie Beam Details
- **Size:** `300mm x 400mm` RC Tie Beam
- **Reinforcement:** `4 - 16mm Ø` main bars with `10mm Ø @ 200mm` stirrups
- **Purpose:** Seismic connectivity between footings at ends


### Interior Column Foundation (×2)

**Column:** `250x250 RC`, Height: `4.00 m`, $P_u$ = `70.82 kN`

> [!NOTE]
> RC Columns are cast monolithically with the pedestal/footing. Steel base plates and anchor bolts are not required.

#### Column & Pedestal Details

| Parameter | Value |
| --- | --- |
| RC Column Section | `250 mm × 250 mm` |
| Vertical Reinforcement | `4 — 12mm Ø bars` (Grade 40) |
| Lateral Ties | `10mm Ø @ 192mm O.C.` |
| Concrete Cover | `40 mm` |
| Slenderness ($kL_u/r$) | `55.4` (Slender) ✅ |
| Axial Capacity ($\phi P_n$) | `663.7 kN` ≥ `70.8 kN` ✅ |
| Moment Magnification ($\delta_{ns}$) | `1.096` |
| Magnified Moment ($M_c$) | `1.16 kN·m` |

#### Isolated Square Footing

| Parameter | Value |
| --- | --- |
| Foundation Depth | `1.0 m` below grade |
| Dimensions | `0.60 m × 0.60 m × 0.25 m` |
| Bearing Pressure | `131.1 kPa` ≤ `144 kPa` ✅ |
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

## 8. Top-Supported Warren Transfer Truss

### Configuration

| Parameter | Value |
| --- | --- |
| Truss Type | **Top-Supported Warren** (underslung, top chord extended) |
| Purpose | Transfer beam — carries interior column load to adjacent frames |
| Span | `10.0 m` |
| Depth | `1.4 m` |
| Bays | `4` @ `2.50 m` |
| Member Construction | **Double Angles (2L)** Chords, **Single Angles (L)** Webs |
| Point Load (Factored) | `70.82 kN` at midspan (from interior column reaction) |
| Point Load (Service) | `47.21 kN` (factored / 1.5) |
| Supports | Simply supported (pin + roller) at top chord |

### Deflection Check

- **Max Deflection:** `11.45 mm`
- **Deflection Ratio (L/d):** `873` (Target > 360) PASS

### Optimized Member Selection

| Group | Selected Shape | Weight | KL/r | Gov. Force (kN) | Capacity (kN) |
| --- | --- | --- | --- | --- | --- |
| Top Chord | `2L3X2-1/2X3/16LLBB` | 6.8 plf | 103.9 | -126.47 | 152.67 |
| Bottom Chord | `2L2X2X1/8` | 3.3 plf | 158.8 | 94.85 | 141.53 |
| Verticals | `L2X2X1/8` | 1.6 plf | 141.0 | 35.41 | 70.76 |
| Diagonals | `L2X2X1/8` | 1.6 plf | 189.0 | 47.47 | 70.76 |

- **Total Steel Weight:** `193.7 kg`
- **Support Reactions:** `35.41 kN` per end (transferred to interior columns)

### Structural Plots

#### Top-Supported Warren -- Structure & Point Load
![Top-Supported Warren -- Structure & Point Load](images/warren_top_structure.png)

#### Top-Supported Warren -- Axial Forces
![Top-Supported Warren -- Axial Forces](images/warren_top_axial.png)

#### Top-Supported Warren -- Deflection
![Top-Supported Warren -- Deflection](images/warren_top_displacement.png)

#### Top-Supported Warren -- Support Reactions
![Top-Supported Warren -- Support Reactions](images/warren_top_reactions.png)
