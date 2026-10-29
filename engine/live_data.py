def fetch_live_budgets():
    """Returns a comprehensive dictionary of baseline budgets for all three spheres."""
    
    # 1. National Sphere (R millions)
    national = {
        'The Presidency': 739, 'Parliament': 3067, 'Cooperative Governance': 131129, 'Home Affairs': 11060,
        'International Relations': 7090, 'National Treasury': 29972, 'Public Works': 7647, 'Basic Education': 32000,
        'Higher Education': 16000, 'Health': 62000, 'Social Development': 25000, 'Defence': 57184,
        'Police': 113000, 'Correctional Services': 28000, 'Justice': 25368, 'Labour': 4153,
        'Agriculture': 7610, 'Communications': 2546, 'Public Enterprises': 5000, 'Human Settlements': 34043,
        'Water and Sanitation': 18000, 'Science and Tech': 9000, 'Tourism': 2500, 'Trade and Industry': 10000,
        'Transport': 25000, 'Sport and Culture': 6000, 'Small Business': 6000
    }

    # 2. Provincial Sphere (R millions) - All 9 Provinces with standard departments
    provincial = {
        'Eastern Cape': {'Health': 25000, 'Education': 38000, 'Roads': 4000, 'Social Dev': 2500, 'Agriculture': 1500},
        'Free State': {'Health': 12000, 'Education': 15000, 'Roads': 2500, 'Social Dev': 1200, 'Agriculture': 800},
        'Gauteng': {'Health': 55000, 'Education': 60000, 'Roads': 6000, 'Social Dev': 5000, 'Agriculture': 1000},
        'KwaZulu-Natal': {'Health': 48000, 'Education': 58000, 'Roads': 5500, 'Social Dev': 4500, 'Agriculture': 2000},
        'Limpopo': {'Health': 22000, 'Education': 35000, 'Roads': 3500, 'Social Dev': 2200, 'Agriculture': 1500},
        'Mpumalanga': {'Health': 15000, 'Education': 22000, 'Roads': 3000, 'Social Dev': 1800, 'Agriculture': 1200},
        'Northern Cape': {'Health': 5000, 'Education': 7000, 'Roads': 1500, 'Social Dev': 800, 'Agriculture': 600},
        'North West': {'Health': 14000, 'Education': 18000, 'Roads': 2800, 'Social Dev': 1500, 'Agriculture': 1000},
        'Western Cape': {'Health': 28000, 'Education': 25000, 'Roads': 4500, 'Social Dev': 3000, 'Agriculture': 2000}
    }

    # 3. Local Sphere (R millions) - Aggregated by standard municipal functions
    # This represents the consolidated budgets of all 257 municipalities.
    local = {
        'Water': 45000,
        'Electricity': 55000,
        'Roads & Transport': 20000,
        'Waste Management': 12000,
        'Community & Public Safety': 18000,
        'Health & Environmental': 8000,
        'Housing & Planning': 15000
    }

    return {"national": national, "provincial": provincial, "local": local}
