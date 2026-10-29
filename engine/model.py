import numpy as np
import pandas as pd
import os
import requests
from engine.microsim import HouseholdSimulator
from engine.firm_abm import FirmMarket

class LeontiefTwin:
    def __init__(self, A_matrix, va_ratios, sectors):
        self.A = A_matrix.values
        self.va = va_ratios.values
        self.sectors = list(sectors)
        self.I = np.eye(self.A.shape[0])
        self.base_Leontief_inverse = np.linalg.inv(self.I - self.A)
        self.microsim = HouseholdSimulator()
        self.firm_market = FirmMarket(num_firms=500)
        
        self.base_gdp_zar_mn = 7_000_000  
        self.base_debt_zar_mn = 5_200_000 
        self.interest_rate = 0.10         
        
    def simulate_year(self, actual_budgets, base_budgets, vat_rate, cit_rate, pit_rate, tariff_shock, bbbee_share, markup_reduction, localization):
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
            
        demand_boost = 1 + (markup_reduction / 100)
        Y = Y * demand_boost
        
        A_modified = self.A * (1 + (localization / 100))
        Leontief_modified = np.linalg.inv(self.I - A_modified)
        
        vat_drag = 1 - ((vat_rate - 15) / 100 * 0.5) 
        cit_drag = 1 - ((cit_rate - 27) / 100 * 0.3)
        pit_drag = 1 - ((pit_rate - 30) / 100 * 0.4)
        
        for i, sec in enumerate(self.sectors):
            if sec in ['Trade', 'Services', 'Business Services', 'Transport']:
                Y[i] *= vat_drag
            if sec in ['Finance', 'Manufacturing', 'Construction']:
                Y[i] *= cit_drag
            if sec in ['Trade', 'Services', 'Government & Social']:
                Y[i] *= pit_drag

        X = Leontief_modified @ Y
        gdp_effect = np.sum(X * self.va)
        
        demand_shocks = {sec: 1.0 + (X[i] / 100000) for i, sec in enumerate(self.sectors)}
        net_job_change = self.firm_market.step(cit_rate, markup_reduction, demand_shocks)
        hhi = self.firm_market.calculate_hhi()
        
        # CALIBRATION: Base revenue matches base spending to create a realistic deficit
        # Base spending is ~600,000. Let's set base revenue to ~550,000.
        base_revenue = 550_000
        revenue_multiplier = ((vat_rate / 15) * 0.3) + ((cit_rate / 27) * 0.2) + ((pit_rate / 30) * 0.5)
        revenue = (base_revenue + gdp_effect * 0.1) * revenue_multiplier
        
        return gdp_effect, revenue, net_job_change, hhi, pd.DataFrame({'sector': self.sectors, 'gross_output_zar_mn': X})

    def simulate_5_years(self, budget_matrix, base_budgets, envelope, allow_deficit, vat_rate, cit_rate, pit_rate, tariff_shock, bbbee_share, markup_reduction, localization):
        history = []
        current_debt = self.base_debt_zar_mn
        current_gdp = self.base_gdp_zar_mn
        
        self.microsim = HouseholdSimulator()
        self.firm_market = FirmMarket(num_firms=500)
        
        for year in range(1, 6):
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
            
            gdp_effect, revenue, net_job_change, hhi, _ = self.simulate_year(
                actual_budgets, base_budgets, vat_rate, cit_rate, pit_rate, tariff_shock, bbbee_share, markup_reduction, localization
            )
            
            net_fiscal = revenue - budget_change
            current_debt -= net_fiscal 
            current_gdp = current_gdp * 1.015 + gdp_effect 
            
            self.microsim.households = self.microsim.apply_policy_shocks(net_job_change, vat_rate, pit_rate)
            micro_metrics = self.microsim.get_metrics(self.microsim.households)
            
            history.append({
                "Year": f"Year {year}",
                "GDP": current_gdp / 1_000_000,
                "Debt": current_debt / 1_000_000,
                "Debt_to_GDP": (current_debt / current_gdp) * 100,
                "Net_Jobs": net_job_change,
                # Scale employment by 1000 to represent real economy size
                "Total_Employment": self.firm_market.get_total_employment() * 1000,
                "Net_Fiscal_mn": net_fiscal,
                "Gini": micro_metrics["current_gini"],
                "Poverty_Rate": micro_metrics["current_poverty"],
                "HHI": hhi
            })
            
        return pd.DataFrame(history)

    def ask_ai_advisor(self, query, scenario_data):
        base_url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
        api_key = os.getenv("OMNIROUTE_API_KEY", "optional")
        
        final_year = scenario_data.iloc[-1]
        summary = f"""
        - Year 5 GDP: R {final_year['GDP']:.2f} Trillion
        - Year 5 Debt-to-GDP: {final_year['Debt_to_GDP']:.1f}%
        - Year 5 Total Employment: {final_year['Total_Employment']:,.0f} workers
        - Year 5 Gini Coefficient: {final_year['Gini']:.3f}
        - Year 5 Poverty Rate: {final_year['Poverty_Rate']:.1f}%
        - Year 5 Market Concentration (HHI): {final_year['HHI']:.0f}
        """
        
        system_prompt = f"""
        You are a Chief Economist advising the South African National Treasury.
        Here is the final 5-year macroeconomic simulation data based on the policy changes:
        {summary}
        
        Answer the user's question professionally. Focus on trade-offs between GDP, Debt, Employment, Inequality, and Market Concentration. Keep it concise (under 250 words).
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
                timeout=120
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"AI Advisor unavailable. Error: {e}"
