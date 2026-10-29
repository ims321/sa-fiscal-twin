import numpy as np
import pandas as pd
import os
import requests

class LeontiefTwin:
    def __init__(self, A_matrix, va_ratios, sectors):
        self.A = A_matrix.values
        self.va = va_ratios.values
        self.sectors = list(sectors)
        self.I = np.eye(self.A.shape[0])
        
        # Base Leontief Inverse
        self.base_Leontief_inverse = np.linalg.inv(self.I - self.A)
        
        self.emp_multipliers = {
            'Agriculture': 4.0, 'Mining': 1.2, 'Manufacturing': 2.5,
            'Utilities': 1.5, 'Construction': 5.0, 'Trade': 3.5,
            'Transport': 3.0, 'Finance': 1.8, 'Business Services': 4.2,
            'Government & Social': 3.8
        }
        
        self.base_gdp_zar_mn = 7_000_000  
        self.base_debt_zar_mn = 5_200_000 
        self.interest_rate = 0.10         
        
    def simulate_year(self, actual_budgets, base_budgets, tax_rate, tariff_shock, bbbee_share, markup_reduction, localization):
        Y = np.zeros(len(self.sectors))
        dept_to_sector = {
            'Health': 'Government & Social', 'Education': 'Government & Social',
            'Public Works': 'Construction', 'Trade and Industry': 'Business Services',
            'Small Business Development': 'Business Services'
        }
        
        # 1. Budget Shocks
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
        
        # 2. Tariff Shock (Export elasticity)
        export_elasticity = -1.30
        for sec in ['Agriculture', 'Mining', 'Manufacturing']:
            idx = self.sectors.index(sec)
            export_change = 500000 * (tariff_shock / 100) * export_elasticity
            Y[idx] += export_change
            
        # 3. Competition Policy (Markup reduction boosts real demand)
        # If markups fall by 1%, it's like a 1% increase in real income for consumers
        demand_boost = 1 + (markup_reduction / 100)
        Y = Y * demand_boost
        
        # 4. Localization (Increases domestic inter-industry linkages)
        # If localization is 20%, we scale the A matrix up by 20% (simplistic proxy for import substitution)
        A_modified = self.A * (1 + (localization / 100))
        Leontief_modified = np.linalg.inv(self.I - A_modified)
        
        X = Leontief_modified @ Y
        gdp_effect = np.sum(X * self.va)
        jobs_effect = sum(X[i] * self.emp_multipliers.get(sector, 1.0) for i, sector in enumerate(self.sectors))
        revenue = gdp_effect * (tax_rate / 100)
        
        return gdp_effect, revenue, jobs_effect, pd.DataFrame({'sector': self.sectors, 'gross_output_zar_mn': X})

    def simulate_5_years(self, budget_matrix, base_budgets, envelope, allow_deficit, tax_rate, tariff_shock, bbbee_share, markup_reduction, localization):
        history = []
        current_debt = self.base_debt_zar_mn
        current_gdp = self.base_gdp_zar_mn
        
        for year in range(1, 6):
            # Get budgets for this specific year from the matrix
            year_budgets = budget_matrix.iloc[year-1].to_dict()
            
            total_proposed = sum(year_budgets.values())
            actual_budgets = year_budgets.copy()
            budget_scaled = False
            
            interest_payment = current_debt * self.interest_rate if year > 1 else 0
            effective_envelope = envelope - interest_payment
            
            if total_proposed > effective_envelope and not allow_deficit:
                scale_factor = effective_envelope / total_proposed if total_proposed > 0 else 1
                actual_budgets = {k: v * scale_factor for k, v in year_budgets.items()}
                total_proposed = effective_envelope
                budget_scaled = True
            
            budget_change = total_proposed - sum(base_budgets.values())
            
            gdp_effect, revenue, jobs_effect, _ = self.simulate_year(
                actual_budgets, base_budgets, tax_rate, tariff_shock, bbbee_share, markup_reduction, localization
            )
            
            net_fiscal = revenue - budget_change
            current_debt -= net_fiscal 
            current_gdp = current_gdp * 1.015 + gdp_effect 
            
            history.append({
                "Year": f"Year {year}",
                "GDP": current_gdp / 1_000_000,
                "Debt": current_debt / 1_000_000,
                "Debt_to_GDP": (current_debt / current_gdp) * 100,
                "Jobs_Created": jobs_effect,
                "Net_Fiscal_mn": net_fiscal,
                "Interest_Payment_mn": interest_payment,
                "Actual_Spend_mn": total_proposed
            })
            
        return pd.DataFrame(history)

    def ask_ai_advisor(self, query, scenario_data):
        """Connects to Omniroute to generate a report or answer questions."""
        base_url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
        api_key = os.getenv("OMNIROUTE_API_KEY", "optional")
        
        system_prompt = f"""
        You are a Chief Economist advising the South African National Treasury.
        Here is the current macroeconomic simulation data based on the user's policy levers:
        {scenario_data.to_string()}
        
        Answer the user's question professionally, focusing on trade-offs between GDP, Debt, and Jobs. Keep it concise.
        """
        
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "auto",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "temperature": 0.3
                },
                timeout=30
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"AI Advisor unavailable. Ensure Omniroute is running. Error: {e}"
