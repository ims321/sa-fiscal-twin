import numpy as np
import pandas as pd

class LeontiefTwin:
    def __init__(self, A_matrix, va_ratios, sectors):
        self.A = A_matrix.values
        self.va = va_ratios.values
        self.sectors = list(sectors)
        self.I = np.eye(self.A.shape[0])
        self.Leontief_inverse = np.linalg.inv(self.I - self.A)
        
        self.emp_multipliers = {
            'Agriculture': 4.0, 'Mining': 1.2, 'Manufacturing': 2.5,
            'Utilities': 1.5, 'Construction': 5.0, 'Trade': 3.5,
            'Transport': 3.0, 'Finance': 1.8, 'Business Services': 4.2,
            'Government & Social': 3.8
        }
        
    def simulate(self, proposed_budgets, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share):
        # --- 1. BUDGET ENVELOPE LOGIC ---
        total_proposed = sum(proposed_budgets.values())
        total_base = sum(base_budgets.values())
        
        actual_budgets = proposed_budgets.copy()
        budget_scaled = False
        
        if total_proposed > envelope:
            if allow_deficit:
                pass # Let them spend over the envelope
            else:
                # Scale down proportionally to fit the envelope
                scale_factor = envelope / total_proposed
                actual_budgets = {k: v * scale_factor for k, v in proposed_budgets.items()}
                total_proposed = envelope
                budget_scaled = True
                
        budget_change = total_proposed - total_base
        
        # --- 2. SHOCK VECTOR (Y) ---
        Y = np.zeros(len(self.sectors))
        
        dept_to_sector = {
            'Health': 'Government & Social',
            'Education': 'Government & Social',
            'Public Works': 'Construction',
            'Trade and Industry': 'Business Services',
            'Small Business Development': 'Business Services'
        }
        
        for dept, new_total in actual_budgets.items():
            delta = new_total - base_budgets.get(dept, 0)
            sector = dept_to_sector.get(dept, 'Government & Social')
            idx = self.sectors.index(sector)
            
            if bbbee_share > 0 and delta > 0:
                redirect = delta * (bbbee_share / 100)
                Y[idx] += (delta - redirect)
                Y[self.sectors.index('Business Services')] += redirect
            else:
                Y[idx] += delta
        
        # Tariff effect
        export_elasticity = -1.30
        for sec in ['Agriculture', 'Mining', 'Manufacturing']:
            idx = self.sectors.index(sec)
            export_change = 500000 * (tariff_shock / 100) * export_elasticity
            Y[idx] += export_change
        
        # --- 3. LEONTIEF MATH ---
        X = self.Leontief_inverse @ Y
        gdp_effect = np.sum(X * self.va)
        
        jobs_effect = sum(X[i] * self.emp_multipliers.get(sector, 1.0) for i, sector in enumerate(self.sectors))
        revenue = gdp_effect * (tax_rate / 100)
        net_fiscal = revenue - budget_change
        
        results = pd.DataFrame({'sector': self.sectors, 'gross_output_zar_mn': X})
        
        return results, gdp_effect, revenue, jobs_effect, net_fiscal, actual_budgets, budget_scaled
