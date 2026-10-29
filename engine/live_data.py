def fetch_live_budgets():
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

    # 2. Provincial Sphere - 12 Departments per Province
    prov_depts = ['Health', 'Education', 'Roads & Transport', 'Social Development', 'Agriculture', 'Public Works', 'Treasury', 'Community Safety', 'Human Settlements', 'Sport & Culture', 'Economic Dev', 'Cooperative Gov']
    provinces = ['Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal', 'Limpopo', 'Mpumalanga', 'Northern Cape', 'North West', 'Western Cape']
    
    provincial = {prov: {dept: 1500 for dept in prov_depts} for prov in provinces}
    # Adjust baselines roughly to reality
    provincial['Gauteng']['Health'] = 55000; provincial['Gauteng']['Education'] = 60000
    provincial['KwaZulu-Natal']['Health'] = 48000; provincial['KwaZulu-Natal']['Education'] = 58000
    provincial['Western Cape']['Health'] = 28000; provincial['Western Cape']['Education'] = 25000
    provincial['Eastern Cape']['Health'] = 25000; provincial['Eastern Cape']['Education'] = 38000

    # 3. Local Sphere - Metros & District Municipalities
    mun_depts = ['Water', 'Electricity', 'Roads & Stormwater', 'Waste Management', 'Community Safety', 'Housing & Planning']
    municipalities = {
        'City of Johannesburg': {dept: 3500 for dept in mun_depts},
        'City of Cape Town': {dept: 3000 for dept in mun_depts},
        'eThekwini': {dept: 2800 for dept in mun_depts},
        'City of Tshwane': {dept: 2500 for dept in mun_depts},
        'Ekurhuleni': {dept: 2200 for dept in mun_depts},
        'Nelson Mandela Bay': {dept: 1500 for dept in mun_depts},
        'Buffalo City': {dept: 1200 for dept in mun_depts},
        'Mangaung': {dept: 1100 for dept in mun_depts},
        'Amathole District': {dept: 800 for dept in mun_depts},
        'Cape Winelands': {dept: 700 for dept in mun_depts}
        # In a production environment, we would add the remaining 247 municipalities here
    }

    return {"national": national, "provincial": provincial, "local": municipalities}
