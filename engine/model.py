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
        
    def simulate_year(self, budgets, base_budgets, levers):
        Y = np.zeros(len(self.sectors))
        
        # Mapping for all three spheres
        dept_to_sector = {
            # National
            'The Presidency': 'Government & Social', 'Parliament': 'Government & Social', 'Cooperative Governance': 'Government & Social',
            'Home Affairs': 'Government & Social', 'International Relations': 'Government & Social', 'National Treasury': 'Government & Social',
            'Public Works': 'Construction', 'Basic Education': 'Government & Social', 'Higher Education': 'Government & Social',
            'Health': 'Government & Social', 'Social Development': 'Government & Social', 'Defence': 'Government & Social',
            'Police': 'Government & Social', 'Correctional Services': 'Government & Social', 'Justice': 'Government & Social',
            'Labour': 'Government & Social', 'Agriculture': 'Agriculture', 'Communications': 'Business Services',
            'Public Enterprises': 'Utilities', 'Human Settlements': 'Construction', 'Water and Sanitation': 'Utilities',
            'Science and Tech': 'Business Services', 'Tourism': 'Trade', 'Trade and Industry': 'Business Services',
            'Transport': 'Transport', 'Sport and Culture': 'Government & Social', 'Small Business': 'Business Services',
            # Provincial
            'Provincial Health': 'Government & Social', 'Provincial Education': 'Government & Social',
            'Provincial Roads': 'Construction', 'Provincial Social Dev': 'Government & Social',
            # Local
            'Metro Water': 'Utilities', 'Metro Electricity': 'Utilities', 'Metro Roads': 'Construction', 'Metro Waste': 'Utilities'
        }
        
        # 1. Budget Shocks (All Spheres)
        for sphere in ['national', 'provincial', 'local']:
            for dept, new_total in budgets[sphere].items():
                base_total = base_budgets[sphere].get(dept, 0)
                delta = new_total - base_total
                sector = dept_to_sector.get(dept, 'Government & Social')
                idx = self.sectors.index(sector)
                
                if levers['bbbee'] > 0 and delta > 0:
                    redirect = delta * (levers['bbbee'] / 100)
                    Y[idx] += (delta - redirect)
                    Y[self.sectors.index('Business Services')] += redirect
                else:
                    Y[idx] += delta
        
        # 2. Trade & Industrial Shocks
        for sec in ['Agriculture', 'Mining', 'Manufacturing']:
            idx = self.sectors.index(sec)
            export_change = 500000 * (levers['tariff'] / 100) * -1.30
            Y[idx] += export_change
            
        Y = Y * (1 + (levers['markup_cap'] / 100))
        A_modified = self.A * (1 + (levers['localization'] / 100))
        Leontief_modified = np.linalg.inv(self.I - A_modified)
        
        # 3. Tax Drags on Demand
        for i, sec in enumerate(self.sectors):
            if sec in ['Trade', 'Services', 'Business Services', 'Transport']:
                Y[i] *= (1 - ((levers['vat'] - 15) / 100 * 0.5) - ((levers['fuel_levy'] - 1.0) * 0.1))
            if sec in ['Finance', 'Manufacturing', 'Construction']:
                Y[i] *= (1 - ((levers['cit'] - 27) / 100 * 0.3) - ((levers['repo_rate'] - 8.25) / 100 * 0.5))
            if sec in ['Trade', 'Services', 'Government & Social']:
                Y[i] *= (1 - ((levers['pit'] - 30) / 100 * 0.4))

        X = Leontief_modified @ Y
        gdp_effect = np.sum(X * self.va)
        
        # 4. Step the ABM
        demand_shocks = {sec: 1.0 + (X[i] / 100000) for i, sec in enumerate(self.sectors)}
        net_job_change = self.firm_market.step(levers['cit'], levers['markup_cap'], levers['repo_rate'], levers['eti'], demand_shocks)
        hhi = self.firm_market.calculate_hhi()
        
        # 5. Revenue Calculation (Base + Taxes)
        base_rev = 1_500_000
        rev_mult = ((levers['vat'] / 15) * 0.25) + ((levers['cit'] / 27) * 0.2) + ((levers['pit'] / 30) * 0.35) + (levers['fuel_levy'] * 0.1) + (levers['sin_tax'] * 0.1)
        revenue = (base_rev + gdp_effect * 0.1) * rev_mult
        
        return gdp_effect, revenue, net_job_change, hhi

    def simulate_5_years(self, budgets, base_budgets, levers):
        history = []
        current_debt = self.base_debt_zar_mn
        current_gdp = self.base_gdp_zar_mn
        self.microsim = HouseholdSimulator()
        self.firm_market = FirmMarket(num_firms=500)
        
        total_base_spend = sum(base_budgets['national'].values()) + sum(base_budgets['provincial'].values()) + sum(base_budgets['local'].values())
        
        for year in range(1, 6):
            # Sum all proposed budgets
            total_proposed = sum(budgets['national'].values()) + sum(budgets['provincial'].values()) + sum(budgets['local'].values())
            actual_budgets = {s: budgets[s].copy() for s in budgets}
            
            interest = current_debt * (levers['repo_rate'] / 100) if year > 1 else 0
            
            # If not allowing deficit, scale down budgets
            if total_proposed > (total_base_spend + 50000) and not levers['allow_deficit']: # 50bn buffer
                scale = (total_base_spend + 50000) / total_proposed
                for s in actual_budgets:
                    for k in actual_budgets[s]:
                        actual_budgets[s][k] *= scale
                total_proposed = total_base_spend + 50000
                
            budget_change = total_proposed - total_base_spend
            gdp_effect, revenue, net_job_change, hhi = self.simulate_year(actual_budgets, base_budgets, levers)
            
            net_fiscal = revenue - budget_change - interest
            current_debt -= net_fiscal 
            current_gdp = current_gdp * 1.015 + gdp_effect 
            
            self.microsim.households = self.microsim.apply_policy_shocks(net_job_change, levers['vat'], levers['pit'], levers['grant_uplift'], levers['min_wage'], levers['fuel_levy'])
            micro = self.microsim.get_metrics(self.microsim.households)
            
            history.append({
                "Year": f"Year {year}",
                "GDP": current_gdp / 1_000_000,
                "Debt_to_GDP": (current_debt / current_gdp) * 100,
                "Total_Employment": self.firm_market.get_total_employment() * 1000,
                "Net_Fiscal_mn": net_fiscal,
                "Gini": micro["current_gini"],
                "Poverty_Rate": micro["current_poverty"],
                "HHI": hhi
            })
            
        return pd.DataFrame(history)

    def ask_ai_advisor(self, query, scenario_data):
        base_url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
        api_key = os.getenv("OMNIROUTE_API_KEY", "optional")
        final = scenario_data.iloc[-1]
        
        prompt = f"Year 5 Data: GDP R{final['GDP']:.2f}T, Debt {final['Debt_to_GDP']:.1f}%, Poverty {final['Poverty_Rate']:.1f}%, HHI {final['HHI']:.0f}. Answer: {query}"
        
        try:
            res = requests.post(f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json={"model": "auto", "messages": [{"role": "system", "content": "You are a Chief Economist advising Treasury. Keep answers under 250 words."}, {"role": "user", "content": prompt}], "temperature": 0.3}, timeout=300)
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"AI unavailable: {e}"
