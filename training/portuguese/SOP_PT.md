# Procedimento Operacional Padrão (SOP): Triagem de Biossegurança Offline
**Objetivo:** Realizar triagem segura de sequências proteicas sem conexão à internet.

1. **Configuração do Ambiente**: Certifique-se de que o computador está desconectado de todas as redes para evitar "Riscos de Informação."
2. **Inicialização**: Execute `bash ../deployment/offline_setup.sh` uma vez para descarregar os modelos.
3. **Execução**: Execute `python3 ../src/engine.py --fasta <caminho_do_arquivo>`.
4. **Auditoria**: Confirme a geração do `audit_trail.jsonl` para relatórios de conformidade.
