"""Funções de apoio do projeto de previsão de faltas.

Ficam num arquivo só para que todos os notebooks usem exatamente a mesma carga,
as mesmas variáveis, o mesmo modelo final e a mesma regra de próxima melhor ação.
Cada notebook mostra o código relevante da sua etapa; este arquivo garante que
as etapas seguintes consigam recriar o que estiver faltando no banco.
"""
import os
import sqlite3

import numpy as np
import pandas as pd

REPO = 'https://raw.githubusercontent.com/jessicapmartins/previsao-faltas-consultas/main'
DRIVE = '/content/drive/MyDrive/03_Portfolio/Projetos_ML/02_previsao-faltas-consultas'
DATA_CORTE = '2016-05-30'          # consultas a partir desta data formam o teste ("a agenda futura")


# --------------------------------------------------------------------------------------
# Conexão
# --------------------------------------------------------------------------------------
def conectar():
    """No Colab: monta o Drive e usa a pasta dados do projeto. Fora dele: ../dados."""
    try:
        from google.colab import drive
        drive.mount('/content/drive')
        dados, csv = f'{DRIVE}/dados', f'{REPO}/data/raw/KaggleV2-May-2016.csv'
    except ModuleNotFoundError:
        dados, csv = '../dados', '../data/raw/KaggleV2-May-2016.csv'
    os.makedirs(dados, exist_ok=True)
    con = sqlite3.connect(f'{dados}/consultas.db')
    return con, dados, csv


def tabelas(con):
    return pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", con)['name'].tolist()


# --------------------------------------------------------------------------------------
# Etapa 00: carga e modelagem em 3 tabelas
# --------------------------------------------------------------------------------------
def carregar_base(con, csv):
    bruto = pd.read_csv(csv)
    df = bruto.rename(columns={
        'PatientId': 'paciente_id', 'AppointmentID': 'consulta_id', 'Gender': 'genero',
        'ScheduledDay': 'data_agendamento', 'AppointmentDay': 'data_consulta', 'Age': 'idade',
        'Neighbourhood': 'bairro', 'Scholarship': 'bolsa_familia', 'Hipertension': 'hipertensao',
        'Diabetes': 'diabetes', 'Alcoholism': 'alcoolismo', 'Handcap': 'deficiencia',
        'SMS_received': 'sms_recebido', 'No-show': 'faltou'})
    df['paciente_id'] = df['paciente_id'].astype('int64')
    df['faltou'] = (df['faltou'] == 'Yes').astype(int)
    df['data_agendamento'] = pd.to_datetime(df['data_agendamento']).dt.tz_localize(None).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['data_consulta'] = pd.to_datetime(df['data_consulta']).dt.strftime('%Y-%m-%d')

    bairros = (df[['bairro']].drop_duplicates().sort_values('bairro')
               .reset_index(drop=True).rename_axis('bairro_id').reset_index())
    pacientes = df[['paciente_id', 'genero', 'bolsa_familia', 'hipertensao', 'diabetes',
                    'alcoolismo', 'deficiencia']].drop_duplicates('paciente_id')
    consultas = df.merge(bairros, on='bairro')[['consulta_id', 'paciente_id', 'bairro_id', 'data_agendamento',
                                                'data_consulta', 'idade', 'sms_recebido', 'faltou']]
    for nome, tab in {'bairros': bairros, 'pacientes': pacientes, 'consultas': consultas}.items():
        tab.to_sql(nome, con, if_exists='replace', index=False)
    con.execute('CREATE INDEX IF NOT EXISTS ix_cons_pac ON consultas(paciente_id)')
    con.commit()
    return bruto


