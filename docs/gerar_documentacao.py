"""Gera a documentação do modelo Power BI lendo os arquivos TMDL do projeto (.pbip).

Uso:  python gerar_documentacao.py <pasta .SemanticModel/definition> <saida.html>
A estrutura (tabelas, colunas, tipos, medidas, DAX, relações, fontes) vem dos arquivos;
as descrições de negócio estão no dicionário DESCRICOES abaixo.
"""
import html, json, os, re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'definition'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'documentacao_modelo.html'

# ------------------------------------------------------------------ leitura do TMDL
def nome(s):
    s = s.strip()
    return s[1:-1].replace("''", "'") if s.startswith("'") and s.endswith("'") else s

def ler_tabela(path):
    t = {'colunas': [], 'medidas': [], 'descricao': '', 'fonte': ''}
    linhas = open(path, encoding='utf-8').read().splitlines()
    atual, doc, em_fonte, fonte = None, '', False, []
    for ln in linhas:
        if ln.startswith('///'):
            doc = ln[3:].strip(); continue
        if ln.startswith('table '):
            t['nome'] = nome(ln[6:]); t['descricao'] = doc; doc = ''; continue
        s = ln.strip()
        if em_fonte:
            if ln.startswith('\t\t\t') or not s:
                fonte.append(ln.strip('\n')); continue
            em_fonte = False
        if ln.startswith('\t') and not ln.startswith('\t\t'):
            if s.startswith('///'):
                doc = s[3:].strip(); continue
            m = re.match(r"(measure|column)\s+('(?:[^']|'')+'|[^=]+?)(?:\s*=\s*(.*))?$", s)
            if m:
                kind, n, expr = m.groups()
                atual = {'nome': nome(n), 'expr': (expr or '').strip(), 'props': {}, 'descricao': doc}
                doc = ''
                (t['medidas'] if kind == 'measure' else t['colunas']).append(atual)
                continue
            if s.startswith('partition'):
                atual = None; continue
        elif ln.startswith('\t\t') and atual is not None:
            if ':' in s and not s.startswith('source'):
                k, v = s.split(':', 1); atual['props'][k.strip()] = v.strip()
            elif s in ('isHidden',):
                atual['props']['isHidden'] = 'true'
        if s.startswith('source ='):
            em_fonte, fonte = True, []
    t['fonte'] = '\n'.join(x.strip() for x in fonte if x.strip())
    return t

tabelas = [ler_tabela(os.path.join(SRC, 'tables', f)) for f in ['Consultas.tmdl', 'Agenda.tmdl', 'Premissas.tmdl', 'Modelos.tmdl']]
rels = re.findall(r'fromColumn:\s*(\S+)\s+toColumn:\s*(\S+)', open(os.path.join(SRC, 'relationships.tmdl'), encoding='utf-8').read())
modelo = open(os.path.join(SRC, 'model.tmdl'), encoding='utf-8').read()
cultura = re.search(r'culture:\s*(\S+)', modelo).group(1)

