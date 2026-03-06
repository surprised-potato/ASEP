import pandas as pd
import numpy as np
import math

class AISCDatabase:
    def __init__(self, db_path='aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0'):
        """Loads and filters the AISC shapes database for structural use."""
        self.db_path = db_path
        self.sheet_name = sheet_name
        self.db_filtered = None
        self._load_database()

    def _load_database(self):
        print(f"Loading AISC Member Database from {self.db_path}...")
        try:
            db = pd.read_excel(self.db_path, sheet_name=self.sheet_name)
            allowed_types = ['W', 'HSS', 'L', 'WT', '2L']
            self.db_filtered = db[db['Type'].isin(allowed_types)].copy()
            
            props = ['A', 'W', 'rx', 'ry', 'rz', 'Ix', 'Iy', 'bf', 'b', 'd']
            for p in props:
                self.db_filtered[p] = pd.to_numeric(self.db_filtered[p], errors='coerce')
            
            self.db_filtered['r_min'] = self.db_filtered[['rx', 'ry', 'rz']].min(axis=1)
            self.db_filtered = self.db_filtered.dropna(subset=['A', 'r_min', 'W', 'Ix'])
            print(f"Successfully loaded {len(self.db_filtered)} candidate shapes.")
        except Exception as e:
            print(f"Error loading database: {e}")
            self.db_filtered = None

    def check_shape(self, Ag, r_min, Pu_kips, L_in, Fy=50, E=29000):
        """Checks if a shape passes strength and slenderness criteria. Returns (passes, cap_kips, klr)"""
        klr = L_in / r_min
        if Pu_kips < 0 and klr > 200: return False, 0.0, klr # Compression slenderness
        if Pu_kips >= 0 and klr > 300: return False, 0.0, klr # Tension slenderness
        
        cap_t = 0.9 * Fy * Ag
        cap_c = 0.0
        
        if Pu_kips < 0:
            Fe = (math.pi**2 * E) / (klr**2)
            sl_limit = 4.71 * math.sqrt(E / Fy)
            Fcr = (0.658**(Fy / Fe)) * Fy if klr <= sl_limit else 0.877 * Fe
            cap_c = 0.9 * Fcr * Ag
            
            if cap_c < abs(Pu_kips): return False, cap_c, klr
            return True, cap_c, klr
        else:
            if cap_t < Pu_kips: return False, cap_t, klr
            return True, cap_t, klr

    def select_candidates(self, Pu_kN, L_m, family='HSS', bf_max=None):
        """Returns a list of all shapes capable of supporting the load, sorted by weight."""
        if self.db_filtered is None: return []
        
        # Convert to imperial for AISC checks
        Pu_kips = Pu_kN * 0.224809
        L_in = L_m * 39.3701
        
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
                width_in = 2 * w_b + 0.375 # Assuming 3/8" gusset plate gap
            elif type_str == 'W':
                width_in = row['bf'] if pd.notna(row['bf']) else 0

            # Filter if shape is geometrically wider than chord
            if bf_max is not None and width_in > bf_max:
                continue

            # Enforce A36 steel for all members per user request
            fy = 36
            
            passes, cap_kips, klr = self.check_shape(row['A'], row['r_min'], Pu_kips, L_in, Fy=fy)
            if passes:
                cap_kN = cap_kips / 0.224809
                valid.append({
                    'Label': str(row['AISC_Manual_Label']), 
                    'Weight': float(row['W']), 
                    'Area': float(row['A']), 
                    'Ix': float(row['Ix']), 
                    'KL/r': float(klr),
                    'Capacity_kN': float(cap_kN),
                    'bf_in': float(width_in)
                })
                
        # Sort by weight (lightest first)
        return sorted(valid, key=lambda x: x['Weight'])

    def select_lightest(self, Pu_kN, L_m, family='HSS', bf_max=None):
        """Returns the single lightest shape capable of supporting the load."""
        candidates = self.select_candidates(Pu_kN, L_m, family, bf_max)
        return candidates[0] if candidates else None

# Singleton-like instance for easy import across modules
aisc_db = AISCDatabase()