# --------------------------------------------------------------------------------------
# Etapa 02: base analítica (uma linha por consulta, só com informação disponível antes dela)
# --------------------------------------------------------------------------------------
BASE_SQL = '''
CREATE TABLE base_modelo AS
WITH c AS (
    SELECT c.consulta_id, c.paciente_id, c.data_agendamento, c.data_consulta, c.idade,
           c.sms_recebido, c.faltou, b.bairro,
           p.genero, p.bolsa_familia, p.hipertensao, p.diabetes, p.alcoolismo, p.deficiencia,
           CAST(julianday(c.data_consulta) - julianday(date(c.data_agendamento)) AS INTEGER) AS antecedencia_dias,
           CAST(strftime('%w', c.data_consulta) AS INTEGER)                              AS dia_semana
    FROM consultas c
    JOIN pacientes p ON p.paciente_id = c.paciente_id
    JOIN bairros   b ON b.bairro_id   = c.bairro_id
)
SELECT c.*,
       COUNT(*)     OVER hist                                        AS consultas_anteriores,
       COALESCE(SUM(faltou) OVER hist, 0)                            AS faltas_anteriores,
       COUNT(*)     OVER (PARTITION BY paciente_id, data_consulta)   AS consultas_no_dia
FROM c
WHERE idade BETWEEN 0 AND 100          -- remove idade -1 e idades implausíveis
  AND antecedencia_dias >= 0           -- remove consultas "antes" do agendamento
WINDOW hist AS (PARTITION BY paciente_id ORDER BY julianday(data_consulta)
                RANGE BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)   -- só dias ANTERIORES
'''


def criar_base_modelo(con):
    con.execute('DROP TABLE IF EXISTS base_modelo')
    con.execute(BASE_SQL)
    con.commit()


# --------------------------------------------------------------------------------------
# Etapa 03: variáveis e modelo final
# --------------------------------------------------------------------------------------
NUMERICAS = ['idade', 'antecedencia_dias', 'consultas_anteriores', 'faltas_anteriores', 'consultas_no_dia',
             'taxa_falta_bairro', 'sms_recebido', 'bolsa_familia', 'hipertensao', 'diabetes',
             'alcoolismo', 'deficiencia', 'feminino', 'dia_semana']


def separar(base):
    """Treino: consultas antes de DATA_CORTE. Teste: a semana seguinte, como uma agenda futura."""
    treino = base[base['data_consulta'] < DATA_CORTE].copy()
    teste = base[base['data_consulta'] >= DATA_CORTE].copy()
    return treino, teste


def preparar_X(df, taxa_bairro, taxa_geral):
    """Monta a matriz de variáveis. A taxa de falta do bairro vem SÓ do treino (evita vazamento)."""
    X = df.copy()
    X['taxa_falta_bairro'] = X['bairro'].map(taxa_bairro).fillna(taxa_geral)
    X['feminino'] = (X['genero'] == 'F').astype(int)
    X['deficiencia'] = (X['deficiencia'] > 0).astype(int)
    return X[NUMERICAS].astype(float)


def taxas_bairro(treino, minimo=50):
    """Taxa de falta por bairro no treino, suavizada para bairros com poucas consultas."""
    geral = treino['faltou'].mean()
    g = treino.groupby('bairro')['faltou'].agg(['sum', 'count'])
    return ((g['sum'] + minimo * geral) / (g['count'] + minimo)).to_dict(), geral


def modelo_final():
    from sklearn.ensemble import HistGradientBoostingClassifier
    return HistGradientBoostingClassifier(learning_rate=0.05, max_iter=400, max_leaf_nodes=31,
                                          min_samples_leaf=100, l2_regularization=1.0,
                                          early_stopping=True, validation_fraction=0.15,
                                          random_state=42)


def treinar_e_prever(con):
    base = pd.read_sql('SELECT * FROM base_modelo', con)
    treino, teste = separar(base)
    taxa_bairro, geral = taxas_bairro(treino)
    modelo = modelo_final().fit(preparar_X(treino, taxa_bairro, geral), treino['faltou'])
    teste['risco'] = modelo.predict_proba(preparar_X(teste, taxa_bairro, geral))[:, 1]
    previsoes = teste[['consulta_id', 'data_consulta', 'risco', 'faltou']]
    previsoes.to_sql('previsoes', con, if_exists='replace', index=False)
    return previsoes


