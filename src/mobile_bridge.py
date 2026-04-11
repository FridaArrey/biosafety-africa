"""
Bridge for Android/iOS deployment. 
Integrates LiteEngine with mobile camera/clipboard inputs.
"""
from src.engine import LiteEngine, sequence_sha256

def mobile_scan_sequence(raw_text):
    """
    Called by the Android UI layer (e.g., via Chaquopy or Kivy) 
    to process sequences captured via OCR.
    """
    # Force batch_size=1 to protect mobile RAM (typically 4GB-8GB)
    engine = LiteEngine(batch_size=1) 
    embedding = engine.embed(raw_text)
    
    # In a field deployment, this dictionary is passed back to 
    # the Java/Kotlin/Swift UI to display results.
    return {
        "status": "Success",
        "hash": sequence_sha256(raw_text),
        "embedding_preview": embedding[:5].tolist(),
        "model_version": engine.model_version
    }

if __name__ == "__main__":
    # Demo for field testing
    test_seq = "MAVVMGAVVM"
    print(f"Mobile Scan Result: {mobile_scan_sequence(test_seq)}")
