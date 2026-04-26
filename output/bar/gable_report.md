# Gable Roof Structural Analysis Report

## 1. Frame Geometry & Loads
- **Span:** `20.0 m`
- **Column Height:** `6.0 m`
- **Max Vertical Deflection:** `0.12 mm` (Limit: 83.33 mm)

## 2. Loading Data (NSCP 2015 Combinations)
- **Frame Spacing:** `4.2 m` (Tributary Width)
- **Dead Load (DL):** `0.9 kPa \times 4.2m = 3.78 kN/m`
- **Roof Live Load (LR):** `0.6 kPa \times 4.2m = 2.52 kN/m`
- **Governing Combination ($1.2D + 1.6L$):** `1.2(3.78) + 1.6(2.52) = 8.57 kN/m` (Applied as UDL)

### Optimized Member Selection (AISC Chapter H Interaction)
| Group | Selected W-Shape | Weight (plf) | Area (in²) | Interaction Ratio |
| --- | --- | --- | --- | --- |
| Beam | `W21X48` | 48.0 | 14.10 | 0.95 |
| Column | `W21X48` | 48.0 | 14.10 | 0.95 |

- **Total Steel Weight (per frame):** `2307.6 kg`
- **Estimated Material Cost:** `PHP 149,994.30` (@ PHP 65/kg)

## 2. Foundation Design (Base Plate, Pedestal & Footing)
### Base Plate Details
| Parameter | Value |
| --- | --- |
| Dimensions ($B \times N$) | `300mm x 300mm` |
| Thickness ($t$) | `16mm` |
| Anchor Bolts | `4 nos. 20mm \phi A325 Bolts` |
| Grout Thickness | `25 mm` |

### Concrete Pedestal
| Parameter | Value |
| --- | --- |
| Dimensions | `500mm x 500mm` |
| Vertical Load ($P_u$) | `83.26 kN` |
| Vertical Reinforcement | `8 nos. 16mm \phi Bars` |
| Lateral Ties | `10mm \phi @ 200mm o.c.` |
| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |

### Isolated Square Footing
| Parameter | Value |
| --- | --- |
| Dimensions | `1.5m x 1.5m` |
| Thickness | `0.40 m` |
| Depth of Bottom | `1.50 m below Ground Level` |
| Main Reinforcement | `12mm \phi @ 150mm o.c. (Bottom BW)` |
| Soil Bearing Cap | `120 kPa (Assumed)` |

## 3. Visualizations
### Frame Structure & Loads
![Frame Structure & Loads](images/gable_structure.png)

### Axial Force Diagram
![Axial Force Diagram](images/axial_force.png)

### Shear Force Diagram
![Shear Force Diagram](images/shear_force.png)

### Bending Moment Diagram
![Bending Moment Diagram](images/bending_moment.png)

### Displacement Plot
![Displacement Plot](images/displacement.png)

### Reaction Forces
![Reaction Forces](images/reactions.png)
