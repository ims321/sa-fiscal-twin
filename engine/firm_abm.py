import numpy as np
import pandas as pd

class Firm:
    def __init__(self, firm_id, sector, productivity, market_share):
        self.id = firm_id
        self.sector = sector
        self.productivity = productivity # > 1.0 is highly efficient
        self.market_share = market_share
        self.active = True
        self.employees = max(10, int(market_share * 5000))
        
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
        
        # Initialize firms with random productivity and market share
        for _ in range(num_firms):
            sector = np.random.choice(self.sectors)
            productivity = np.random.normal(1.0, 0.15) # Mean 1.0, some are very good
            market_share = np.random.uniform(0.005, 0.05)
            self.firms.append(Firm(self.next_id, sector, productivity, market_share))
            self.next_id += 1

    def calculate_hhi(self):
        """Herfindahl-Hirschman Index: Measures market concentration. <1500 is competitive, >2500 is monopoly."""
        active_firms = [f for f in self.firms if f.active]
        if not active_firms:
            return 0
        total_share = sum(f.market_share for f in active_firms)
        hhi = sum(((f.market_share / total_share) * 100)**2 for f in active_firms)
        return hhi

    def step(self, cit_rate, markup_reduction, macro_demand_shocks):
        """Simulate one year of firm dynamics."""
        new_firms = []
        
        for f in self.firms:
            if not f.active:
                continue
                
            # 1. Calculate Profitability
            # Base profit depends on productivity and market share
            base_profit = f.productivity * f.market_share * 100
            
            # Corporate tax drag
            tax_drag = 1 - ((cit_rate - 27) / 100)
            
            # Competition drag (lower markups mean lower profit per unit)
            markup_drag = 1 - (markup_reduction / 100)
            
            # Macro demand shock (e.g., if construction spending goes up)
            demand_boost = macro_demand_shocks.get(f.sector, 1.0)
            
            profit = base_profit * tax_drag * markup_drag * demand_boost
            
            # 2. Firm Death (Bankruptcy)
            # If profit falls below a survival threshold, they close down.
            if profit < 1.5:
                f.active = False
                
            # 3. Firm Growth (Hiring & Market Share)
            elif profit > 5.0:
                f.employees += int(profit // 2)
                f.market_share += 0.001 # Steal market share
                
            # 4. Entrants (New firms entering the market)
            # If markups are reduced (pro-competition) or demand is high, new firms enter.
            if markup_reduction > 5 and np.random.rand() < 0.1:
                sector = np.random.choice(self.sectors)
                new_f = Firm(self.next_id, sector, np.random.normal(1.05, 0.1), 0.01)
                new_firms.append(new_f)
                self.next_id += 1
                
        self.firms.extend(new_firms)
        
        # Return dataframe for visualization
        return pd.DataFrame([f.to_dict() for f in self.firms if f.active])
