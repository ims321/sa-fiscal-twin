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
        
        # Macro baselines for South Africa
        self.base_gdp_zar_mn = 7_000_000  # R7 Trillion
        self.base_debt_zar_mn = 5_200_000 # R5.2 Trillion
        self.interest_rate = 0.10         # 10% average cost of debt
        
    def simulate_year(self, actual_budgets, base_budgets, tax_rate, tariff_shock, bbbee_share):
        Y = np.zeros(len(self.sectors))
        dept_to_sector = {
            'Health': 'Government & Social', 'Education': 'Government & Social',
            'Public Works': 'Construction', 'Trade and Industry': 'Business Services',
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
        
        export_elasticity = -1.30
        for sec in ['Agriculture', 'Mining', 'Manufacturing']:
            idx = self.sectors.index(sec)
            export_change = 500000 * (tariff_shock / 100) * export_elasticity
            Y[idx] += export_change
        
        X = self.Leontief_inverse @ Y
        gdp_effect = np.sum(X * self.va)
        jobs_effect = sum(X[i] * self.emp_multipliers.get(sector, 1.0) for i, sector in enumerate(self.sectors))
        revenue = gdp_effect * (tax_rate / 100)
        
        return gdp_effect, revenue, jobs_effect, pd.DataFrame({'sector': self.sectors, 'gross_output_zar_mn': X})

    def simulate_5_years(self, proposed_budgets, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share):
        history = []
        current_debt = self.base_debt_zar_mn
        
        # Assume a baseline GDP growth of 1.5% per year even without shocks
        current_gdp = self.base_gdp_zar_mn
        
        for year in range(1, 6):
            total_proposed = sum(proposed_budgets.values())
            actual_budgets = proposed_budgets.copy()
            budget_scaled = False
            
            # Deduct interest payments from the envelope for years > 1
            interest_payment = current_debt * self.interest_rate if year > 1 else 0
            effective_envelope = envelope - interest_payment
            
            if total_proposed > effective_envelope:
                if allow_deficit:
                    pass
                else:
                    scale_factor = effective_envelope / total_proposed if total_proposed > 0 else 1
                    actual_budgets = {k: v * scale_factor for k, v in proposed_budgets.items()}
                    total_proposed = effective_envelope
                    budget_scaled = True
            
            budget_change = total_proposed - sum(base_budgets.values())
            gdp_effect, revenue, jobs_effect, sector_df = self.simulate_year(
                actual_budgets, base_budgets, tax_rate, tariff_shock, bbbee_share
            )
            
            net_fiscal = revenue - budget_change
            
            # Update debt and GDP for next year
            current_debt -= net_fiscal 
            current_gdp = current_gdp * 1.015 + gdp_effect 
            
            history.append({
                "Year": f"Year {year}",
                "GDP": current_gdp / 1_000_000, # In Trillions
                "Debt": current_debt / 1_000_000, # In Trillions
                "Debt_to_GDP": (current_debt / current_gdp) * 100,
                "Jobs_Created": jobs_effect,
                "Net_Fiscal_mn": net_fiscal,
                "Interest_Payment_mn": interest_payment,
                "Budget_Scaled": budget_scaled,
                "Actual_Spend_mn": total_proposed
            })
            
        return pd.DataFrame(history)
