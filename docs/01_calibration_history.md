# AI Governance: Calibration & Risk Assessment History

This document tracks the evolution of the prompt engineering and system-level guardrails used in the **Biosafety Africa** forensic pipeline. It serves as a technical record of how we mitigated "Passive Bias" in frontier LLMs.

## 📈 Evolution Summary

| Version | Governance Strategy | Observed AI Behavior | Security Outcome |
| :--- | :--- | :--- | :--- |
| **v1.0 (Academic)** | Open-ended analytical request. | High technical accuracy; Severe underestimation of operational risk. | ❌ **FAIL** (Mislabeled Ricin as "Low Risk") |
| **v2.0 (Forensic)** | Regulatory anchoring (CDC/CWC) + Adversarial context. | High-confidence identification; Tiered alert triggers. | ✅ **SUCCESS** (Identified Ricin/Anthrax) |
| **v2.1 (Refusal)** | Maximum-strictness protocol. | Hard refusal on specific motifs (SEB). | 🛑 **COLLISION** (False Positive Refusal) |

---

## 🔬 Phase 1: Identifying "Passive Bias" (v1.0)
**Constraint:** The model was treated as a general biology tutor.
**Failure Mode:** The model correctly identified the molecular mechanism of **Ricin** (RNA N-glycosidase) but categorized it as a "low-to-moderate" environmental risk. 
**Insight:** General-purpose training data often emphasizes the *educational* aspects of toxins over their *operational* security risks.

---

## 🛠️ Phase 2: Regulatory Anchoring (v2.0)
**Constraint:** Injected strict operational protocols requiring cross-referencing with:
- **CDC Select Agent List**
- **Chemical Weapons Convention (CWC) Schedules**
- **ENDAR Logic (Engineering vs Nature)**

**Success:** The model shifted from verbose speculation to definitive forensic identification. 
**Primary Artifact:** The model successfully escalated to a **"LEVEL 4 ALERT"** for *Bacillus anthracis* (Anthrax).

---

## 🛑 Phase 3: The "Safety Collision" Edge Case (v2.1)
**Constraint:** Maximum adversarial mindset.
**The Finding:** When analyzing **Staphylococcal Enterotoxin B (SEB)**, the model triggered a hard refusal: *"I cannot provide information or guidance on biological agents."*
**Strategic Analysis:** This represents an **Alignment Error**. The guardrails designed to prevent bioweapon *creation* are inadvertently blocking forensic *defense*. 

---

## 🛡️ Conclusion for Stakeholders
Our governance research indicates that **Base LLMs require a Regulatory Wrapper** to be useful in biosecurity. Without this wrapper, models oscillate between underestimating lethal threats and refusing to assist in legitimate forensic identification.

## 📉 Phase 4: The "Dilution" Effect (v3.0)
**Strategy:** Scientific Neutrality (Bioinformatics Persona).
**The Finding:** While v3.0 successfully bypassed the Hard Refusal seen in v2.1, it resulted in "Semantic Dilution." The model provided accurate definitions of the motifs but failed the taxonomic identification, mislabeling a bacterial toxin (SEB) as "mammalian/reptilian." 
**Security Insight:** Neutrality prompts may lower safety triggers but at the cost of forensic precision. This suggests that for high-consequence threats, a "Regulatory Guardrail" (v2.0) is superior, provided the user has authenticated "Specialized Access" to override refusal-wall collisions.
