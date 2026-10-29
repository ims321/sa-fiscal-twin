import pandas as pd
import numpy as np

# 10 aggregate sectors
SECTOR_MAP = {
    'Agriculture': ['Agriculture', 'Forestry', 'Fishing'],
    'Mining': ['Mining of coal', 'Mining of gold', 'Mining of other'],
    'Manufacturing': ['Manufacturing of food', 'Manufacturing of textiles', 'Manufacturing of petroleum', 
                      'Manufacturing of chemicals', 'Manufacturing of metals', 'Manufacturing of machinery',
                      'Manufacturing of transport', 'Manufacturing of furniture', 'Other manufacturing'],
    'Utilities': ['Electricity', 'Gas', 'Water'],
    'Construction': ['Construction'],
    'Trade': ['Wholesale', 'Retail', 'Motor trade'],
    'Transport': ['Land transport', 'Water transport', 'Air transport', 'Transport support'],
    'Finance': ['Financial services', 'Insurance', 'Real estate'],
    'Business Services': ['Professional services', 'Administrative services'],
    'Government & Social': ['Public administration', 'Education', 'Health', 'Social work']
}

def load_and_aggregate_sam(path="data/sam_2019.xlsx"):
    print("Loading SAM...")
    # 1. Dynamically find the header row (looks for the row containing 'Ind')
    raw = pd.read_excel(path, sheet_name="SASAM 2019 61Ind 4Educ", header=None)
    header_idx = 0
    for i in range(10):
        row_vals = [str(x).lower() for x in raw.iloc[i].dropna()]
        if any('ind' in s for s in row_vals):
            header_idx = i
            break
            
    df = pd.read_excel(path, sheet_name="SASAM 2019 61Ind 4Educ", skiprows=header_idx, index_col=0)
    df.columns = [str(c).strip() for c in df.columns]
    df.index = [str(i).strip() for i in df.index]
    
    # 2. Identify industry columns (starts with 'Ind')
    industry_cols = [c for c in df.columns if c.startswith('Ind') or c.startswith('IND')]
    
    # 3. Dynamically find the 'Total' column
    total_col = None
    for c in df.columns:
        if 'total' in c.lower():
            total_col = c
            break
    if not total_col:
        total_col = df.columns[-1] # Fallback to the last column
        
    use_table = df.loc[df.index.isin(industry_cols), industry_cols].copy()
    use_table = use_table.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    total_output = df.loc[df.index.isin(industry_cols), total_col].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # 4. Aggregate to 10 sectors
    agg_use = pd.DataFrame(0.0, index=SECTOR_MAP.keys(), columns=SECTOR_MAP.keys())
    agg_output = pd.Series(0.0, index=SECTOR_MAP.keys())
    
    for agg_name, sub_sectors in SECTOR_MAP.items():
        # Match sub-sectors flexibly
        matching = [c for c in industry_cols if any(sub.lower() in str(c).lower() for sub in sub_sectors)]
        if not matching:
            matching = [i for i in df.index if any(sub.lower() in str(i).lower() for sub in sub_sectors)]
            
        if matching:
            valid_cols = [m for m in matching if m in use_table.columns]
            valid_rows = [m for m in matching if m in use_table.index]
            
            if valid_cols:
                # Sum columns
                agg_use.loc[agg_name] = use_table.loc[valid_rows, valid_cols].sum(axis=0).values
            if valid_rows:
                agg_output[agg_name] = total_output.loc[valid_rows].sum()
    
    A = agg_use.div(agg_output, axis=1).fillna(0)
    va_ratio = 1 - A.sum(axis=0)
    va_ratio = va_ratio.clip(0, 1)
    
    print("Aggregation complete.")
    return A, va_ratio, agg_output

if __name__ == "__main__":
    A, va, output = load_and_aggregate_sam()
    print("\nA Matrix (Input Coefficients):")
    print(A.round(3))
