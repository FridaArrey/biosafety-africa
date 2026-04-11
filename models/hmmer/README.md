# Common vector backbone markers (Tier 1 HMMER)

Pfam HMMs from [EBI InterPro](https://www.ebi.ac.uk/interpro/) (gzip payload decompressed). **Not** a substitute for regulated select-agent screening — indicative markers only.

```bash
hmmscan --domtblout hits.domtblout models/hmmer/*.hmm query.pep.fa
```

- `beta_lactamase_AmpR.hmm` — Class A beta-lactamase / AmpR (common antibiotic resistance on cloning vectors) (`PF13354`)
- `rep_plasmid_N.hmm` — Plasmid replication Rep protein N-terminal domain (`PF02486`)
