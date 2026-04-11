# Procédure Opérationnelle Normalisée (SOP) : Criblage de Biosécurité Hors Ligne
**Objectif :** Effectuer un criblage sécurisé des séquences protéiques sans connexion internet.

1. **Configuration de l'environnement** : Déconnectez l'ordinateur de tout réseau pour éviter les risques d'informations sensibles.
2. **Initialisation** : Exécutez `bash ../deployment/offline_setup.sh` une fois pour télécharger les modèles.
3. **Exécution** : Lancez `python3 ../src/engine.py --fasta <chemin_du_fichier>`.
4. **Audit** : Vérifiez la création du journal `audit_trail.jsonl` pour la conformité.
