import numpy as np
import pandas as pd
import os
import requests
import copy
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
            'Roads & Transport': 'Construction', 'Treasury': 'Government & Social', 'Community Safety': 'Government & Social', 
            'Economic Dev': 'Business Services', 'Cooperative Gov': 'Government & Social', 'Sport & Culture': 'Government & Social',
            # Municipal Revenue/Expenditure mapping
            'Property Rates': 'Finance', 'Service Charges - Electricity': 'Utilities', 'Service Charges - Water': 'Utilities',
            'Service Charges - Sanitation': 'Utilities', 'Service Charges - Refuse': 'Utilities', 'Fuel Levy': 'Transport',
            'Operating Grants & Subsidies': 'Government & Social', 'Other Own Revenue': 'Business Services',
            'Employee Costs': 'Government & Social', 'Bulk Purchases - Electricity': 'Utilities', 'Bulk Purchases - Water': 'Utilities',
            'Contracted Services': 'Business Services', 'Depreciation & Impairment': 'Finance', 'Other Operating Expenses': 'Government & Social'
        }
        
    def simulate_year(self, budgets, base_budgets, levers):
        Y = np.zeros(len(self.sectors))
        
        # 1. National & Provincial Shocks
        for dept, new_total in budgets['national'].items():
            delta = new_total - base_budgets['national'].get(dept, 0)
            sector = self.dept_to_sector.get(dept, 'Government & Social')
            Y[self.sectors.index(sector)] += delta
            
        for prov, depts in budgets['provincial'].items():
            for dept, new_total in depts.items():
                delta = new_total - base_budgets['provincial'].get(prov, {}).get(dept, 0)
                sector = self.dept_to_sector.get(dept, 'Government & Social')
                Y[self.sectors.index(sector)] += delta

        # 2. Municipal Shocks (Revenue & Expenditure)
        # Municipal spending is a direct demand shock. Municipal revenue collection affects household disposable income.
        for mun, data in budgets['local'].items():
            base_data = base_budgets['local'].get(mun, {})
            # Expenditure shocks
            for item, new_val in data['expenditure'].items():
                delta = new_val - base_data.get('expenditure', {}).get(item, 0)
                sector = self.dept_to_sector.get(item, 'Government & Social')
                Y[self.sectors.index(sector)] += delta
            # Revenue shocks (e.g., if property rates go up, it acts as a tax on Finance/Real Estate)
            for item, new_val in data['revenue'].items():
                delta = new_val - base_data.get('revenue', {}).get(item, 0)
                sector = self.dept_to_sector.get(item, 'Finance')
                Y[self.sectors.index(sector)] -= delta # Revenue collection reduces private demand

        # 3. Tax Drags
        for i, sec in enumerate(self.sectors):
            if sec in ['Trade', 'Services', 'Business Services', 'Transport']:
                Y[i] *= (1 - ((levers['vat'] - 15) / 100 * 0.5) - ((levers['fuel_levy'] - 1.0) * 0.1))
            if sec in ['Finance', 'Manufacturing', 'Construction']:
                Y[i] *= (1 - ((levers['cit'] - 27) / 100 * 0.3) - ((levers['repo_rate'] - 8.25) / 100 * 0.5))
            if sec in ['Trade', 'Services', 'Government & Social']:
                Y[i] *= (1 - ((levers['pit'] - 30) / 100 * 0.4))

        X = self.base_Leontief_inverse @ Y
        gdp_effect = np.sum(X * self.va)
        
        # 4. ABM Step
        demand_shocks = {sec: 1.0 + (X[i] / 100000) for i, sec in enumerate(self.sectors)}
        net_job_change = self.firm_market.step(levers['cit'], levers['markup_cap'], levers['repo_rate'], levers['eti'], demand_shocks)
        hhi = self.firm_market.calculate_hhi()
        
        # 5. Total Revenue Calculation
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
        
        total_base_spend = sum(base_budgets['national'].values())
        for p in base_budgets['provincial'].values(): total_base_spend += sum(p.values())
        for m in base_budgets['local'].values():
            total_base_spend += sum(m['expenditure'].values())
        
        for year in range(1, 6):
            total_proposed = sum(budgets['national'].values())
            for p in budgets['provincial'].values(): total_proposed += sum(p.values())
            for m in budgets['local'].values(): total_proposed += sum(m['expenditure'].values())
            
            interest = current_debt * (levers['repo_rate'] / 100) if year > 1 else 0
            
            if total_proposed > (total_base_spend + 50000) and not levers['allow_deficit']:
                scale = (total_base_spend + 50000) / total_proposed
                actual_budgets = copy.deepcopy(budgets)
                for k in actual_budgets['national']: actual_budgets['national'][k] *= scale
                for p in actual_budgets['provincial']:
                    for k in actual_budgets['provincial'][p]: actual_budgets['provincial'][p][k] *= scale
                for m in actual_budgets['local']:
                    for k in actual_budgets['local'][m]['expenditure']: actual_budgets['local'][m]['expenditure'][k] *= scale
                total_proposed = total_base_spend + 50000
            else:
                actual_budgets = copy.deepcopy(budgets)
                
            budget_change = total_proposed - total_base_spend
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
        # (Same as before, abbreviated for brevity)
        return "AI response placeholder"
