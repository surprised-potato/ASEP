# ASEP Project Memory

This file serves as a persistent context for AI agents working on the ASEP codebase.

## Critical Structural Analysis Rules

1. **No Notebook Generation**: Do NOT use Python scripts to generate or write to `.ipynb` files for core logic. Use the modular CLI pipeline.
2. **Stiffness Property Updates**: Never update `EA` or `EI` on an existing `anastruct` element. Always rebuild the `SystemElements` object with the new properties.
3. **Truss Elements**: Use `add_element(..., spring={1: 0, 2: 0})` instead of `add_truss_element` to ensure compatibility and explicit property setting.
4. **Database Consistency**: Always use `aisc_db.select_lightest()` or `aisc_db.select_candidates()` from `aisc_database.py` for member sizing.

## Unit Conversion Reference (Imperial <-> SI)

| Category | Conversion | Formula |
| --- | --- | --- |
| Area | in² -> m² | `value * 0.00064516` |
| Inertia | in⁴ -> m⁴ | `value * 4.1623e-7` |
| Force | kN -> kips | `value * 0.224809` |
| Length | m -> in | `value * 39.3701` |
| Weight | plf -> kg/m | `value * 1.488` |

## Material Defaults
- **Steel**: A36 ($F_y = 36$ ksi)
- **Concrete**: $f'_c = 21$ MPa, $f_y = 275$ MPa (for footing/column calcs)
- **Modulus of Elasticity (E)**: 200 GPa ($29,000$ ksi)
