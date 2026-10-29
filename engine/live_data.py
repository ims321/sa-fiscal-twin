def fetch_live_budgets():
    # National Sphere (R millions)
    national = {
        'The Presidency': 739, 'Parliament': 3068, 'Cooperative Governance': 131129, 'Home Affairs': 11060,
        'International Relations': 7090, 'National Treasury': 29973, 'Public Works': 7648, 'Basic Education': 32000,
        'Higher Education': 16000, 'Health': 62000, 'Social Development': 25000, 'Defence': 57184,
        'Police': 113000, 'Correctional Services': 28000, 'Justice': 25368, 'Labour': 4153,
        'Agriculture': 7610, 'Communications': 2546, 'Public Enterprises': 5000, 'Human Settlements': 34043,
        'Water and Sanitation': 18000, 'Science and Tech': 9000, 'Tourism': 2500, 'Trade and Industry': 10000,
        'Transport': 25000, 'Sport and Culture': 6000, 'Small Business': 6000
    }

    # Provincial Sphere (R millions) - 9 Provinces with 12 standard departments
    prov_depts = ['Health', 'Education', 'Roads & Transport', 'Social Development', 'Agriculture', 'Public Works', 'Treasury', 'Community Safety', 'Human Settlements', 'Sport & Culture', 'Economic Dev', 'Cooperative Gov']
    provinces = ['Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal', 'Limpopo', 'Mpumalanga', 'Northern Cape', 'North West', 'Western Cape']
    provincial = {prov: {dept: 1500 for dept in prov_depts} for prov in provinces}
    # Adjust key baselines to reality
    provincial['Gauteng']['Health'] = 55000; provincial['Gauteng']['Education'] = 60000
    provincial['KwaZulu-Natal']['Health'] = 48000; provincial['KwaZulu-Natal']['Education'] = 58000
    provincial['Western Cape']['Health'] = 28000; provincial['Western Cape']['Education'] = 25000
    provincial['Eastern Cape']['Health'] = 25000; provincial['Eastern Cape']['Education'] = 38000

    # Local Sphere (R millions) - Full MBRR structure for major metros
    # Benchmark: City of Johannesburg 2025/26 (R84.8bn Revenue, R80.7bn Expenditure)
    local = {
        'City of Johannesburg': {
            'revenue': {
                'Property Rates': 18100, 'Service Charges - Electricity': 25600, 'Service Charges - Water': 20000,
                'Service Charges - Sanitation': 3400, 'Service Charges - Refuse': 3300, 'Fuel Levy': 4570,
                'Operating Grants & Subsidies': 8000, 'Other Own Revenue': 1830
            },
            'expenditure': {
                'Employee Costs': 24000, 'Bulk Purchases - Electricity': 16000, 'Bulk Purchases - Water': 7000,
                'Contracted Services': 12000, 'Depreciation & Impairment': 6000, 'Other Operating Expenses': 15700
            }
        },
        'City of Cape Town': {
            'revenue': {
                'Property Rates': 14000, 'Service Charges - Electricity': 12000, 'Service Charges - Water': 4500,
                'Service Charges - Sanitation': 1800, 'Service Charges - Refuse': 2500, 'Fuel Levy': 3000,
                'Operating Grants & Subsidies': 5000, 'Other Own Revenue': 2000
            },
            'expenditure': {
                'Employee Costs': 14000, 'Bulk Purchases - Electricity': 8000, 'Bulk Purchases - Water': 2000,
                'Contracted Services': 8000, 'Depreciation & Impairment': 3000, 'Other Operating Expenses': 10800
            }
        },
        'eThekwini': {
            'revenue': {
                'Property Rates': 8000, 'Service Charges - Electricity': 23300, 'Service Charges - Water': 1150,
                'Service Charges - Sanitation': 1200, 'Service Charges - Refuse': 2000, 'Fuel Levy': 2200,
                'Operating Grants & Subsidies': 4000, 'Other Own Revenue': 1500
            },
            'expenditure': {
                'Employee Costs': 12000, 'Bulk Purchases - Electricity': 14000, 'Bulk Purchases - Water': 1000,
                'Contracted Services': 6000, 'Depreciation & Impairment': 2500, 'Other Operating Expenses': 7850
            }
        }
    }

    return {"national": national, "provincial": provincial, "local": local}
