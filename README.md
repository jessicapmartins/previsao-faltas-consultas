# Previsão de faltas em consultas médicas

> 🚧 **Em construção.** Projeto de ponta a ponta, supervisionado, seguindo o CRISP-DM.

**Cliente (cenário):** rede pública de saúde em Vitória (ES).
**Pergunta de negócio:** quais consultas têm mais risco de falta, para priorizar lembretes e confirmações?

**Ferramentas:** SQL (SQLite) · Python (pandas, scikit-learn, XGBoost, Keras) · IA generativa (LLM) · Power BI · Google Colab

## Etapas
| Etapa (CRISP-DM) | Notebook | Status |
|---|---|---|
| Entender os dados com SQL | [00 · modelagem em tabelas](notebooks/00_setup_modelagem_sql.ipynb) · [01 · perguntas de negócio](notebooks/01_sql_perguntas_negocio.ipynb) | ⏳ |
| Análise exploratória | [02 · EDA](notebooks/02_eda.ipynb) | ⏳ |
| Modelagem (Machine Learning) | [03 · logística, Random Forest, XGBoost](notebooks/03_modelagem_ml.ipynb) | ⏳ |
| Modelagem (Deep Learning) | [04 · rede densa](notebooks/04_deep_learning.ipynb) | ⏳ |
| IA generativa | [05 · lembretes por perfil de risco](notebooks/05_ia_generativa_lembretes.ipynb) | ⏳ |
| Implantação | [06 · dados para o Power BI](notebooks/06_exportar_powerbi.ipynb) · painel publicado | ⏳ |

## Dados
[Medical Appointment No Shows](https://www.kaggle.com/datasets/joniarroba/noshowappointments), de Joni Hoppen e Aquarela Analytics: 110.527 agendamentos em Vitória (ES), 2016. Licença [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). O arquivo original está em `data/raw/` sob a mesma licença, sem alterações.

## Como rodar
1. Abra o notebook 00 no Colab pelo botão "Abrir no Colab" e execute. Ele cria `consultas.db` no seu Google Drive.
2. Siga os notebooks na ordem.

---
**Autora:** Jéssica Priscila de Oliveira Martins · [LinkedIn](https://www.linkedin.com/in/jessica-oliveira-martins/) · [Portfólio](https://claude.ai/artifact/YPyaaqo16QuwKBKGw9VF5m)
