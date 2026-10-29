import numpy as np
import pandas as pd

def find_optimal_policy(twin, base_budgets, envelope, target_poverty, max_debt_gdp):
    """
    Runs a Monte Carlo search to find the optimal policy combination.
    Returns the best tax rates and a multiplier for the budget.
    """
    best_score = float('inf')
    best_params = {}
    
    # We will test 50 different random policy combinations
    for _ in range(50):
        # 1. Randomly sample policy levers within realistic bounds
        vat = np.random.randint(14, 20)
        cit = np.random.randint(20, 35)
        pit = np.random.randint(25, 40)
        
        # Sample budget scaling (e.g., scaling up Public Works vs cutting Education)
        pw_scale = np.random.uniform(0.5, 2.0)
        edu_scale = np.random.uniform(0.8, 1.2)
        
        test_budgets = base_budgets.copy()
        test_budgets['Public Works'] = int(test_budgets['Public Works'] * pw_scale)
        test_budgets['Education'] = int(test_budgets['Education'] * edu_scale)
        
        # Create a static 5-year matrix for this test
        years = [f"Year {i}" for i in range(1, 6)]
        test_df = pd.DataFrame([test_budgets for _ in range(5)], index=years)
        
        # 2. Run the simulation
        result = twin.simulate_5_years(
            test_df, base_budgets, envelope, True, vat, cit, pit, 0, 10, 5, 0
        )
        
        # 3. Score the result (Lower is better)
        final_year = result.iloc[-1]
        poverty = final_year['Poverty_Rate']
        debt = final_year['Debt_to_GDP']
        jobs = final_year['Total_Employment']
        
        # Penalty function
        score = 0
        # Huge penalty if debt is breached
        if debt > max_debt_gdp:
            score += (debt - max_debt_gdp) * 100 
        
        # Penalty for missing the poverty target
        score += abs(poverty - target_poverty) * 10
        
        # Reward job creation (lowers score)
        score -= (jobs / 10000)
        
        if score < best_score:
            best_score = score
            best_params = {
                "vat": vat, "cit": cit, "pit": pit,
                "pw_scale": pw_scale, "edu_scale": edu_scale,
                "resulting_poverty": poverty, "resulting_debt": debt,
                "resulting_jobs": jobs
            }
            
    return best_params
