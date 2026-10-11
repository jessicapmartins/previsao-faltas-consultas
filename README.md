# Previsão de faltas em consultas médicas

Projeto de ponta a ponta, supervisionado, seguindo o CRISP-DM. Ele vai do SQL ao modelo de risco e termina numa **regra de próxima melhor ação**, que escolhe o que fazer com cada consulta.

**Cliente (cenário):** rede pública de saúde em Vitória (ES).
**Pergunta de negócio:** quais consultas têm mais risco de falta, e qual ação vale a pena para cada uma (lembrete, ligação, reconfirmação ou encaixe)?

**Ferramentas:** SQL (SQLite, funções de janela) · Python (pandas, scikit-learn, Keras) · IA generativa (Gemini) · Power BI · Google Colab

## Etapas
| Etapa (CRISP-DM) | Notebook | Status |
|---|---|---|
| Entender os dados com SQL | [00 · modelagem em 3 tabelas](notebooks/00_setup_modelagem_sql.ipynb) · [01 · 9 perguntas de negócio](notebooks/01_sql_perguntas_negocio.ipynb) | ✅ |
| Análise exploratória | [02 · EDA e base analítica](notebooks/02_eda.ipynb) | ✅ |
| Modelagem (Machine Learning) | [03 · regressão logística, Random Forest, Gradient Boosting](notebooks/03_modelagem_ml.ipynb) | ✅ |
| Modelagem (Deep Learning) | [04 · rede densa em Keras](notebooks/04_deep_learning.ipynb) | ✅ |
| Decisão + IA generativa | [05 · próxima melhor ação e textos de contato](notebooks/05_proxima_melhor_acao.ipynb) | ✅ |
| Implantação | [06 · dados para o Power BI](notebooks/06_exportar_powerbi.ipynb) · [painel publicado](https://app.powerbi.com/view?r=eyJrIjoiODA0MjQyYzYtNTMwOC00ZGM0LTgxYjUtOTMyMzY2ZjBhNjYzIiwidCI6IjU4NTQwODYwLTQzNDgtNDQwMC05NjI3LTlmMTA4MWNiYWFjMiJ9) | ✅ |

## Painel interativo (Power BI)
[![Painel Power BI: faltas em consultas](img/painel_powerbi.jpg)](https://app.powerbi.com/view?r=eyJrIjoiODA0MjQyYzYtNTMwOC00ZGM0LTgxYjUtOTMyMzY2ZjBhNjYzIiwidCI6IjU4NTQwODYwLTQzNDgtNDQwMC05NjI3LTlmMTA4MWNiYWFjMiJ9)

🔗 [Abrir o painel](https://app.powerbi.com/view?r=eyJrIjoiODA0MjQyYzYtNTMwOC00ZGM0LTgxYjUtOTMyMzY2ZjBhNjYzIiwidCI6IjU4NTQwODYwLTQzNDgtNDQwMC05NjI3LTlmMTA4MWNiYWFjMiJ9): 4 páginas (visão geral, paradoxo do SMS, agenda da semana com a próxima melhor ação, premissas e modelo), com filtros por sexo, faixa etária, bairro, SMS e período.

📘 **Documentação do modelo Power BI:** [abrir](https://claude.ai/artifact/NVBMomumL2gSB1UVCS4ktG) · gerada por [`docs/gerar_documentacao.py`](docs/gerar_documentacao.py), que lê os arquivos TMDL do projeto (tabelas, colunas, 17 medidas DAX, relação e fontes).

## Principais resultados
- **20,2% das consultas viram falta** (22.319 de 110.527).
- **A antecedência é o principal fator:** consultas do mesmo dia têm 4,6% de falta; a partir de 8 dias de antecedência, mais de 30%. Histórico de faltas e idade vêm em seguida.
- **O efeito do SMS não pode ser medido com esta base:** na base inteira, quem recebeu SMS falta mais (27,6% contra 16,7%). Dentro de cada faixa de antecedência, falta menos. O SMS não foi enviado ao acaso (só a partir de 3 dias de antecedência), então a diferença não é causal.
- **Modelo:** Gradient Boosting com ROC-AUC 0,73 e PR-AUC 0,34, contra 0,19 de um modelo sem informação, em uma semana de teste separada no tempo. Ligando para os 20% de maior risco, a equipe encontra 38% das faltas, quase o dobro do acaso.
- **Deep learning:** uma rede densa em Keras empatou com o Gradient Boosting (PR-AUC 0,341 contra 0,342). Como não ganhou nada e é mais complexa de treinar e explicar, o modelo final continua o Gradient Boosting.
- **Próxima melhor ação:** uma regra de custo esperado escolhe entre nenhuma ação, lembrete, ligação, reconfirmação e encaixe. Na semana de teste, a regra reduziria o custo das faltas em 11,5%, contra 8,8% de ligar para todos.
  - Os efeitos das ações são **premissas ilustrativas**, a validar com teste A/B.

## Limitações
- A base cobre só 6 semanas de 2016, e 60% das consultas são a primeira do paciente na base.
- Faltam variáveis importantes: especialidade, horário, distância e clima.
- O modelo superestima o risco nas faixas mais altas na semana de teste, que teve menos faltas. Em uso real, precisaria de recalibração periódica.
- O encaixe (overbooking) tem custo humano em saúde pública: só deve ser usado com fila de espera e limite por turno.

## Dados
[Medical Appointment No Shows](https://www.kaggle.com/datasets/joniarroba/noshowappointments), de Joni Hoppen e Aquarela Analytics: 110.527 agendamentos em Vitória (ES), 2016. Licença [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). O arquivo original está em `data/raw/`, sob a mesma licença e sem alterações.

## Como rodar
1. Abra o notebook 00 no Colab pelo botão "Abrir no Colab" e execute. Ele cria `consultas.db` no seu Google Drive.
2. Siga os notebooks na ordem.
   - Cada um termina gravando o banco no Drive.
   - Se uma tabela de uma etapa anterior não aparecer, o notebook a recria sozinho com o mesmo código, que fica em [`src/apoio.py`](src/apoio.py).
3. No notebook 05, a parte de IA generativa usa a chave `GEMINI_API_KEY` guardada nos *Secrets* do Colab. Nunca escreva a chave no notebook.

---
**Autora:** Jéssica Priscila de Oliveira Martins · [LinkedIn](https://www.linkedin.com/in/jessica-oliveira-martins/) · [Portfólio](https://claude.ai/artifact/YPyaaqo16QuwKBKGw9VF5m)
