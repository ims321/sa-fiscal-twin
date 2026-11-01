import numpy as np
import pandas as pd
import os
import requests
import copy
from engine.microsim import HouseholdSimulator
from engine.firm_abm import FirmMarket

def sum_nested(d):
    if isinstance(d, (int, float)):
        return d
    total = 0
    for v in d.values():
        total += sum_nested(v)
    return total

def scale_nested(d, factor):
    for k, v in d.items():
        if isinstance(v, dict):
            scale_nested(v, factor)
        else:
            d[k] *= factor

def flatten_dict(d, parent_key='', sep=' > '):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

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
        
        self.dept_to_sector = {
            'The Presidency': 'Government & Social', 'Parliament': 'Government & Social', 'Cooperative Governance': 'Government & Social',
            'Home Affairs': 'Government & Social', 'International Relations': 'Government & Social', 'National Treasury': 'Government & Social',
            'Public Works': 'Construction', 'Basic Education': 'Government & Social', 'Higher Education': 'Government & Social',
            'Health': 'Government & Social', 'Social Development': 'Government & Social', 'Defence': 'Government & Social',
            'Police': 'Government & Social', 'Correctional Services': 'Government & Social', 'Justice': 'Government & Social',
            'Labour': 'Government & Social', 'Agriculture': 'Agriculture', 'Communications': 'Business Services',
            'Public Enterprises': 'Utilities', 'Human Settlements': 'Construction', 'Water and Sanitation': 'Utilities',
            'Science and Tech': 'Business Services', 'Tourism': 'Trade', 'Trade, Industry and Competition': 'Business Services',
            'Trade and Industry': 'Business Services', 'Transport': 'Transport', 'Sport and Culture': 'Government & Social', 
            'Small Business': 'Business Services',
            'Roads & Transport': 'Construction', 'Treasury': 'Government & Social', 'Community Safety': 'Government & Social', 
            'Economic Dev': 'Business Services', 'Cooperative Gov': 'Government & Social', 'Sport & Culture': 'Government & Social',
            'Property Rates': 'Finance', 'Electricity': 'Utilities', 'Water': 'Utilities', 'Sanitation': 'Utilities', 'Refuse': 'Utilities',
            'Fuel Levy': 'Transport', 'Operating Grants & Subsidies': 'Government & Social', 'Other Own Revenue': 'Business Services',
            'Employee Costs': 'Government & Social', 'Bulk Purchases - Electricity': 'Utilities', 'Bulk Purchases - Water': 'Utilities',
            'Contracted Services': 'Business Services', 'Depreciation & Impairment': 'Finance', 'Other Operating Expenses': 'Government & Social'
        }
        
    def simulate_year(self, budgets, base_budgets, levers):
        Y = np.zeros(len(self.sectors))
        
        # 1. National
        for dept, programmes in budgets['national'].items():
            base_progs = base_budgets['national'].get(dept, {})
            delta = sum_nested(programmes) - sum_nested(base_progs)
            sector = self.dept_to_sector.get(dept, 'Government & Social')
            Y[self.sectors.index(sector)] += delta

        # 2. Provincial
        for prov, depts in budgets['provincial'].items():
            for dept, programmes in depts.items():
                base_progs = base_budgets['provincial'].get(prov, {}).get(dept, {})
                delta = sum_nested(programmes) - sum_nested(base_progs)
                sector = self.dept_to_sector.get(dept, 'Government & Social')
                Y[self.sectors.index(sector)] += delta

        # 3. Local
        for category, municipalities in budgets['local'].items():
            for mun, functions in municipalities.items():
                base_funcs = base_budgets['local'].get(category, {}).get(mun, {})
                flat_funcs = flatten_dict(functions)
                flat_base = flatten_dict(base_funcs)
                for func, new_val in flat_funcs.items():
                    delta = new_val - flat_base.get(func, 0)
                    sector = self.dept_to_sector.get(func, 'Utilities')
                    Y[self.sectors.index(sector)] += delta

        # 4. Trade & Industrial
        for sec in ['Agriculture', 'Mining', 'Manufacturing']:
            idx = self.sectors.index(sec)
            Y[idx] += 500000 * (levers['tariff'] / 100) * -1.30
            
        Y = Y * (1 + (levers['markup_cap'] / 100))
        A_modified = self.A * (1 + (levers['localization'] / 100))
        Leontief_modified = np.linalg.inv(self.I - A_modified)
        
        # 5. Tax Drags
        for i, sec in enumerate(self.sectors):
            if sec in ['Trade', 'Services', 'Business Services', 'Transport']:
                Y[i] *= (1 - ((levers['vat'] - 15) / 100 * 0.5) - ((levers['fuel_levy'] - 1.0) * 0.1))
            if sec in ['Finance', 'Manufacturing', 'Construction']:
                Y[i] *= (1 - ((levers['cit'] - 27) / 100 * 0.3) - ((levers['repo_rate'] - 8.25) / 100 * 0.5))
            if sec in ['Trade', 'Services', 'Government & Social']:
                Y[i] *= (1 - ((levers['pit'] - 30) / 100 * 0.4))

        X = Leontief_modified @ Y
        gdp_effect = np.sum(X * self.va)
        
        # 6. ABM
        demand_shocks = {sec: 1.0 + (X[i] / 100000) for i, sec in enumerate(self.sectors)}
        net_job_change = self.firm_market.step(levers['cit'], levers['markup_cap'], levers['repo_rate'], levers['eti'], demand_shocks)
        hhi = self.firm_market.calculate_hhi()
        
        # 7. Revenue
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
        
        # Total base spending (using recursive sum)
        total_base = 0
        for d in base_budgets['national'].values(): total_base += sum_nested(d)
        for p in base_budgets['provincial'].values():
            for d in p.values(): total_base += sum_nested(d)
        for c in base_budgets['local'].values():
            for m in c.values(): total_base += sum_nested(m)
        
        for year in range(1, 6):
            # Proposed spending (using recursive sum)
            total_proposed = 0
            for d in budgets['national'].values(): total_proposed += sum_nested(d)
            for p in budgets['provincial'].values():
                for d in p.values(): total_proposed += sum_nested(d)
            for c in budgets['local'].values():
                for m in c.values(): total_proposed += sum_nested(m)
            
            interest = current_debt * (levers['repo_rate'] / 100) if year > 1 else 0
            
            if total_proposed > (total_base + 50000) and not levers['allow_deficit']:
                scale = (total_base + 50000) / total_proposed
                actual_budgets = copy.deepcopy(budgets)
                for k in actual_budgets['national']: scale_nested(actual_budgets['national'][k], scale)
                for pr in actual_budgets['provincial']:
                    for d in actual_budgets['provincial'][pr]: scale_nested(actual_budgets['provincial'][pr][d], scale)
                for c in actual_budgets['local']:
                    for m in actual_budgets['local'][c]: scale_nested(actual_budgets['local'][c][m], scale)
                total_proposed = total_base + 50000
            else:
                actual_budgets = copy.deepcopy(budgets)
                
            budget_change = total_proposed - total_base
            gdp_effect, revenue, net_job_change, hhi = self.simulate_year(actual_budgets, base_budgets, levers)
            
            net_fiscal = revenue - budget_change - interest
            current_debt -= net_fiscal 
            current_gdp = current_gdp * 1.015 + gdp_effect 
            
            self.microsim.households = self.microsim.apply_policy_shocks(net_job_change, levers['vat'], levers['pit'], levers['grant_uplift'], levers['min_wage'], levers['fuel_levy'])
            micro = self.microsim.get_metrics(self.microsim.households)
            
            history.append({
                "Year": f"Year {year}", "GDP": current_gdp / 1_000_000, "Debt_to_GDP": (current_debt / current_gdp) * 100,
                "Total_Employment": self.firm_market.get_total_employment() * 1000,
                "Net_Fiscal_mn": net_fiscal, "Gini": micro["current_gini"], "Poverty_Rate": micro["current_poverty"], "HHI": hhi
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