# ------------------------------------------------------------------ descrições de negócio
DESCRICOES = {
    'Consultas': 'Uma linha por consulta agendada (abr–jun/2016), já limpa no notebook 02. É a base de toda a visão histórica.',
    'Agenda': 'Consultas da semana de teste (30/05 a 08/06/2016), com o risco previsto pelo modelo e a ação recomendada pela regra de custo.',
    'Premissas': 'Custo e efeito premissados de cada ação. São ilustrativos e servem para a regra de próxima melhor ação.',
    'Modelos': 'Métricas dos modelos na semana de teste, para a comparação da última página.',
    'Consultas.consulta_id': 'Identificador da consulta. Chave da relação com Agenda.',
    'Consultas.data_consulta': 'Data da consulta.', 'Consultas.data_agendamento': 'Data em que a consulta foi marcada.',
    'Consultas.dia_semana': 'Dia da semana por extenso (técnica, usada para ordenar).',
    'Consultas.antecedencia_dias': 'Dias entre o agendamento e a consulta.',
    'Consultas.faixa_antecedencia': 'Faixa de antecedência com prefixo numérico, usada para ordenar.',
    'Consultas.idade': 'Idade do paciente na data da consulta.', 'Consultas.faixa_etaria': 'Faixa etária (0-12, 13-18, …, 60+).',
    'Consultas.sexo': 'Feminino ou Masculino.', 'Consultas.bairro': 'Bairro da unidade de saúde.',
    'Consultas.bolsa_familia': '1 se o paciente recebe Bolsa Família.', 'Consultas.hipertensao': '1 se tem hipertensão.',
    'Consultas.diabetes': '1 se tem diabetes.', 'Consultas.alcoolismo': '1 se tem registro de alcoolismo.',
    'Consultas.deficiencia': '1 se tem alguma deficiência.', 'Consultas.sms_recebido': '1 se recebeu lembrete por SMS.',
    'Consultas.historico': 'Primeira consulta, já veio e nunca faltou, ou já faltou antes (técnica).',
    'Consultas.faltou': '1 se o paciente faltou. Variável alvo.',
    'Consultas.periodo': 'Histórico (treino) ou semana de teste, conforme a separação no tempo do notebook 03.',
    'Consultas.Dia da semana': 'Abreviação do dia para os eixos, ordenada de segunda a sábado.',
    'Consultas.dia_ordem': 'Ordem de segunda (1) a sábado (6).',
    'Consultas.Antecedência': 'Faixa de antecedência sem o prefixo, ordenada pela coluna técnica.',
    'Consultas.SMS': 'Rótulo "Com SMS" ou "Sem SMS" para filtros.',
    'Consultas.historico_ordem': 'Ordem das categorias de histórico.',
    'Consultas.Histórico do paciente': 'Cópia de exibição de historico, ordenada por historico_ordem.',
    'Agenda.consulta_id': 'Identificador da consulta. Liga com Consultas.', 'Agenda.data_consulta': 'Data da consulta.',
    'Agenda.risco': 'Probabilidade de falta prevista pelo Gradient Boosting.', 'Agenda.faltou': '1 se faltou de fato (para conferir o modelo).',
    'Agenda.acao': 'Ação de menor custo esperado (técnica).',
    'Agenda.custo_esperado_acao': 'Custo esperado com a ação escolhida (R$).', 'Agenda.custo_esperado_sem_acao': 'Custo esperado sem nenhuma ação (R$).',
    'Agenda.faixa_risco': 'Faixa de risco com prefixo numérico (técnica).', 'Agenda.economia_esperada': 'Custo sem ação menos custo com a ação (R$).',
    'Agenda.Faixa de risco': 'Faixa de risco para os eixos, ordenada.', 'Agenda.acao_ordem': 'Ordem das ações, da mais barata à mais intensa.',
    'Agenda.Ação recomendada': 'Ação recomendada para exibição, ordenada por acao_ordem.',
    'Premissas.Ação': 'Nome da ação.', 'Premissas.Custo por consulta': 'Custo de aplicar a ação em uma consulta.',
    'Premissas.Redução da falta (premissa)': 'Quanto a ação reduz a chance de falta (premissa, não medida).',
    'Premissas.Custo do horário vago': 'Custo de um horário que fica vago (R$ 100).',
    'Modelos.Modelo': 'Nome do modelo.', 'Modelos.ROC-AUC': 'Capacidade de separar quem falta de quem comparece.',
    'Modelos.PR-AUC': 'Precisão média; referência sem informação: 0,185.', 'Modelos.Brier': 'Erro quadrático da probabilidade (menor é melhor).',
    'Modelos.Recall nos 20% de maior risco': 'Das faltas reais, quantas estão entre os 20% de maior risco previsto.',
    'm:Consultas': 'Total de consultas no contexto.', 'm:Faltas': 'Total de faltas.', 'm:Taxa de falta': 'Faltas ÷ consultas.',
    'm:Taxa de falta com SMS': 'Taxa de falta só das consultas com SMS.', 'm:Taxa de falta sem SMS': 'Taxa de falta só das consultas sem SMS.',
    'm:% com SMS': 'Parcela das consultas que recebeu SMS.', 'm:Taxa de falta no mesmo dia': 'Taxa de falta de quem agendou para o mesmo dia.',
    'm:Taxa de falta com 8+ dias': 'Taxa de falta de quem agendou com 8 dias ou mais.',
    'm:Consultas na agenda': 'Consultas da semana de teste.',
    'm:% da agenda': 'Participação de cada ação na agenda, ignorando o filtro de ação.',
    'm:Risco médio previsto': 'Média do risco previsto.', 'm:Falta real na agenda': 'Taxa de falta real na semana de teste.',
    'm:Custo esperado sem ação': 'Soma do custo esperado sem ação.', 'm:Custo esperado com a regra': 'Soma do custo esperado com a ação recomendada.',
    'm:Economia esperada': 'Diferença entre os dois custos (R$).', 'm:Economia esperada %': 'Economia sobre o custo sem ação.',
    'm:Consultas de alto risco': 'Consultas com risco previsto de 30% ou mais.',
}
PAGINAS = [
    ('Visão geral', 'Taxa de falta geral, por dia, antecedência, histórico, faixa etária e bairro (500+ consultas).', 'Sexo, faixa etária, bairro, SMS, data'),
    ('O paradoxo do SMS', 'Falta com e sem SMS dentro de cada faixa de antecedência, e quem recebe SMS.', 'Sexo, faixa etária, bairro, histórico'),
    ('Agenda da semana', 'Consultas por ação recomendada, falta real por faixa de risco, resumo por ação e leitura da economia.', 'Ação, faixa de risco, faixa etária, bairro, data'),
    ('Premissas e modelo', 'Tabela de premissas, comparação dos modelos, como a regra decide e limitações.', 'Sem filtros'),
]
VALIDACAO = [
    ('Consultas na base', '110.514', '110.514'), ('Taxa de falta', '20,2%', '20,2%'),
    ('Falta com SMS / sem SMS', '27,6% / 16,7%', '27,6% / 16,7%'), ('Consultas na semana de teste', '35.240', '35.240'),
    ('Risco médio previsto', '21,6%', '21,6%'), ('Economia esperada', 'R$ 152.234', 'R$ 152.234'),
]

