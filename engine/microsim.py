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
        self.households.loc[~self.households['employed'], 'current_income'] = 0
        self.poverty_line = 12000

    def calculate_gini(self, incomes):
        sorted_income = np.sort(incomes)
        n = len(sorted_income)
        index = np.arange(1, n + 1)
        if np.sum(sorted_income) == 0: return 1.0
        return (np.sum((2 * index - n - 1) * sorted_income)) / (n * np.sum(sorted_income))

    def apply_policy_shocks(self, net_job_change, vat, pit, grant_uplift, min_wage, fuel_levy):
        df = self.households.copy()
        
        # 1. Hire/Fire
        if net_job_change > 0:
            unemployed = df[df['employed'] == False].index
            hired = np.random.choice(unemployed, size=min(int(net_job_change), len(unemployed)), replace=False)
            df.loc[hired, 'employed'] = True
            df.loc[hired, 'current_income'] = np.random.normal(120000, 20000, size=len(hired))
        elif net_job_change < 0:
            employed = df[df['employed'] == True].index
            fired = np.random.choice(employed, size=min(int(abs(net_job_change)), len(employed)), replace=False)
            df.loc[fired, 'employed'] = False
            df.loc[fired, 'current_income'] = 0

        # 2. Minimum Wage (Boosts the bottom 20% of earners)
        if min_wage > 1.0:
            low_income_mask = (df['current_income'] > 0) & (df['current_income'] < 60000)
            df.loc[low_income_mask, 'current_income'] *= min_wage

        # 3. Direct Taxes (PIT)
        df['current_income'] *= (1 - ((pit - 30) / 100))
        
        # 4. Indirect Taxes & Fuel Levy (Regressive - hits everyone)
        indirect_drag = 1 - ((vat - 15) / 100 * 0.4) - ((fuel_levy - 1.0) * 0.05)
        df['current_income'] *= indirect_drag
        
        # 5. Social Grants (Direct transfer to the poorest 30%)
        # Grant uplift multiplies the baseline transfer value
        if grant_uplift > 1.0:
            poorest_mask = df['base_income'] < 40000
            grant_amount = 24000 * (grant_uplift - 1.0) # Additional grant money
            df.loc[poorest_mask, 'current_income'] += grant_amount

        return df

    def get_metrics(self, df):
        return {
            "current_gini": self.calculate_gini(df['current_income']),
            "current_poverty": (df['current_income'] < self.poverty_line).mean() * 100
        }
