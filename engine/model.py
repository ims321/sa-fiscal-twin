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
        
        # Comprehensive mapping of all departments/functions to economic sectors
        self.dept_to_sector = {
            'The Presidency': 'Government & Social', 'Parliament': 'Government & Social', 'Cooperative Governance': 'Government & Social',
            'Home Affairs': 'Government & Social', 'International Relations': 'Government & Social', 'National Treasury': 'Government & Social',
            'Public Works': 'Construction', 'Basic Education': 'Government & Social', 'Higher Education': 'Government & Social',
            'Health': 'Government & Social', 'Social Development': 'Government & Social', 'Defence': 'Government & Social',
            'Police': 'Government & Social', 'Correctional Services': 'Government & Social', 'Justice': 'Government & Social',
            'Labour': 'Government & Social', 'Agriculture': 'Agriculture', 'Communications': 'Business Services',
            'Public Enterprises': 'Utilities', 'Human Settlements': 'Construction', 'Water and Sanitation': 'Utilities',
            'Science and Tech': 'Business Services', 'Tourism': 'Trade', 'Trade and Industry': 'Business Services',
            'Transport': 'Transport', 'Sport and Culture': 'Government & Social', 'Small Business': 'Business Services',
            # Provincial mapping
            'Health (Prov)': 'Government & Social', 'Education (Prov)': 'Government & Social', 'Roads': 'Construction', 'Social Dev': 'Government & Social', 'Agriculture (Prov)': 'Agriculture',
            # Local mapping
            'Water': 'Utilities', 'Electricity': 'Utilities', 'Roads & Transport': 'Construction', 'Waste Management': 'Utilities',
            'Community & Public Safety': 'Government & Social', 'Health & Environmental': 'Government & Social', 'Housing & Planning': 'Construction'
        }
        
    def simulate_year(self, budgets, base_budgets, levers):
        Y = np.zeros(len(self.sectors))
        
        # 1. National Sphere Shocks
        for dept, new_total in budgets['national'].items():
            delta = new_total - base_budgets['national'].get(dept, 0)
            sector = self.dept_to_sector.get(dept, 'Government & Social')
            idx = self.sectors.index(sector)
            if levers['bbbee'] > 0 and delta > 0:
                redirect = delta * (levers['bbbee'] / 100)
                Y[idx] += (delta - redirect)
                Y[self.sectors.index('Business Services')] += redirect
            else:
                Y[idx] += delta
        
        # 2. Provincial Sphere Shocks
        for prov, depts in budgets['provincial'].items():
            for dept, new_total in depts.items():
                delta = new_total - base_budgets['provincial'].get(prov, {}).get(dept, 0)
                sector = self.dept_to_sector.get(dept, 'Government & Social')
                Y[self.sectors.index(sector)] += delta
        
        # 3. Local Sphere Shocks
        for func, new_total in budgets['local'].items():
            delta = new_total - base_budgets['local'].get(func, 0)
            sector = self.dept_to_sector.get(func, 'Government & Social')
            Y[self.sectors.index(sector)] += delta

        # 4. Trade & Industrial Shocks
        for sec in ['Agriculture', 'Mining', 'Manufacturing']:
            idx = self.sectors.index(sec)
            export_change = 500000 * (levers['tariff'] / 100) * -1.30
            Y[idx] += export_change
            
        Y = Y * (1 + (levers['markup_cap'] / 100))
        A_modified = self.A * (1 + (levers['localization'] / 100))
        Leontief_modified = np.linalg.inv(self.I - A_modified)
        
        # 5. Tax Drags on Demand
        for i, sec in enumerate(self.sectors):
            if sec in ['Trade', 'Services', 'Business Services', 'Transport']:
                Y[i] *= (1 - ((levers['vat'] - 15) / 100 * 0.5) - ((levers['fuel_levy'] - 1.0) * 0.1))
            if sec in ['Finance', 'Manufacturing', 'Construction']:
                Y[i] *= (1 - ((levers['cit'] - 27) / 100 * 0.3) - ((levers['repo_rate'] - 8.25) / 100 * 0.5))
            if sec in ['Trade', 'Services', 'Government & Social']:
                Y[i] *= (1 - ((levers['pit'] - 30) / 100 * 0.4))

        X = Leontief_modified @ Y
        gdp_effect = np.sum(X * self.va)
        
        # 6. Step the ABM
        demand_shocks = {sec: 1.0 + (X[i] / 100000) for i, sec in enumerate(self.sectors)}
        net_job_change = self.firm_market.step(levers['cit'], levers['markup_cap'], levers['repo_rate'], levers['eti'], demand_shocks)
        hhi = self.firm_market.calculate_hhi()
        
        # 7. Revenue Calculation
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
        
        # Calculate total base spending across all spheres
        total_base_spend = sum(base_budgets['national'].values())
        for prov in base_budgets['provincial'].values():
            total_base_spend += sum(prov.values())
        total_base_spend += sum(base_budgets['local'].values())
        
        for year in range(1, 6):
            # Calculate total proposed spending
            total_proposed = sum(budgets['national'].values())
            for prov in budgets['provincial'].values():
                total_proposed += sum(prov.values())
            total_proposed += sum(budgets['local'].values())
            
            interest = current_debt * (levers['repo_rate'] / 100) if year > 1 else 0
            
            # If not allowing deficit, scale down proportionally
            if total_proposed > (total_base_spend + 50000) and not levers['allow_deficit']:
                scale = (total_base_spend + 50000) / total_proposed
                # Deep copy and scale
                import copy
                actual_budgets = copy.deepcopy(budgets)
                for k in actual_budgets['national']: actual_budgets['national'][k] *= scale
                for p in actual_budgets['provincial']:
                    for k in actual_budgets['provincial'][p]: actual_budgets['provincial'][p][k] *= scale
                for k in actual_budgets['local']: actual_budgets['local'][k] *= scale
                total_proposed = total_base_spend + 50000
            else:
                import copy
                actual_budgets = copy.deepcopy(budgets)
                
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
