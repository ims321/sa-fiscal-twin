import numpy as np
import pandas as pd

class Firm:
    def __init__(self, firm_id, sector, productivity, market_share):
        self.id = firm_id
        self.sector = sector
        self.productivity = productivity
        self.market_share = market_share
        self.active = True
        
        # Scale employment so the sum matches our microsim (~6500 employed households)
        # 500 firms * ~13 employees = 6500
        self.employees = max(1, int(np.random.normal(13, 3)))
        
    def to_dict(self):
        return {
            "id": self.id, "sector": self.sector, "active": self.active,
            "market_share": self.market_share, "employees": self.employees,
            "productivity": self.productivity
        }

class FirmMarket:
    def __init__(self, num_firms=500):
        self.sectors = ['Agriculture', 'Mining', 'Manufacturing', 'Utilities', 'Construction', 
                        'Trade', 'Transport', 'Finance', 'Business Services', 'Government & Social']
        self.firms = []
        self.next_id = 0
        
        for _ in range(num_firms):
            sector = np.random.choice(self.sectors)
            productivity = np.random.normal(1.0, 0.15)
            market_share = np.random.uniform(0.005, 0.05)
            self.firms.append(Firm(self.next_id, sector, productivity, market_share))
            self.next_id += 1

    def get_total_employment(self):
        return sum(f.employees for f in self.firms if f.active)

    def calculate_hhi(self):
        active_firms = [f for f in self.firms if f.active]
        if not active_firms:
            return 0
        total_share = sum(f.market_share for f in active_firms)
        hhi = sum(((f.market_share / total_share) * 100)**2 for f in active_firms)
        return hhi

    def step(self, cit_rate, markup_reduction, macro_demand_shocks):
        """Simulate one year of firm dynamics. Returns net job change."""
        prev_employment = self.get_total_employment()
        new_firms = []
        
        for f in self.firms:
            if not f.active:
                continue
                
            base_profit = f.productivity * f.market_share * 100
            tax_drag = 1 - ((cit_rate - 27) / 100)
            markup_drag = 1 - (markup_reduction / 100)
            demand_boost = macro_demand_shocks.get(f.sector, 1.0)
            
            profit = base_profit * tax_drag * markup_drag * demand_boost
            
            # Bankruptcy: Firm dies, employees are fired
            if profit < 1.5:
                f.active = False
                
            # Growth: Firm hires new workers
            elif profit > 5.0:
                f.employees += int(profit // 2)
                f.market_share += 0.001
                
            # Entrants
            if markup_reduction > 5 and np.random.rand() < 0.1:
                sector = np.random.choice(self.sectors)
                new_f = Firm(self.next_id, sector, np.random.normal(1.05, 0.1), 0.01)
                new_f.employees = 2 # Start small
                new_firms.append(new_f)
                self.next_id += 1
                
        self.firms.extend(new_firms)
        
        current_employment = self.get_total_employment()
        net_job_change = current_employment - prev_employment
        
        return net_job_change
