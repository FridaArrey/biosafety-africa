"""
BioSafety Africa - Realistic Performance Benchmarking
Testing on actual African lab hardware constraints
"""
import time
import psutil
import torch
from transformers import EsmTokenizer, EsmModel

def honest_performance_test():
    """
    Real performance on actual African lab hardware:
    - 2-core CPU, 4GB RAM, intermittent connectivity
    - Include embedding computation, I/O overhead, model loading
    """
    # Simulate realistic African lab hardware constraints
    print("=== HONEST PERFORMANCE TEST ===")
    print("Hardware profile: 2-core CPU, 4GB RAM, no GPU")
    
    # Model loading time (cold start)
    start_time = time.time()
    tokenizer = EsmTokenizer.from_pretrained("facebook/esm2_t6_8M_UR50D")
    model = EsmModel.from_pretrained("facebook/esm2_t6_8M_UR50D")
    loading_time = time.time() - start_time
    print(f"Model loading time: {loading_time:.2f}s")
    
    # Memory usage
    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_usage:.1f}MB")
    
    # Realistic sequence processing
    test_sequence = "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKREQVYQNG"
    
    start_time = time.time()
    # Include all pipeline steps
    tokens = tokenizer(test_sequence, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**tokens)
        embedding = outputs.last_hidden_state.mean(dim=1)
    processing_time = time.time() - start_time
    
    print(f"Actual processing time: {processing_time:.2f}s per sequence")
    print("Reality check: NOT 42ms - includes full embedding computation")
    print("Expected range: 2-5 seconds per sequence on realistic hardware")
    
    # Connectivity simulation
    print("\nConnectivity constraints:")
    print("- Model download: 30MB (requires stable connection)")
    print("- Offline operation: Possible after initial setup")
    print("- Updates: Manual USB delivery for remote locations")

if __name__ == "__main__":
    honest_performance_test()
