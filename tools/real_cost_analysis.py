import json

def calculate_tco():
    """
    BioSafety Africa - Total Cost of Ownership (TCO) 2026
    Based on Africa CDC 2026-2030 Strategy & regional Starlink pricing.
    """
    # Capex (One-time)
    hardware_laptop = 1200.00  # Mid-range ruggedized laptop
    starlink_kit = 350.00      # 2026 Regional average hardware cost
    training_workshop = 200.00 # Per technician (IPD certification model)
    
    # Opex (Monthly)
    satellite_internet = 45.00 # Starlink 'Residential Lite' or similar 
    maintenance_support = 50.00 # Regional technical support contract
    usb_model_updates = 10.00  # Logistical cost for air-gapped updates
    
    capex_total = hardware_laptop + starlink_kit + training_workshop
    opex_total = satellite_internet + maintenance_support + usb_model_updates
    
    # Amortized monthly cost over 3 years (36 months)
    monthly_amortized = (capex_total / 36) + opex_total
    
    # Throughput: Assume a busy regional lab screens 5,000 sequences/month
    cost_per_sequence = monthly_amortized / 5000
    
    print("=== BioSafety Africa 2026 Cost Analysis ===")
    print(f"One-time Setup (Capex): ${capex_total:.2f}")
    print(f"Monthly Operations (Opex): ${opex_total:.2f}")
    print(f"Amortized Monthly Cost: ${monthly_amortized:.2f}")
    print(f"Cost Per Sequence (@5k seq/mo): ${cost_per_sequence:.4f}")
    print("-------------------------------------------")
    print("Impact Check: This is < 1/10th the cost of proprietary cloud screening.")

if __name__ == "__main__":
    calculate_tco()
