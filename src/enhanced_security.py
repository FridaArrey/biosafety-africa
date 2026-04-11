"""
BioSafety Africa - Enhanced Security Beyond Simple Regex
Multi-layered detection system for sophisticated bypass attempts
"""
import re
from typing import List, Dict

class EnhancedSecurityEngine:
    """
    Expanded security beyond simple BsaI/BsmBI detection
    """
    
    def __init__(self):
        # Multi-enzyme detection (not just BsaI/BsmBI)
        self.restriction_enzymes = {
            'BsaI': ['GGTCTC', 'GAGACC'],
            'BsmBI': ['CGTCTC', 'GAGACG'], 
            'BbsI': ['GAAGAC', 'GTCTTC'],
            'Esp3I': ['CGTCTC', 'GAGACG'],
            'SapI': ['GCTCTTC', 'GAAGAGC'],
            # Add more Type IIS enzymes used in Golden Gate
        }
        
        self.suspicious_patterns = [
            r'ATGAGCTC.{20,200}GAAGAC',  # Start codon + enzyme sites
            r'(GGTCTC.{4,8}GAGACC)',    # BsaI recognition patterns
            r'BBa_[A-Z]\d{5}',          # BioBrick identifiers
            r'pSB[1-9][A-Z]\d',        # Standard plasmid backbones
        ]
    
    def detect_assembly_scars(self, sequence: str) -> Dict:
        """
        AI-based assembly pattern recognition
        Look for signs of modular assembly beyond simple enzyme sites
        """
        findings = {
            'enzyme_sites': [],
            'assembly_patterns': [],
            'risk_score': 0.0,
            'regulatory_flags': []
        }
        
        # Multi-enzyme detection
        for enzyme, sites in self.restriction_enzymes.items():
            for site in sites:
                if site in sequence.upper():
                    findings['enzyme_sites'].append({
                        'enzyme': enzyme,
                        'site': site,
                        'positions': [m.start() for m in re.finditer(site, sequence.upper())]
                    })
                    findings['risk_score'] += 0.2
        
        # Behavioral analysis of ordering patterns
        if len(findings['enzyme_sites']) >= 2:
            findings['assembly_patterns'].append('Multiple Type IIS sites detected')
            findings['risk_score'] += 0.5
            
        # Integration with African regulatory frameworks
        # (This would connect to actual regulatory databases)
        if findings['risk_score'] > 0.7:
            findings['regulatory_flags'].append('Requires review under S3741 equivalent')
            findings['regulatory_flags'].append('Alert to Africa CDC network')
        
        return findings
    
    def check_fragment_assembly_risk(self, fragments: List[str]) -> Dict:
        """
        Analyze multiple fragments for potential dangerous assembly
        """
        total_length = sum(len(f) for f in fragments)
        enzyme_density = 0
        
        for fragment in fragments:
            result = self.detect_assembly_scars(fragment)
            enzyme_density += len(result['enzyme_sites'])
        
        # Risk assessment based on fragment patterns
        if total_length > 500 or enzyme_density >= 2:
            return {
                'risk_level': 'HIGH',
                'reason': 'Multiple fragments with assembly potential',
                'recommendation': 'Requires expert review'
            }
        
        return {'risk_level': 'LOW'}

# Example usage for African regulatory integration
def integrate_african_frameworks():
    """
    Integration with existing African regulatory frameworks
    """
    frameworks = {
        'south_africa': 'National Health Laboratory Service protocols',
        'nigeria': 'Nigerian Centre for Disease Control guidelines', 
        'kenya': 'KEMRI biosafety standards',
        'senegal': 'Institut Pasteur Dakar protocols'
    }
    
    # This would connect to actual regulatory APIs/databases
    return frameworks
