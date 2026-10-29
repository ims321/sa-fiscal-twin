import numpy as np
import pandas as pd

class HouseholdSimulator:
    def __init__(self, num_households=10000):
        self.n = num_households
        np.random.seed(42)
        
        sigma = 1.2
        mu = np.log(120000) - (sigma**2)/2
        base_incomes = np.random.lognormal(mean=mu, sigma=sigma, size=self.n)
        
        self.households = pd.DataFrame({
            'household_id': range(self.n),
            'base_income': base_incomes,
            'current_income': base_incomes.copy(),
            'employed': np.random.choice([True, False], size=self.n, p=[0.65, 0.35])
        })
        
        # Set unemployed income to 0
        self.households.loc[~self.households['employed'], 'current_income'] = 0
        
        self.poverty_line = 12000

    def calculate_gini(self, incomes):
        sorted_income = np.sort(incomes)
        n = len(sorted_income)
        index = np.arange(1, n + 1)
        # Handle the case where everyone has 0 income
        if np.sum(sorted_income) == 0: return 1.0
        return (np.sum((2 * index - n - 1) * sorted_income)) / (n * np.sum(sorted_income))

    def apply_policy_shocks(self, net_job_change, vat_change, pit_change):
        df = self.households.copy()
        
        # 1. Hire or Fire based on net_job_change
        if net_job_change > 0:
            unemployed_ids = df[df['employed'] == False].index
            num_to_hire = min(int(net_job_change), len(unemployed_ids))
            if num_to_hire > 0:
                hired_ids = np.random.choice(unemployed_ids, size=num_to_hire, replace=False)
                df.loc[hired_ids, 'employed'] = True
                df.loc[hired_ids, 'current_income'] = np.random.normal(120000, 20000, size=num_to_hire)
                
        elif net_job_change < 0:
            employed_ids = df[df['employed'] == True].index
            num_to_fire = min(int(abs(net_job_change)), len(employed_ids))
            if num_to_fire > 0:
                fired_ids = np.random.choice(employed_ids, size=num_to_fire, replace=False)
                df.loc[fired_ids, 'employed'] = False
                df.loc[fired_ids, 'current_income'] = 0

        # 2. PIT (Income Tax)
        pit_effect = 1 - ((pit_change - 30) / 100)
        df['current_income'] = df['current_income'] * pit_effect
        
        # 3. VAT (Consumption Tax) - Only hurts those with income
        vat_effect = 1 - ((vat_change - 15) / 100 * 0.6)
        df['current_income'] = df['current_income'] * vat_effect
        
        return df

    def get_metrics(self, df):
        current_gini = self.calculate_gini(df['current_income'])
        current_poverty = (df['current_income'] < self.poverty_line).mean() * 100
        
        return {
            "current_gini": current_gini,
            "current_poverty": current_poverty
        }
