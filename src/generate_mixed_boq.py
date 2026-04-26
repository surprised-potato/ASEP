"""Consolidates BOQ for 5 standard frames and 1 long-span frame.
Includes Tie Beam quantities.
"""
import os
import math

def get_total_boq(ls_steel_kg):
    # Standard Frame Data
    standard_steel = 401.0
    standard_concrete = 4.16
    standard_rebar = 293.7
    
    # LONG SPAN Frame 6 (2 columns/footings only)
    ls_steel = ls_steel_kg
    ls_conc = 2.08   # 1.28 (cols) + 0.8 (footings)
    ls_rebar = 146.9 # Half of standard
    
    # TIE BEAM (6 beams, each 21m)
    tb_size = (0.3, 0.4) 
    tb_len_per_frame = 21.0
    tb_vol_total = tb_size[0] * tb_size[1] * tb_len_per_frame * 6 # 15.12 m3
    
    tb_rebar_16_kg = (4 * 21 * 6) * 1.58 # 796.3 kg
    tb_rebar_10_kg = (105 * 1.4 * 6) * 0.62 # 546.8 kg
    tb_rebar_total = tb_rebar_16_kg + tb_rebar_10_kg # 1343.1 kg
    
    return {
        "standard_total": {"steel": 5 * standard_steel, "conc": 5 * standard_concrete, "rebar": 5 * standard_rebar},
        "long_span_total": {"steel": ls_steel, "conc": ls_conc, "rebar": ls_rebar},
        "tie_beam_total": {"conc": tb_vol_total, "rebar": tb_rebar_total}
    }

def generate_mixed_boq_report(ls_steel_kg, project_name="Bar_Project_Mixed"):
    vals = get_total_boq(ls_steel_kg)
    s = vals["standard_total"]
    ls = vals["long_span_total"]
    tb = vals["tie_beam_total"]
    
    total_steel = s['steel'] + ls['steel']
    total_conc = s['conc'] + ls['conc'] + tb['conc']
    total_rebar = s['rebar'] + ls['rebar'] + tb['rebar']
    
    output_dir = os.path.join('output', project_name)
    os.makedirs(output_dir, exist_ok=True)
    
    report = [
        "# Bill of Materials (BOM) — Mixed Frame Building\n",
        "**Project:** Bar building with 5 Standard Frames and 1 Long-Span Frame\n",
        "**Configuration:** 6 Frames total, 21m Span, 4m Height.\n",
        "- **Standard Frames (1-5):** Isosceles Howe with 2 interior columns.\n",
        "- **Long-Span Frame (6):** Isosceles Howe with NO interior columns.\n",
        "- **Tie Beams:** 300x400mm RC beams connecting all exterior footings (126m total length).\n",
        "\n## 1. Summary of Quantities\n",
        "| Material Type | Unit | 5x Standard | 1x Long-Span | Tie Beams | **Grand Total** |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| Structural Steel | kg | {s['steel']:.1f} | {ls['steel']:.1f} | - | **{total_steel:.1f}** |",
        f"| Concrete (21 MPa) | m³ | {s['conc']:.2f} | {ls['conc']:.2f} | {tb['conc']:.2f} | **{total_conc:.2f}** |",
        f"| Reinforcement | kg | {s['rebar']:.1f} | {ls['rebar']:.1f} | {tb['rebar']:.1f} | **{total_rebar:.1f}** |\n",
        "\n## 2. Estimated Costs\n",
        "| Material | Total Qty | Unit | Unit Rate | Total (PHP) |",
        "| --- | --- | --- | --- | --- |",
        f"| Steel | {total_steel:,.1f} | kg | 60.00 | {total_steel*60:,.2f} |",
        f"| Concrete | {total_conc:,.2f} | m³ | 5,500.00 | {total_conc*5500:,.2f} |",
        f"| Rebar | {total_rebar:,.1f} | kg | 55.00 | {total_rebar*55:,.2f} |",
        f"| **TOTAL** | | | | **{total_steel*60 + total_conc*5500 + total_rebar*55:,.2f}** |\n",
        "\n## 3. Detailed Member Schedule (Long-Span Frame 6 Only)\n",
        "| Group | Shape | Total Length | Unit Weight | Total Weight |",
        "| --- | --- | --- | --- | --- |",
        "| Top Chord | `2L3X3X3/8` | 21.36 m | 21.4 kg/m | 457.1 kg |",
        "| Bottom Chord | `2L3-1/2X3-1/2X1/4` | 21.00 m | 17.3 kg/m | 363.3 kg |",
        "| Vertical Webs | `Rect. Pipe 51x25` | 21.00 m | 3.27 kg/m | 68.7 kg |",
        "| Diagonal Webs | `Rect. Pipe 51x25` | 29.89 m | 3.27 kg/m | 97.7 kg |\n",
        "\n## 4. Discussion\n",
        "- Frame 6 (Long Span) requires significantly heavier steel sections (`2L3x3x3/8` vs `2L2x2x1/8`) to bridge 21m without interior columns.",
        "- Tie beams (300x400) connect all exterior footings along the building length (21m per bay/frame).",
        "- All designs maintain L/240 deflection at service loads."
    ]
    
    with open(os.path.join(output_dir, 'BILL_OF_MATERIALS_MIXED.md'), 'w') as f:
        f.write('\n'.join(report))
    
    print(f"OK: Mixed BOQ generated: output/{project_name}/BILL_OF_MATERIALS_MIXED.md")

if __name__ == "__main__":
    generate_mixed_boq_report(ls_steel_kg=986.7)
