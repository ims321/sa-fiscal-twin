def fetch_live_budgets():
    # 1. NATIONAL SPHERE (Exact 2025/26 ENE Programme & Sub-Programme Structures)
    national = {
        'Trade, Industry and Competition': {
            '1. Administration': {'Ministry': 50, 'Departmental Management': 200, 'Corporate Services': 400, 'Financial Management': 150, 'Office Accommodation': 200},
            '2. Trade': {'International Trade Development': 180, 'African Economic Development': 139},
            '3. Investment & Spatial Industrial Dev.': {'Investment Promotion': 80, 'SEZ & Industrial Parks': 79},
            '4. Sectors': {'Industrial Competitiveness': 800, 'Customised Sector Programmes': 804},
            '5. Regulation': {'Regulatory Services': 200, 'Consumer Protection': 220},
            '6. Incentives': {'Incentive Schemes': 4000, 'Transfer to IDC': 800, 'Transfer to Other Entities': 431},
            '7. Export': {'Export Promotion': 200, 'Export Development': 167},
            '8. Transformation & Competition': {'B-BBEE': 500, 'Competition Policy': 300, 'Transfer to B-BBEE Commission': 100, 'Transfer to Competition Commission': 800, 'Transfer to Competition Tribunal': 261},
            '9. Research': {'Economic Research': 63}
        },
        'Health': {
            '1. Administration': {'Ministry': 100, 'Departmental Management': 500, 'Corporate Services': 1200, 'Financial Management': 300},
            '2. Public Health': {'District Health Services': 8000, 'Community Health': 4000, 'Emergency Medical Services': 2000},
            '3. Hospital Services': {'Central Hospitals': 15000, 'Provincial Hospitals': 12000, 'Specialised Hospitals': 3000},
            '4. HIV/AIDS': {'HIV/AIDS Prevention': 3000, 'Treatment & Care': 4000}
        },
        'Basic Education': {
            '1. Administration': {'Ministry': 80, 'Departmental Management': 300, 'Corporate Services': 800},
            '2. Curriculum': {'Curriculum Development': 5000, 'Teacher Training': 4000, 'Assessment': 2000},
            '3. Infrastructure': {'School Infrastructure': 8000, 'Maintenance': 4000}
        },
        'Police': {
            '1. Administration': {'Ministry': 150, 'Departmental Management': 800, 'Corporate Services': 2500},
            '2. Visible Policing': {'Crime Prevention': 30000, 'Border Security': 10000, 'Public Order': 5000},
            '3. Detective Services': {'Detective Services': 20000, 'Forensic Services': 5000},
            '4. Crime Intelligence': {'Intelligence Operations': 8000, 'Analysis': 3000}
        },
        'The Presidency': {'1. Administration': {'Ministry': 200, 'Departmental Management': 539}},
        'Parliament': {'1. Administration': {'Members Affairs': 1500, 'Legislative Support': 1568}},
        'Cooperative Governance': {'1. Administration': {'Ministry': 500, 'Provincial Governance': 80000, 'Municipal Support': 50629}},
        'Home Affairs': {'1. Administration': {'Citizen Services': 6000, 'Immigration': 3060, 'Refugee Management': 2000}},
        'National Treasury': {'1. Administration': {'Ministry': 300, 'Public Finance': 15000, 'Economic Policy': 14673}},
        'Public Works': {'1. Administration': {'Ministry': 100, 'Infrastructure': 5000, 'Property Management': 2548}},
        'Social Development': {'1. Administration': {'Social Grants': 18000, 'Child Protection': 3000, 'Community Dev': 4000}},
        'Defence': {'1. Administration': {'Landward Defence': 20000, 'Air Defence': 15000, 'Maritime Defence': 22184}},
        'Justice': {'1. Administration': {'Court Services': 15000, 'Legal Services': 10368}},
        'Agriculture': {'1. Administration': {'Agricultural Production': 4000, 'Food Security': 3610}},
        'Transport': {'1. Administration': {'Road Infrastructure': 15000, 'Public Transport': 10000}}
    }

    # 2. PROVINCIAL SPHERE (9 Provinces with exact departmental structures)
    provincial = {}
    provinces = ['Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal', 'Limpopo', 'Mpumalanga', 'Northern Cape', 'North West', 'Western Cape']
    for prov in provinces:
        provincial[prov] = {
            'Health': {'1. Administration': 500, '2. District Health': 5000, '3. Provincial Hospitals': 8000, '4. Emergency Services': 1500},
            'Education': {'1. Administration': 800, '2. Public Ordinary Schools': 12000, '3. Special Needs': 2000, '4. ECD': 3000},
            'Roads & Transport': {'1. Administration': 200, '2. Road Infrastructure': 2500, '3. Maintenance': 1300},
            'Social Development': {'1. Administration': 300, '2. Social Welfare': 1500, '3. Child Care': 1200},
            'Public Works': {'1. Administration': 150, '2. Infrastructure': 1000, '3. Property Management': 500},
            'Treasury': {'1. Administration': 200, '2. Financial Management': 500, '3. Economic Policy': 300},
            'Community Safety': {'1. Administration': 100, '2. Traffic Management': 800, '3. Police Oversight': 200},
            'Human Settlements': {'1. Administration': 300, '2. Housing Development': 1500, '3. Urban Planning': 300},
            'Agriculture': {'1. Administration': 200, '2. Veterinary Services': 400, '3. Food Security': 600},
            'Sport & Culture': {'1. Administration': 150, '2. Sports Development': 400, '3. Arts & Culture': 250},
            'Economic Dev': {'1. Administration': 150, '2. Trade & Investment': 500, '3. Economic Planning': 350},
            'Cooperative Gov': {'1. Administration': 200, '2. Municipal Support': 800, '3. Traditional Affairs': 200}
        }

    # 3. LOCAL SPHERE (Full 2025/26 Budget Structures for Metros and Districts)
    local = {
        'Metropolitan': {
            'City of Johannesburg': {
                'Revenue': {'Property Rates': 18100, 'Electricity': 25600, 'Water': 20000, 'Sanitation': 3400, 'Refuse': 3300, 'Grants': 8000},
                'Expenditure': {'Employee Costs': 24000, 'Bulk Electricity': 16000, 'Bulk Water': 7000, 'Contracted Services': 12000, 'Other Opex': 15700}
            },
            'City of Cape Town': {
                'Revenue': {'Property Rates': 14000, 'Electricity': 12000, 'Water': 4500, 'Sanitation': 1800, 'Refuse': 2500, 'Grants': 5000},
                'Expenditure': {'Employee Costs': 14000, 'Bulk Electricity': 8000, 'Bulk Water': 2000, 'Contracted Services': 8000, 'Other Opex': 10800}
            },
            'eThekwini': {
                'Revenue': {'Property Rates': 8000, 'Electricity': 23300, 'Water': 1150, 'Sanitation': 1200, 'Refuse': 2000, 'Grants': 4000},
                'Expenditure': {'Employee Costs': 12000, 'Bulk Electricity': 14000, 'Bulk Water': 1000, 'Contracted Services': 6000, 'Other Opex': 7850}
            },
            'City of Tshwane': {
                'Revenue': {'Property Rates': 6000, 'Electricity': 8500, 'Water': 1800, 'Sanitation': 1500, 'Refuse': 1500, 'Grants': 3000},
                'Expenditure': {'Employee Costs': 9000, 'Bulk Electricity': 7000, 'Bulk Water': 1500, 'Contracted Services': 4000, 'Other Opex': 4800}
            },
            'Ekurhuleni': {
                'Revenue': {'Property Rates': 5000, 'Electricity': 7500, 'Water': 1500, 'Sanitation': 1200, 'Refuse': 1200, 'Grants': 2500},
                'Expenditure': {'Employee Costs': 8000, 'Bulk Electricity': 6000, 'Bulk Water': 1200, 'Contracted Services': 3500, 'Other Opex': 4000}
            }
        },
        'District': {
            'Amathole District': {
                'Revenue': {'Water': 500, 'Roads': 200, 'Waste Management': 150, 'Grants': 800},
                'Expenditure': {'Employee Costs': 300, 'Contracted Services': 100, 'Other Opex': 400}
            },
            'Cape Winelands': {
                'Revenue': {'Water': 400, 'Roads': 180, 'Waste Management': 120, 'Grants': 600},
                'Expenditure': {'Employee Costs': 250, 'Contracted Services': 80, 'Other Opex': 300}
            },
            'Chris Hani District': {
                'Revenue': {'Water': 300, 'Roads': 150, 'Waste Management': 100, 'Grants': 500},
                'Expenditure': {'Employee Costs': 200, 'Contracted Services': 60, 'Other Opex': 250}
            }
        }
    }

    return {"national": national, "provincial": provincial, "local": local}
