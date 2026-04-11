# Mwongozo wa Utendaji (SOP): Ukaguzi wa Usalama wa Kibayolojia (Offline)
**Lengo:** Kufanya ukaguzi wa protini bila kutumia mtandao ili kulinda data.

1. **Maandalizi**: Hakikisha kompyuta imezimwa mtandao (WiFi/Ethernet) ili kuzuia kuvuja kwa siri za kibaolojia.
2. **Kuanzisha**: Tekeleza `bash ../deployment/offline_setup.sh` mara moja tu ukiwa na mtandao ili kupakua data muhimu.
3. **Utekelezaji**: Tumia amri `python3 ../src/engine.py --fasta <njia_ya_faili>`.
4. **Uthibitisho**: Hakikisha faili la `audit_trail.jsonl` limeundwa kwa ajili ya ripoti za kisheria.
