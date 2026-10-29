import numpy as np
import pandas as pd

class Firm:
    def __init__(self, firm_id, sector, productivity, market_share):
        self.id = firm_id
        self.sector = sector
        self.productivity = productivity
        self.market_share = market_share
        self.active = True
        self.employees = max(1, int(np.random.normal(13, 3)))
        
    def to_dict(self):
        return {"id": self.id, "sector": self.sector, "active": self.active, "market_share": self.market_share, "employees": self.employees, "productivity": self.productivity}

class FirmMarket:
    def __init__(self, num_firms=500):
        self.sectors = ['Agriculture', 'Mining', 'Manufacturing', 'Utilities', 'Construction', 'Trade', 'Transport', 'Finance', 'Business Services', 'Government & Social']
        self.firms = []
        self.next_id = 0
        for _ in range(num_firms):
            sector = np.random.choice(self.sectors)
            self.firms.append(Firm(self.next_id, sector, np.random.normal(1.0, 0.15), np.random.uniform(0.005, 0.05)))
            self.next_id += 1

    def get_total_employment(self):
        return sum(f.employees for f in self.firms if f.active)

    def calculate_hhi(self):
        active = [f for f in self.firms if f.active]
        if not active: return 0
        total = sum(f.market_share for f in active)
        return sum(((f.market_share / total) * 100)**2 for f in active)

    def step(self, cit, markup_cap, repo_rate, eti, macro_shocks):
        prev_emp = self.get_total_employment()
        new_firms = []
        
        for f in self.firms:
            if not f.active: continue
            
            base_profit = f.productivity * f.market_share * 100
            tax_drag = 1 - ((cit - 27) / 100)
            # Markup cap limits profit margins
            markup_drag = 1 - ((markup_cap) / 100)
            # Higher repo rate increases borrowing costs, reducing profit
            interest_drag = 1 - ((repo_rate - 8.25) / 100 * 0.5)
            # ETI reduces the cost of hiring (boosts profit)
            eti_boost = 1 + (eti / 100)
            
            demand = macro_shocks.get(f.sector, 1.0)
            profit = base_profit * tax_drag * markup_drag * interest_drag * eti_boost * demand
            
            if profit < 1.5:
                f.active = False
            elif profit > 5.0:
                # If ETI is active, they hire more aggressively
                hire_rate = 1.5 if eti > 10 else 1.0
                f.employees += int((profit // 2) * hire_rate)
                f.market_share += 0.001
                
            if markup_cap > 5 and np.random.rand() < 0.1:
                new_f = Firm(self.next_id, np.random.choice(self.sectors), np.random.normal(1.05, 0.1), 0.01)
                new_f.employees = 2
                new_firms.append(new_f)
                self.next_id += 1
                
        self.firms.extend(new_firms)
        return self.get_total_employment() - prev_emp
