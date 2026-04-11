#!/usr/bin/env python3
"""
Test the enhanced security engine with realistic scenarios
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.enhanced_security import EnhancedSecurityEngine

def test_security_engine():
    engine = EnhancedSecurityEngine()
    
    print("=== ENHANCED SECURITY TEST ===")
    
    # Test 1: Clean sequence (should be low risk)
    clean_seq = "ATGAAACCGTACGGTAAACTGCCCACCTATTGCGGCCTGAAA"
    result1 = engine.detect_assembly_scars(clean_seq)
    print(f"Clean sequence risk score: {result1['risk_score']}")
    
    # Test 2: Suspicious sequence with BsaI sites
    suspicious_seq = "ATGAGCTCGGTCTCAAAGACCTGAAATTTGAGACCAAACTG"
    result2 = engine.detect_assembly_scars(suspicious_seq)
    print(f"Suspicious sequence risk score: {result2['risk_score']}")
    print(f"Enzyme sites found: {len(result2['enzyme_sites'])}")
    
    # Test 3: Fragment assembly risk
    fragments = [
        "ATGGGTCTCAAAGAC",  # Contains BsaI
        "GCTCTTCAAACTG",    # Contains SapI  
        "GAAGACCTGAAA" * 50  # Long fragment
    ]
    result3 = engine.check_fragment_assembly_risk(fragments)
    print(f"Fragment assembly risk: {result3['risk_level']}")
    
    print("\n=== AFRICAN REGULATORY INTEGRATION ===")
    from src.enhanced_security import integrate_african_frameworks
    frameworks = integrate_african_frameworks()
    for country, protocol in frameworks.items():
        print(f"{country}: {protocol}")

if __name__ == "__main__":
    test_security_engine()