# --------------------------------------------------------------------------------------
# Etapa 05: próxima melhor ação (regra de custo)
# --------------------------------------------------------------------------------------
# PREMISSAS ILUSTRATIVAS: não foram medidas nesta base. Ajuste com os números reais da unidade
# e valide os efeitos com um teste A/B antes de usar a regra de verdade.
CUSTO_FALTA = 100.0      # R$ perdidos quando um horário fica vago (custo do profissional, sala, fila)
ACOES = pd.DataFrame([
    # acao,            custo (R$), reducao_falta (efeito relativo esperado)
    ('Nenhuma ação',          0.00, 0.00),
    ('Lembrete automático',   0.25, 0.10),   # SMS ou WhatsApp
    ('Ligação de confirmação', 3.00, 0.25),
    ('Reconfirmação obrigatória', 8.00, 0.40),  # ligação + libera a vaga para a fila se não confirmar
], columns=['acao', 'custo', 'reducao_falta'])
ENCAIXE_COMPARECE = 0.80   # chance de o paciente encaixado comparecer (≈ 1 - taxa de falta)
CUSTO_SOBRECARGA = 50.0    # R$ quando o titular E o encaixe comparecem (hora extra, espera)


def custos_esperados(risco, custo_falta=CUSTO_FALTA, acoes=ACOES,
                     encaixe=ENCAIXE_COMPARECE, sobrecarga=CUSTO_SOBRECARGA):
    """Custo esperado (R$) de cada ação para cada consulta, dado o risco previsto."""
    p = np.asarray(risco)[:, None]
    c = acoes['custo'].values[None, :] + p * (1 - acoes['reducao_falta'].values[None, :]) * custo_falta
    tab = pd.DataFrame(c, columns=acoes['acao'])
    # Encaixe (overbooking): se o titular faltar, o encaixe ocupa o horário; se ambos vierem, há sobrecarga
    tab['Encaixe (overbooking)'] = (p[:, 0] * custo_falta * (1 - encaixe)
                                    + (1 - p[:, 0]) * encaixe * sobrecarga)
    return tab


def recomendar(previsoes, **kw):
    custos = custos_esperados(previsoes['risco'], **kw)
    out = previsoes.copy().reset_index(drop=True)
    out['acao'] = custos.idxmin(axis=1)
    out['custo_esperado_acao'] = custos.min(axis=1)
    out['custo_esperado_sem_acao'] = custos['Nenhuma ação']
    return out


# --------------------------------------------------------------------------------------
# Garantia contra atraso de sincronização do Google Drive
# --------------------------------------------------------------------------------------
def garantir(con, csv, *nomes):
    """Recria, na ordem certa, as tabelas que não aparecerem no banco."""
    existentes = tabelas(con)
    if 'consultas' not in existentes:
        print('Tabelas de origem não encontradas: recriando a partir do CSV...')
        carregar_base(con, csv)
    if {'base_modelo', 'previsoes', 'acoes'} & set(nomes) and 'base_modelo' not in tabelas(con):
        print('base_modelo não encontrada: recriando com o SQL do notebook 02...')
        criar_base_modelo(con)
    if {'previsoes', 'acoes'} & set(nomes) and 'previsoes' not in tabelas(con):
        print('previsoes não encontrada: retreinando o modelo final do notebook 03...')
        treinar_e_prever(con)
    if 'acoes' in nomes and 'acoes' not in tabelas(con):
        print('acoes não encontrada: aplicando a regra do notebook 05...')
        recomendar(pd.read_sql('SELECT * FROM previsoes', con)).to_sql('acoes', con, if_exists='replace', index=False)
    con.commit()
