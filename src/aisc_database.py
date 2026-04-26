import pandas as pd
import numpy as np
import math
import os

# Resolve project root (one level up from src/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class AISCDatabase:
    def __init__(self, db_path=None, sheet_name='Database v16.0'):
        """Loads and filters the AISC shapes database for structural use."""
        self.db_path = db_path or os.path.join(_PROJECT_ROOT, 'data', 'aisc-shapes-database-v160-2.xlsx')
        self.sheet_name = sheet_name
        self.db_filtered = None
        self._load_database()

    def _load_database(self):
        print(f"Loading AISC Member Database from {self.db_path}...")
        try:
            db = pd.read_excel(self.db_path, sheet_name=self.sheet_name)
            allowed_types = ['W', 'HSS', 'L', 'WT', '2L']
            self.db_filtered = db[db['Type'].isin(allowed_types)].copy()
            
            props = ['A', 'W', 'rx', 'ry', 'rz', 'Ix', 'Iy', 'bf', 'b', 'd', 'tw', 'Zx', 'Sx', 'Zy', 'Sy']
            for p in props:
                self.db_filtered[p] = pd.to_numeric(self.db_filtered[p], errors='coerce')
            
            self.db_filtered['r_min'] = self.db_filtered[['rx', 'ry', 'rz']].min(axis=1)
            self.db_filtered = self.db_filtered.dropna(subset=['A', 'r_min', 'W', 'Ix'])
            print(f"Successfully loaded {len(self.db_filtered)} candidate shapes.")
        except Exception as e:
            print(f"Error loading database: {e}")
            self.db_filtered = None

    def check_shape(self, Ag, r_min, Pu_kips, L_in, Fy=36, E=29000, Mux_kipsft=0.0, Muy_kipsft=0.0, Zx=0.0, Sx=0.0, Zy=0.0, Sy=0.0):
        """
        Checks if a shape passes strength and slenderness criteria (AISC Chapter H). 
        Returns (passes, cap_ratio, klr)
        """
        klr = L_in / r_min
        if Pu_kips < 0 and klr > 200: return False, 99.0, klr # Compression slenderness
        if Pu_kips >= 0 and klr > 300: return False, 99.0, klr # Tension slenderness
        
        # 1. Axial Capacity (phi Pn)
        phi_p = 0.9
        phi_Pn = 0.0
        if Pu_kips < 0: # Compression
            Fe = (math.pi**2 * E) / (klr**2)
            sl_limit = 4.71 * math.sqrt(E / Fy)
            Fcr = (0.658**(Fy / Fe)) * Fy if klr <= sl_limit else 0.877 * Fe
            phi_Pn = phi_p * Fcr * Ag
        else: # Tension
            phi_Pn = phi_p * Fy * Ag
            
        # 2. Bending Capacity (phi Mn) - Assuming compact sections for simplicity
        phi_m = 0.9
        phi_Mnx = phi_m * Fy * Zx / 12.0 # ft-kips
        phi_Mny = phi_m * Fy * Zy / 12.0 # ft-kips
        
        # Avoid division by zero
        if phi_Pn == 0: phi_Pn = 1e-6
        if phi_Mnx == 0: phi_Mnx = 1e-6
        if phi_Mny == 0: phi_Mny = 1e-6
        
        # 3. Interaction Check (AISC H1-1a/b)
        pr = abs(Pu_kips) / phi_Pn
        mr = abs(Mux_kipsft) / phi_Mnx + abs(Muy_kipsft) / phi_Mny
        
        if pr >= 0.2:
            ratio = pr + (8/9) * mr
        else:
            ratio = (pr / 2.0) + mr
            
        return (ratio <= 1.0), ratio, klr

    def select_candidates(self, Pu_kN, L_m, family='HSS', bf_max=None, Mx_kN_m=0.0, My_kN_m=0.0):
        """Returns a list of all shapes capable of supporting the combined loads, sorted by weight."""
        if self.db_filtered is None: return []
        
        # Convert to imperial for AISC checks
        Pu_kips = Pu_kN * 0.224809
        L_in = L_m * 39.3701
        Mux_kipsft = Mx_kN_m * 0.737562 # kN-m to kips-ft
        Muy_kipsft = My_kN_m * 0.737562
        
        subset = self.db_filtered[self.db_filtered['Type'] == family] if family else self.db_filtered
        valid = []
        
        for _, row in subset.iterrows():
            # Calculate cross-sectional width for geometric constraints
            width_in = 0
            type_str = str(row['Type'])
            if type_str == 'WT':
                width_in = row['bf'] if pd.notna(row['bf']) else 0
            elif type_str == 'L':
                width_in = max(row['b'] if pd.notna(row['b']) else 0, row['d'] if pd.notna(row['d']) else 0)
            elif type_str == '2L':
                w_b = row['b'] if pd.notna(row['b']) else 0
                width_in = 2 * w_b + 0.375
            elif type_str == 'W':
                width_in = row['bf'] if pd.notna(row['bf']) else 0

            if bf_max is not None and width_in > bf_max:
                continue

            fy = 36
            passes, ratio, klr = self.check_shape(
                row['A'], row['r_min'], Pu_kips, L_in, Fy=fy,
                Mux_kipsft=Mux_kipsft, Muy_kipsft=Muy_kipsft,
                Zx=row['Zx'], Sx=row['Sx'], Zy=row['Zy'], Sy=row['Sy']
            )
            if passes:
                valid.append({
                    'Label': str(row['AISC_Manual_Label']), 
                    'Weight': float(row['W']), 
                    'Area': float(row['A']), 
                    'Ix': float(row['Ix']), 
                    'KL/r': float(klr),
                    'Capacity_Ratio': float(ratio),
                    'bf_in': float(width_in),
                    'tw_in': float(row['tw']) if pd.notna(row['tw']) else 0.0
                })
                
        return sorted(valid, key=lambda x: x['Weight'])

    def select_lightest(self, Pu_kN, L_m, family='HSS', bf_max=None, Mx_kN_m=0.0, My_kN_m=0.0):
        """Returns the single lightest shape capable of supporting the combined loads."""
        candidates = self.select_candidates(Pu_kN, L_m, family, bf_max, Mx_kN_m, My_kN_m)
        return candidates[0] if candidates else None

# Singleton-like instance for easy import across modules
aisc_db = AISCDatabase()