# ------------------------------------------------------------------ HTML
e = html.escape
def tipo(c):
    return {'int64': 'Inteiro', 'string': 'Texto', 'dateTime': 'Data', 'double': 'Decimal'}.get(c['props'].get('dataType', ''), c['props'].get('dataType', '—'))

n_med = sum(len(t['medidas']) for t in tabelas)
n_calc = sum(1 for t in tabelas for c in t['colunas'] if c['expr'])
n_col = sum(len(t['colunas']) for t in tabelas)

sec_tabs = []
for t in tabelas:
    linhas = ''.join(
        f"<tr><td><code>{e(c['nome'])}</code>{' <span class=\"pill calc\">calculada</span>' if c['expr'] else ''}"
        f"{' <span class=\"pill hid\">oculta</span>' if c['props'].get('isHidden') else ''}</td>"
        f"<td>{tipo(c)}</td><td>{e(c['props'].get('formatString', '') or '—')}</td>"
        f"<td>{e(DESCRICOES.get(t['nome'] + '.' + c['nome'], ''))}</td></tr>" for c in t['colunas'])
    origem = 'Tabela digitada no Power Query (#table)' if '#table' in t['fonte'] else \
        'CSV: ' + (re.search(r'([\w]+\.csv)', t['fonte']).group(1) if re.search(r'([\w]+\.csv)', t['fonte']) else '—')
    sec_tabs.append(f"""
    <section class="card" id="t-{e(t['nome'])}">
      <header class="th"><h3>{e(t['nome'])}</h3><span class="meta">{len(t['colunas'])} colunas · {len(t['medidas'])} medidas · {e(origem)}</span></header>
      <p>{e(DESCRICOES.get(t['nome'], t['descricao']))}</p>
      <div class="scroll"><table><thead><tr><th>Coluna</th><th>Tipo</th><th>Formato</th><th>Descrição</th></tr></thead><tbody>{linhas}</tbody></table></div>
      <details><summary>Consulta Power Query (M)</summary><pre><code>{e(t['fonte'])}</code></pre></details>
    </section>""")

med_rows = ''.join(
    f"<article class=\"measure\"><header><h4>{e(m['nome'])}</h4><span class=\"meta\">{e(t['nome'])} · {e(m['props'].get('displayFolder', '—'))} · <code>{e(m['props'].get('formatString', ''))}</code></span></header>"
    f"<p>{e(DESCRICOES.get('m:' + m['nome'], m['descricao']))}</p><pre><code>{e(m['expr'])}</code></pre></article>"
    for t in tabelas for m in t['medidas'])
calc_rows = ''.join(
    f"<tr><td><code>{e(t['nome'])}[{e(c['nome'])}]</code></td><td><code class=\"dax\">{e(c['expr'])}</code></td>"
    f"<td>{e(('ordena por ' + c['props']['sortByColumn']) if c['props'].get('sortByColumn') else '—')}</td></tr>"
    for t in tabelas for c in t['colunas'] if c['expr'])
rel_txt = ''.join(f"<li><code>{e(a)}</code> (muitos) → <code>{e(b)}</code> (um), filtro em direção única</li>" for a, b in rels)
pag_rows = ''.join(f"<tr><td><b>{e(p)}</b></td><td>{e(d)}</td><td>{e(f)}</td></tr>" for p, d, f in PAGINAS)
val_rows = ''.join(f"<tr><td>{e(a)}</td><td class=\"num\">{e(b)}</td><td class=\"num\">{e(c)}</td><td><span class=\"pill ok\">confere</span></td></tr>" for a, b, c in VALIDACAO)

PAGE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelo_documentacao.html'), encoding='utf-8').read()
out = (PAGE.replace('{{N_TAB}}', str(len(tabelas))).replace('{{N_COL}}', str(n_col)).replace('{{N_MED}}', str(n_med))
           .replace('{{N_CALC}}', str(n_calc)).replace('{{N_REL}}', str(len(rels))).replace('{{CULTURA}}', cultura)
           .replace('{{TABELAS}}', ''.join(sec_tabs)).replace('{{MEDIDAS}}', med_rows).replace('{{CALC}}', calc_rows)
           .replace('{{RELS}}', rel_txt).replace('{{PAGINAS}}', pag_rows).replace('{{VALIDACAO}}', val_rows))
open(OUT, 'w', encoding='utf-8').write(out)
print('ok', OUT, f'{len(tabelas)} tabelas, {n_col} colunas, {n_med} medidas, {n_calc} calculadas, {len(rels)} relação')
