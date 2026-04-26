# Modified Truss & CHB Gable Structure - Project: bar

## 1. Global Building Parameters
- **Building Span:** `20.0 m`
- **Total Bays:** `6 bays` @ `4.2 m` spacing
- **Main Steel Frames:** `5 Interior Trusses` (4.2m Tributary Width)
- **Gable Ends:** `2 Reinforced CHB Walls` (Bearing 2.1m Tributary Width)
- **Roof Pitch:** `10.0 degrees`
- **Truss Depth (Parallel):** `0.80 m`
- **Apex Height (Total):** `6.96 m`
- **Column/Eave Height:** `5.20 m`
- **Number of Panels:** `14` (Per Top/Bottom Chord)

## 2. Interior Roof Truss Member Selection (AISC Chapter H)
- **Max Deflection:** `0.13 mm`
| Group | Selected Shape | Weight (plf) | Area (in²) | Interaction Ratio |
| --- | --- | --- | --- | --- |
| Chords | `WT4X12` | 12.0 | 3.54 | 0.97 |
| Webs | `2L2X2X3/16` | 4.9 | 1.44 | 0.83 |

- **Total Building Steel Weight (5 Trusses):** `4,874.5 kg`
- **Estimated Steel Material Cost:** `PHP 316,845.05` (@ PHP 65/kg)
*(Note: Cost excludes the front & rear concrete gable walls)*

## 3. Global Steel Truss Cutting List (5 Trusses)
| Component | Shape | L per Piece (m) | Qty per Truss | Total Building Qty | Total Length (m) |
| --- | --- | --- | --- | --- | --- |
| Top/Bot Chords | `WT4X12` | 1.451 | 28 | 140 | 203.09 |
| Vertical Webs | `2L2X2X3/16` | 0.812 | 15 | 75 | 60.93 |
| Diagonal Webs | `2L2X2X3/16` | 1.643 | 14 | 70 | 115.04 |

## 4. Front & Rear CHB Gable Wall Specification
The 2 end steel trusses have been omitted in favor of structural Concrete Hollow Block (CHB) walls that directly carry the roof purlins and resist lateral wind loads across the 20m span.

### RC Column Layout (Vertical Supports)
- **Quantity:** `6 structural concrete columns` per gable wall.
- **Spacing:** Maximum `4.0 m` horizontal spacing between columns.
- **Column Sizing:** All gable wall columns to be `200mm x 350mm` reinforced with `8 pcs 16mm \phi` vertical rebars.

### RC Beam Layout (Horizontal Supports)
- **Mid-Height Tie Beam:** Continuous `150mm x 300mm` beam at approx `2.8m - 3.0m` height to break the unbraced CHB vertical span.
- **Sloped Gable Roof Beam:** Continuous `200mm x 400mm` boundary beam tracing the 10-degree roof slope (from 5.2m eave up to 6.96m apex).
  - **Main Reinforcement:** `6 pcs 16mm \phi` continuous long bars (3 top, 3 bottom).
  - **Stirrups:** `10mm \phi` ties spaced at `100mm` near columns and `200mm` at midspan.
  - **Embedment:** Purlin cleats/plates must be embedded here at `0.60m` max spacing.

## 5. Visualizations (Interior Truss)
### Truss Structure & Loads
![Truss Structure & Loads](images/truss_structure.png)

### Axial Force Diagram
![Axial Force Diagram](images/truss_axial.png)

### Bending Moment Diagram
![Bending Moment Diagram](images/truss_bending.png)

### Displacement Plot
![Displacement Plot](images/truss_displacement.png)

### Reaction Forces
![Reaction Forces](images/truss_reactions.png)


## 6. 3D Bracing Requirements (5-Truss System)
To ensure global stability out-of-plane for the 6-bay building, the following bracing is required:
- **Roof Purlins (Top Chord Bracing):** `LC 150x50x20x1.5mm` spaced at max `0.60m` attached to truss chords and the CHB Gable Beam.
- **Bottom Chord Kickers (Uplift Bracing):** `L2X2X1/4` angle kickers installed every `3.0m` along the internal truss bottom chords.
- **Longitudinal Roof X-Bracing:** `16mm \phi` sag rods spanning across the roof plane in the 2nd and 5th bays (adjacent to the stiff CHB gable walls).
- **Sidewall Vertical X-Bracing:** `20mm \phi` rods or `L2X2X1/4` angles in the 2nd and 5th wall bays to transfer longitudinal shear.
- **Eave Struts:** Continuous longitudinal members connecting the RC columns to the rigid CHB corner columns.
