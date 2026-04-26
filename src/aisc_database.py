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
            
            # Expanded properties for buckling analysis
            # Added 't' for angles, 'h' for web depth
            props = [
                'A', 'W', 'rx', 'ry', 'rz', 'Ix', 'Iy', 'bf', 'b', 'd', 'h', 'tw', 'tf', 't',
                'J', 'Cw', 'ro', 'H', 'b/t', 'h/tw', 'b/tdes', 'tdes'
            ]
            for p in props:
                if p in self.db_filtered.columns:
                    # Robust numeric conversion: non-numerics (like '–') become NaN, then 0.0
                    self.db_filtered[p] = pd.to_numeric(self.db_filtered[p], errors='coerce').fillna(0)
            
            # Special handling for L/2L missing properties
            for idx, row in self.db_filtered.iterrows():
                ts = str(row['Type'])
                if ts in ['L', '2L']:
                    # J approximation for angles: 1/3 * sum(b*t^3)
                    if row['J'] <= 0:
                        # Use 't' if available, otherwise 'tdes', then 'tw'
                        t = row['t'] if row['t'] > 0 else (row['tdes'] if row['tdes'] > 0 else row['tw'])
                        b, d = row['b'], row['d']
                        if t > 0:
                            j_approx = (1.0/3.0) * (b + d - t) * (t**3)
                            if ts == '2L': j_approx *= 2
                            self.db_filtered.at[idx, 'J'] = j_approx
                    
                    # Estimate rz for 2L if missing (approx 0.39 * b_smallest)
                    if ts == '2L' and row['rz'] <= 0:
                        self.db_filtered.at[idx, 'rz'] = 0.39 * min(row['b'], row['d'] if row['d']>0 else 999)

                # Consistent ro and H handling
                if ts in ['L', 'WT', '2L']:
                    if row['ro'] <= 0:
                        # Estimate ro: sqrt(rx^2 + ry^2 + dist_to_sc^2)
                        # SC is approx at intersection of legs.
                        self.db_filtered.at[idx, 'ro'] = math.sqrt(row['rx']**2 + row['ry']**2 + 1.0) # conservative floor
                    if row['H'] <= 0:
                        self.db_filtered.at[idx, 'H'] = 0.8 # common for angles/tees

            # Calculation of r_min from non-zero radii of gyration
            def _get_rmin(r):
                c = [v for v in [r['rx'], r['ry'], r['rz']] if v > 0]
                return min(c) if c else 0.01

            self.db_filtered['r_min'] = self.db_filtered.apply(_get_rmin, axis=1)
            
            # Basic cleanup
            self.db_filtered = self.db_filtered[self.db_filtered['A'] > 0]
            print(f"Successfully loaded {len(self.db_filtered)} candidate shapes with buckling properties.")
        except Exception as e:
            print(f"Error loading database: {e}")
            self.db_filtered = None

    def _calc_Q(self, row, Fy, E):
        """Calculates the reduction factor Q for slender elements (AISC E7)."""
        type_str = str(row['Type'])
        Q = 1.0
        
        # Case 3: Angles (unstiffened)
        if type_str == 'L':
            bt = row['b/t']
            if bt <= 0: return 1.0 # Safe fallback
            
            limit_r = 0.45 * math.sqrt(E / Fy)
            if bt > limit_r:
                if bt <= 0.91 * math.sqrt(E/Fy):
                    Q = 1.34 - 0.76 * bt * math.sqrt(Fy/E)
                else:
                    Q = 0.53 * E / (Fy * bt**2)
        
        # Case 1 & 10: W-shapes
        elif type_str == 'W':
            # Flange
            b_tf = row['bf/2tf'] if 'bf/2tf' in row and row['bf/2tf'] > 0 else (row['bf']/(2*row['tf']) if row['tf']>0 else 0)
            Qs = 1.0
            if b_tf > 0:
                limit_f = 0.56 * math.sqrt(E/Fy)
                if b_tf > limit_f:
                    if b_tf <= 1.03 * math.sqrt(E/Fy):
                        Qs = 1.415 - 0.74 * b_tf * math.sqrt(Fy/E)
                    else:
                        Qs = 0.69 * E / (Fy * b_tf**2)
            
            # Web
            htw = row['h/tw']
            Qa = 1.0
            if htw > 0:
                limit_w = 1.49 * math.sqrt(E/Fy)
                if htw > limit_w:
                    f = Fy
                    be = 1.92 * row['tw'] * math.sqrt(E/f) * (1 - 0.34/(htw * math.sqrt(E/f)))
                    be = min(be, row['h'] if row['h'] > 0 else 1000)
                    Ae = row['A'] - (row['h'] - be)*row['tw'] if row['h'] > 0 else row['A']
                    Qa = Ae / row['A']
            Q = Qs * Qa

        elif type_str == 'WT':
            b_tf = row['bf/2tf'] if 'bf/2tf' in row and row['bf/2tf'] > 0 else (row['bf']/(2*row['tf']) if row['tf']>0 else 0)
            if b_tf > 0:
                limit_f = 0.56 * math.sqrt(E/Fy)
                if b_tf > limit_f:
                    if b_tf <= 1.03 * math.sqrt(E/Fy):
                        Q = 1.415 - 0.74 * b_tf * math.sqrt(Fy/E)
                    else:
                        Q = 0.69 * E / (Fy * b_tf**2)
        
        return max(0.1, min(1.0, Q))

    def _calc_Fe(self, row, Pu_kips, L_in, E):
        """Calculates the elastic buckling stress Fe considering FB, TB, and FTB (AISC E3/E4)."""
        type_str = str(row['Type'])
        G = 11200 # ksi
        
        # Flexural Buckling (E3)
        rmin = row['r_min']
        Fe_fb = (math.pi**2 * E) / ((L_in / rmin)**2) if L_in > 0 else 1e6
        
        Fe = Fe_fb
        
        if type_str in ['L', 'WT', '2L']:
            J, Cw, ro, H = row['J'], row['Cw'], row['ro'], row['H']
            if ro > 0:
                Fez = ( (math.pi**2 * E * Cw / (L_in**2)) + G * J ) / (row['A'] * ro**2) if L_in > 0 else 1e6
                
                if type_str == 'WT' or type_str == '2L':
                    # Singly symmetric
                    Fey = (math.pi**2 * E) / ((L_in / row['ry'])**2) if row['ry'] > 0 and L_in > 0 else 1e6
                    if H > 0:
                        denom = (Fey + Fez)
                        if denom > 0:
                            term = 1 - (4*Fey*Fez*H)/(denom**2)
                            if term >= 0:
                                Fe_ftb = (denom / (2*H)) * (1 - math.sqrt(term))
                                Fe = min(Fe, Fe_ftb)
                elif type_str == 'L':
                    # Simplified torsional floor
                    Fe = min(Fe, Fez) if Fez > 0 else Fe
        
        return max(0.1, Fe)

    def check_shape(self, row, Pu_kips, L_in, Fy=36, E=29000):
        """Comprehensive AISC Chapter E check."""
        Ag = row['A']
        rmin = row['r_min']
        if rmin <= 0: return False, 0.0, 999
        klr = L_in / rmin
        
        # Slenderness limits
        if Pu_kips < 0 and klr > 200: return False, 0.0, klr
        if Pu_kips >= 0 and klr > 300: return False, 0.0, klr
        
        if Pu_kips >= 0:
            cap = 0.9 * Fy * Ag
            return (cap >= Pu_kips), cap, klr
        else:
            Q = self._calc_Q(row, Fy, E)
            Fe = self._calc_Fe(row, Pu_kips, L_in, E)
            
            if Q * Fe >= 0.44 * Fy:
                Fcr = Q * (0.658**(Q * Fy / Fe)) * Fy
            else:
                Fcr = 0.877 * Fe
                
            cap = 0.9 * Fcr * Ag
            return (cap >= abs(Pu_kips)), cap, klr

    def select_candidates(self, Pu_kN, L_m, family='2L', bf_max=None):
        """Returns a list of all shapes capable of supporting the load, sorted by weight."""
        if self.db_filtered is None: return []
        
        Pu_kips = Pu_kN * 0.224809
        L_in = L_m * 39.3701
        subset = self.db_filtered[self.db_filtered['Type'] == family] if family else self.db_filtered
        valid = []
        
        for _, row in subset.iterrows():
            width_in = 0
            ts = str(row['Type'])
            if ts == 'WT': width_in = row['bf']
            elif ts == 'L': width_in = max(row['b'], row['d'])
            elif ts == '2L': width_in = 2 * row['b'] + 0.375
            elif ts == 'W': width_in = row['bf']
            elif ts == 'HSS': width_in = row['bf'] if row['bf'] > 0 else row['d']

            if bf_max is not None and width_in > bf_max:
                continue

            passes, cap_kips, klr = self.check_shape(row, Pu_kips, L_in, Fy=36)
            if passes:
                cap_kN = cap_kips / 0.224809
                valid.append({
                    'Label': str(row['AISC_Manual_Label']), 
                    'Weight': float(row['W']), 
                    'Area': float(row['A']), 
                    'Ix': float(row['Ix']), 
                    'KL/r': float(klr),
                    'Capacity_kN': float(cap_kN),
                    'bf_in': float(width_in),
                    'tw_in': float(row['tw']) if row['tw'] > 0 else (row['tdes'] if 'tdes' in row else 0.0)
                })
                
        return sorted(valid, key=lambda x: x['Weight'])

    def select_lightest(self, Pu_kN, L_m, family='2L', bf_max=None):
        candidates = self.select_candidates(Pu_kN, L_m, family, bf_max)
        return candidates[0] if candidates else None

    @staticmethod
    def get_commercial_label(shape):
        """Returns a Philippine commercial equivalent label for HSS sections."""
        label = shape.get('Label', '')
        if not label or not label.startswith('HSS'):
            return label
        
        try:
            parts = label.replace('HSS', '').split('X')
            if len(parts) < 2: return label
            
            def parse_frac(s):
                if '-' in s:
                    w, f = s.split('-')
                    num, den = f.split('/')
                    return float(w) + float(num)/float(den)
                if '/' in s:
                    num, den = s.split('/')
                    return float(num)/float(den)
                return float(s)

            dims = [parse_frac(p) for p in parts[:-1]]
            t_frac = parse_frac(parts[-1])
            
            dims_mm = [int(round(d * 25.4)) for d in dims]
            t_mm = round(t_frac * 25.4, 1)
            
            if len(dims_mm) == 1:
                return f"Pipe {dims_mm[0]}mm Dia. x {t_mm}mm"
            elif len(dims_mm) == 2:
                if dims_mm[0] == dims_mm[1]:
                    return f"Square Pipe {dims_mm[0]}x{dims_mm[1]}x{t_mm}mm"
                else:
                    return f"Rect. Pipe {dims_mm[0]}x{dims_mm[1]}x{t_mm}mm"
        except:
            pass
        return label

# Singleton-like instance for easy import across modules
aisc_db = AISCDatabase()
