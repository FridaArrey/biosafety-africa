"""
Create validated pathogen dataset from public sources
"""
import requests
from Bio import Entrez, SeqIO
import json

def fetch_validated_pathogens():
    """
    Fetch real pathogen sequences from NCBI for validation
    """
    # Updated with valid researcher contact for NCBI rate-limiting compliance
    Entrez.email = "frida.arreytakubetang@gmail.com"
    
    # NCBI accessions for validated pathogens (public sequences)
    validated_accessions = {
        'ricin_a_chain': 'P02879',  # UniProt
        'botulinum_ntx_a': 'P10844',  # UniProt  
        'staphylococcal_enterotoxin_b': 'P01552',  # UniProt
        'bacillus_anthracis_protective_antigen': 'P13423',  # UniProt
    }
    
    dataset = {}
    
    for pathogen, accession in validated_accessions.items():
        try:
            # Fetch from UniProt API
            url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
            response = requests.get(url)
            
            if response.status_code == 200:
                dataset[pathogen] = {
                    'accession': accession,
                    'sequence': "".join(response.text.split('\n')[1:]),  # Clean sequence
                    'source': 'UniProt',
                    'validation': 'Public database, peer-reviewed'
                }
                print(f"✓ Fetched {pathogen}: {accession}")
            else:
                print(f"✗ Failed to fetch {pathogen}: {accession}")
                
        except Exception as e:
            print(f"Error fetching {pathogen}: {e}")
    
    # Save validated dataset
    with open('data/validated_pathogens.json', 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"\n✓ Created validated dataset with {len(dataset)} pathogens")
    return dataset

if __name__ == "__main__":
    fetch_validated_pathogens()
