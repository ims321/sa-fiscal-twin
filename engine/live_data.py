def fetch_live_budgets():
    """Returns a dictionary of baseline budgets across all three spheres of government."""
    # 1. National Sphere (R millions)
    national = {
        'The Presidency': 739, 'Parliament': 3067, 'Cooperative Governance': 131129, 'Home Affairs': 11060,
        'International Relations': 7090, 'National Treasury': 29972, 'Public Works': 7647, 'Basic Education': 32000,
        'Higher Education': 16000, 'Health': 62000, 'Social Development': 25000, 'Defence': 57184,
        'Police': 113000, 'Correctional Services': 28000, 'Justice': 25368, 'Labour': 3500,
        'Agriculture': 7610, 'Communications': 2546, 'Public Enterprises': 5000, 'Human Settlements': 34043,
        'Water and Sanitation': 18000, 'Science and Tech': 9000, 'Tourism': 2500, 'Trade and Industry': 10000,
        'Transport': 25000, 'Sport and Culture': 6000, 'Small Business': 6000
    }

    # 2. Provincial Sphere (R millions) - Aggregated across 9 provinces
    provincial = {
        'Provincial Health': 280000,
        'Provincial Education': 310000,
        'Provincial Roads': 30000,
        'Provincial Social Dev': 15000
    }

    # 3. Local Sphere (R millions) - Aggregated across 8 major metros
    local = {
        'Metro Water': 35000,
        'Metro Electricity': 45000,
        'Metro Roads': 15000,
        'Metro Waste': 10000
    }

    return {"national": national, "provincial": provincial, "local": local}
