from engine.treasury_data import fetch_treasury_data

def fetch_live_budgets():
    """
    Returns the full Treasury data structure.
    Falls back to a minimal hardcoded structure if the pipeline fails.
    """
    try:
        return fetch_treasury_data()
    except Exception as e:
        print(f"Treasury pipeline failed: {e}. Using fallback.")
        # Minimal fallback to keep the app running
        return {
            "national": {
                "Trade, Industry and Competition": {
                    "1. Administration": 1000.6,
                    "2. Trade": 319.2,
                    "6. Incentives": 5231.7
                },
                "Health": {"1. Administration": 5000, "2. Public Health": 20000}
            },
            "provincial": {
                "Gauteng": {"Health": {"1. Administration": 500, "2. District Health": 5000}}
            },
            "local": {
                "Metropolitan": {
                    "City of Johannesburg": {"Property Rates": 18100, "Electricity": 25600}
                }
            }
        }
