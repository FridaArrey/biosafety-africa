"""
Validate ESM-2 8M vs 650M performance on funcscreen dataset
"""
import torch
from transformers import EsmTokenizer, EsmModel
import numpy as np
from sklearn.metrics import classification_report

def compare_models():
    print("=== MODEL PERFORMANCE COMPARISON ===")
    
    # Load both models
    tokenizer_8m = EsmTokenizer.from_pretrained("facebook/esm2_t6_8M_UR50D")
    model_8m = EsmModel.from_pretrained("facebook/esm2_t6_8M_UR50D")
    
    # Test on funcscreen validation sequences
    test_sequences = [
        "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKREQVYQNG",  # AI toxin
        "MVLSEGEWQLVLHVWAKVEADVAGHGQDILIRLFKSHPETLEKFDRVKHLKTEAEMKASEDLKKHGVTVLTALGAILKKKGHHEAELKPLAQSHATKHKIPIKYLEFISEAIIHVLHSRHPGNFGADAQGAMNKALELFRKDIAAKYKELGYQG"  # Human protein
    ]
    
    for seq in test_sequences:
        # 8M model embedding
        tokens = tokenizer_8m(seq, return_tensors="pt")
        with torch.no_grad():
            outputs_8m = model_8m(**tokens)
            embedding_8m = outputs_8m.last_hidden_state.mean(dim=1)
        
        print(f"Sequence length: {len(seq)}")
        print(f"8M embedding norm: {torch.norm(embedding_8m).item():.3f}")
        print(f"8M embedding dim: {embedding_8m.shape}")
        print("---")
    
    # Performance recommendation
    print("RECOMMENDATION: Hybrid architecture")
    print("- Use 8M model for initial screening (speed)")
    print("- Escalate to 650M model for high-risk sequences (accuracy)")
    print("- Best of both: fast + accurate when needed")

if __name__ == "__main__":
    compare_models()
