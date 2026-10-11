"""Gera a documentação completa do painel Power BI de faltas lendo os arquivos TMDL do projeto (.pbip).

Uso:  python gerar_documentacao.py <pasta .SemanticModel/definition> <saida.html>

Vem dos arquivos do modelo: tabelas, colunas, tipos, formatos, colunas ocultas, colunas
calculadas, medidas e DAX, pastas, relação e consultas do Power Query.
Vem dos notebooks (valores conferidos com consultas DAX no modelo): os valores atuais
das medidas e os números das seções de lógica e resultados.
"""
import html, os, re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'definition'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'documentacao_modelo.html'
e = html.escape

# =============================================================== leitura do TMDL
def nome(s):
    s = s.strip()
    return s[1:-1].replace("''", "'") if s.startswith("'") and s.endswith("'") else s


def ler_tabela(path):
    t = {'colunas': [], 'medidas': [], 'fonte': ''}
    atual, doc, em_fonte, fonte = None, '', False, []
    for ln in open(path, encoding='utf-8').read().splitlines():
        s = ln.strip()
        if ln.startswith('///'):
            doc = ln[3:].strip(); continue
        if ln.startswith('table '):
            t['nome'] = nome(ln[6:]); t['doc'] = doc; doc = ''; continue
        if em_fonte:
            if ln.startswith('\t\t\t') or not s:
                fonte.append(s); continue
            em_fonte = False
        if ln.startswith('\t') and not ln.startswith('\t\t'):
            if s.startswith('///'):
                doc = s[3:].strip(); continue
            m = re.match(r"(measure|column)\s+('(?:[^']|'')+'|[^=]+?)(?:\s*=\s*(.*))?$", s)
            if m:
                kind, n, expr = m.groups()
                atual = {'nome': nome(n), 'expr': (expr or '').strip(), 'p': {}, 'doc': doc}
                doc = ''
                (t['medidas'] if kind == 'measure' else t['colunas']).append(atual)
                continue
            if s.startswith('partition'):
                atual = None
        elif ln.startswith('\t\t') and atual is not None:
            if s == 'isHidden':
                atual['p']['isHidden'] = True
            elif ':' in s:
                k, v = s.split(':', 1); atual['p'][k.strip()] = v.strip()
        if s.startswith('source ='):
            em_fonte, fonte = True, []
    t['fonte'] = '\n'.join(x for x in fonte if x)
    return t


NOMES = ['Consultas', 'Agenda', 'Premissas', 'Modelos']
T = {n: ler_tabela(os.path.join(SRC, 'tables', n + '.tmdl')) for n in NOMES}
RELS = re.findall(r'fromColumn:\s*(\S+)\s+toColumn:\s*(\S+)', open(os.path.join(SRC, 'relationships.tmdl'), encoding='utf-8').read())
CULTURA = re.search(r'culture:\s*(\S+)', open(os.path.join(SRC, 'model.tmdl'), encoding='utf-8').read()).group(1)
n_col = sum(len(t['colunas']) for t in T.values())
n_med = sum(len(t['medidas']) for t in T.values())
n_calc = sum(1 for t in T.values() for c in t['colunas'] if c['expr'])

# =============================================================== conteúdo de negócio
PAPEL = {'Consultas': ('Fato', 'fact'), 'Agenda': ('Fato da semana de teste', 'fact2'), 'Premissas': ('Apoio', 'aux'), 'Modelos': ('Apoio', 'aux')}
LINHAS = {'Consultas': '110.514', 'Agenda': '35.240', 'Premissas': '4', 'Modelos': '4'}
DESC_T = {
    'Consultas': 'Uma linha por consulta agendada entre 29/04 e 08/06/2016, já limpa no notebook 02 (13 registros com erro removidos). É a base da visão histórica e dos filtros de perfil.',
    'Agenda': 'As consultas da semana de teste (30/05 a 08/06/2016) com o risco previsto pelo modelo do notebook 03 e a ação de menor custo escolhida pela regra do notebook 05.',
    'Premissas': 'Custo e efeito premissados de cada ação. Ilustrativos: alimentam a explicação da regra na última página.',
    'Modelos': 'Métricas dos quatro modelos na semana de teste, para a comparação da última página.',
}
D = {
    'Consultas.consulta_id': 'Identificador da consulta.', 'Consultas.data_consulta': 'Data da consulta.',
    'Consultas.data_agendamento': 'Data em que a consulta foi marcada.', 'Consultas.dia_semana': 'Dia da semana por extenso.',
    'Consultas.antecedencia_dias': 'Dias entre o agendamento e a consulta.', 'Consultas.faixa_antecedencia': 'Faixa de antecedência com prefixo numérico para ordenar.',
    'Consultas.idade': 'Idade do paciente na data da consulta.', 'Consultas.faixa_etaria': 'Faixa etária: 0-12, 13-18, 19-29, 30-44, 45-59, 60+.',
    'Consultas.sexo': 'Feminino ou Masculino.', 'Consultas.bairro': 'Bairro da unidade de saúde.',
    'Consultas.bolsa_familia': '1 se recebe Bolsa Família.', 'Consultas.hipertensao': '1 se tem hipertensão.', 'Consultas.diabetes': '1 se tem diabetes.',
    'Consultas.alcoolismo': '1 se tem registro de alcoolismo.', 'Consultas.deficiencia': '1 se tem alguma deficiência.',
    'Consultas.sms_recebido': '1 se recebeu lembrete por SMS.', 'Consultas.historico': 'Primeira consulta, já veio e nunca faltou, ou já faltou antes.',
    'Consultas.faltou': '1 se faltou. Variável alvo do modelo.', 'Consultas.periodo': 'Histórico (treino) ou semana de teste.',
    'Consultas.Dia da semana': 'Rótulo curto do dia, ordenado de segunda a sábado.', 'Consultas.dia_ordem': 'Ordem do dia (1 a 6).',
    'Consultas.Antecedência': 'Faixa de antecedência para exibição.', 'Consultas.SMS': 'Com SMS ou Sem SMS, para filtros.',
    'Consultas.historico_ordem': 'Ordem das categorias de histórico.', 'Consultas.Histórico do paciente': 'Histórico para exibição, ordenado.',
    'Agenda.consulta_id': 'Identificador da consulta; chave estrangeira para Consultas.', 'Agenda.data_consulta': 'Data da consulta.',
    'Agenda.risco': 'Probabilidade de falta prevista pelo Gradient Boosting.', 'Agenda.faltou': '1 se faltou de fato.',
    'Agenda.acao': 'Ação de menor custo esperado.', 'Agenda.custo_esperado_acao': 'Custo esperado com a ação escolhida.',
    'Agenda.custo_esperado_sem_acao': 'Custo esperado sem nenhuma ação.', 'Agenda.faixa_risco': 'Faixa de risco com prefixo para ordenar.',
    'Agenda.economia_esperada': 'Custo sem ação menos custo com a ação.', 'Agenda.Faixa de risco': 'Faixa de risco para exibição.',
    'Agenda.acao_ordem': 'Ordem das ações, da mais leve à mais intensa.', 'Agenda.Ação recomendada': 'Ação para exibição, ordenada.',
    'Premissas.Ação': 'Nome da ação.', 'Premissas.Custo por consulta': 'Custo de aplicar a ação em uma consulta.',
    'Premissas.Redução da falta (premissa)': 'Quanto a ação reduz a chance de falta.', 'Premissas.Custo do horário vago': 'Custo de um horário que fica vago.',
    'Modelos.Modelo': 'Nome do modelo.', 'Modelos.ROC-AUC': 'Separação entre quem falta e quem comparece.',
    'Modelos.PR-AUC': 'Precisão média; sem informação: 0,185.', 'Modelos.Brier': 'Erro da probabilidade; menor é melhor.',
    'Modelos.Recall nos 20% de maior risco': 'Faltas encontradas entre os 20% de maior risco.',
}
MED = {   # descrição, valor atual (sem filtros), conferido no modelo
    'Consultas': ('Consultas no contexto de filtro.', '110.514'), 'Faltas': ('Total de faltas.', '22.311'),
    'Taxa de falta': ('Faltas ÷ consultas. Medida base de quase todo o relatório.', '20,2%'),
    'Taxa de falta com SMS': ('Taxa de falta só das consultas com SMS.', '27,6%'), 'Taxa de falta sem SMS': ('Taxa de falta só das consultas sem SMS.', '16,7%'),
    '% com SMS': ('Parcela das consultas que recebeu SMS.', '32,1%'),
    'Taxa de falta no mesmo dia': ('Taxa de falta de quem agendou para o mesmo dia.', '4,6%'),
    'Taxa de falta com 8+ dias': ('Taxa de falta de quem agendou com 8 dias ou mais.', '32,1%'),
    'Consultas na agenda': ('Consultas da semana de teste.', '35.240'),
    '% da agenda': ('Participação da ação no total da agenda, ignorando o filtro de ação.', '100,0%'),
    'Risco médio previsto': ('Média do risco previsto pelo modelo.', '21,6%'), 'Falta real na agenda': ('Taxa de falta real na semana de teste.', '18,5%'),
    'Custo esperado sem ação': ('Soma do custo esperado se nada for feito.', 'R$ 762.154'),
    'Custo esperado com a regra': ('Soma do custo esperado com a ação recomendada.', 'R$ 609.920'),
    'Economia esperada': ('Diferença entre os dois custos.', 'R$ 152.234'), 'Economia esperada %': ('Economia sobre o custo sem ação.', '20,0%'),
    'Consultas de alto risco': ('Consultas com risco previsto de 30% ou mais.', '10.605'),
}
PASTA_DESC = {'Histórico': 'Base inteira, para a visão geral.', 'SMS': 'O paradoxo do SMS.', 'Agenda': 'Semana de teste e regra de próxima melhor ação.'}

# =============================================================== helpers de HTML
def dax(code):
    code = e(code)
    code = re.sub(r'(&quot;.*?&quot;)', r'<span class="k-str">\1</span>', code)
    code = re.sub(r"(\b[A-Za-zÀ-ú_]+\[[^\]]+\]|\[[^\]]+\])", r'<span class="k-ref">\1</span>', code)
    code = re.sub(r'\b([A-Z][A-Z\.]+)(?=\()', r'<span class="k-fn">\1</span>', code)
    code = re.sub(r'(?<![\w\[#])(\d+(?:\.\d+)?)(?![\w\]])', r'<span class="k-num">\1</span>', code)
    return code


def tipo(c):
    return {'int64': 'Inteiro', 'string': 'Texto', 'dateTime': 'Data', 'double': 'Decimal'}.get(c['p'].get('dataType', ''), '—')


def tags(tn, c):
    out = []
    if tn == 'Consultas' and c['nome'] == 'consulta_id':
        out.append('<span class="tag pk">PK</span>')
    if tn == 'Agenda' and c['nome'] == 'consulta_id':
        out.append('<span class="tag fk">FK</span>')
    if c['expr']:
        out.append('<span class="tag calc">calculada</span>')
    if c['p'].get('isHidden'):
        out.append('<span class="tag hid">oculta</span>')
    if c['p'].get('sortByColumn'):
        out.append(f'<span class="tag">ordena por {e(c["p"]["sortByColumn"])}</span>')
    return ' '.join(out)


def hbars(rows, maxv, fmt=lambda v: f'{v:.1%}'.replace('.', ','), color='var(--coral)'):
    return '<div class="hbars">' + ''.join(
        f'<div class="hb"><span class="lbl">{e(l)}</span><span class="track"><span class="fill" style="width:{v/maxv*100:.1f}%;background:{color}"></span></span><span class="v">{fmt(v)}</span></div>'
        for l, v in rows) + '</div>'

# =============================================================== seções
sec_tabelas = ''
for tn in NOMES:
    t = T[tn]
    papel, cls = PAPEL[tn]
    origem = 'Tabela digitada (#table)' if '#table' in t['fonte'] else (re.search(r'(\w+\.csv)', t['fonte']).group(1) if re.search(r'(\w+\.csv)', t['fonte']) else '—')
    rows = ''.join(f"<tr><td><code>{e(c['nome'])}</code></td><td>{tipo(c)}</td><td>{tags(tn, c)}</td>"
                   f"<td><code class=\"fmt\">{e(c['p'].get('formatString', '') or '—')}</code></td><td>{e(D.get(tn + '.' + c['nome'], ''))}</td></tr>"
                   for c in t['colunas'])
    sec_tabelas += f"""
      <article class="panel tcard" id="tab-{tn}">
        <div class="tcard-head"><h3>{tn}</h3><span class="role {cls}">{papel}</span></div>
        <p>{e(DESC_T[tn])}</p>
        <div class="chips"><span class="chip"><b>{LINHAS[tn]}</b> linhas</span><span class="chip"><b>{len(t['colunas'])}</b> colunas</span>
          <span class="chip"><b>{len(t['medidas'])}</b> medidas</span><span class="chip">origem: <b>{e(origem)}</b></span></div>
        <div class="tw"><table><thead><tr><th>Campo</th><th>Tipo</th><th>Marcadores</th><th>Formato</th><th>Descrição</th></tr></thead><tbody>{rows}</tbody></table></div>
        <details><summary>Ver a consulta Power Query (M)</summary><pre class="m">{e(t['fonte'])}</pre></details>
      </article>"""

pastas = {}
for tn in NOMES:
    for m in T[tn]['medidas']:
        pastas.setdefault(m['p'].get('displayFolder', 'Sem pasta'), []).append((tn, m))
sec_medidas = ''
for pasta, ms in pastas.items():
    cards = ''.join(f"""<article class="mcard"><div class="mtop"><span class="mname">{e(m['nome'])}</span>
        <span class="mval">valor atual <b>{e(MED.get(m['nome'], ('', '—'))[1])}</b><code class="fmt">{e(m['p'].get('formatString', ''))}</code></span></div>
        <p class="mdesc">{e(MED.get(m['nome'], (m['doc'], ''))[0])}</p><pre class="dax">{dax(m['expr'])}</pre></article>""" for tn, m in ms)
    sec_medidas += f"""<div class="folder"><div class="folder-head"><h3>📁 {e(pasta)}</h3><span class="muted">{len(ms)} medidas · {e(PASTA_DESC.get(pasta, ''))}</span></div><div class="mgrid">{cards}</div></div>"""

calc_rows = ''.join(f"<tr><td><code>{e(tn)}[{e(c['nome'])}]</code></td><td><pre class=\"dax inline\">{dax(c['expr'])}</pre></td><td>{e(D.get(tn + '.' + c['nome'], ''))}</td></tr>"
                    for tn in NOMES for c in T[tn]['colunas'] if c['expr'])

# diagrama de relacionamentos (SVG)
def er_box(x, y, w, title, fields, head, dashed=False):
    h = 40 + 22 * len(fields) + 12
    out = f'<rect class="dg-box{" dash" if dashed else ""}" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>'
    if not dashed:
        out += f'<path class="dg-head {head}" d="M{x} {y+10} a10 10 0 0 1 10 -10 h{w-20} a10 10 0 0 1 10 10 v26 h-{w} z"/>'
        out += f'<text class="dg-title" x="{x+14}" y="{y+24}">{e(title)}</text>'
    else:
        out += f'<text class="dg-title dark" x="{x+14}" y="{y+24}">{e(title)}</text>'
    for i, (k, f) in enumerate(fields):
        yy = y + 58 + 22 * i
        if k:
            out += f'<text class="dg-key {k.lower()}" x="{x+14}" y="{yy}">{k}</text>'
        out += f'<text class="dg-field" x="{x+44}" y="{yy}">{e(f)}</text>'
    return out, h

b1, h1 = er_box(40, 30, 270, 'Consultas · fato', [('PK', 'consulta_id'), ('', 'data_consulta'), ('', 'antecedencia_dias'), ('', 'faixa_etaria · sexo · bairro'), ('', 'sms_recebido · faltou'), ('', '+ 14 campos · 8 medidas')], 'f')
b2, h2 = er_box(470, 30, 270, 'Agenda · semana de teste', [('FK', 'consulta_id'), ('', 'risco'), ('', 'Ação recomendada'), ('', 'Faixa de risco'), ('', 'custos e economia'), ('', '+ 7 campos · 9 medidas')], 'a')
b3, h3 = er_box(820, 30, 200, 'Premissas', [('', 'Ação'), ('', 'Custo por consulta'), ('', 'Redução da falta')], '', True)
b4, h4 = er_box(820, 175, 200, 'Modelos', [('', 'Modelo'), ('', 'ROC-AUC · PR-AUC'), ('', 'Brier · Recall')], '', True)
ER = f'''<svg viewBox="0 0 1060 320" role="img" aria-label="Consultas (um) relacionada a Agenda (muitos) por consulta_id; Premissas e Modelos sem relação">
  <defs><marker id="arr" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="dg-arrow"/></marker></defs>
  {b1}{b2}{b3}{b4}
  <path class="dg-rel" d="M310 88 C 390 88, 390 88, 466 88" marker-end="url(#arr)"/>
  <text class="dg-card" x="318" y="80">1</text><text class="dg-card" x="450" y="80">*</text>
  <text class="dg-sub" x="388" y="112" text-anchor="middle">filtra →</text>
  <text class="dg-sub" x="920" y="300" text-anchor="middle">tabelas de apoio, sem relação</text>
</svg>'''

rel_rows = ''.join(f"<tr><td><code>{e(b)}</code></td><td><code>{e(a)}</code></td><td>1 : *</td><td>Única (Consultas → Agenda)</td><td><span class=\"pill ok\">ativa</span></td></tr>" for a, b in RELS)

# =============================================================== página
PAGE = f'''<title>Documentação · Painel de Faltas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: documentação técnica com sumário lateral que acompanha a rolagem, conteúdo em seções numeradas na ordem de leitura */
:root{{
  --bg:#F4F7FA; --surface:#FFFFFF; --surface-2:#EDF2F7; --ink:#14233A; --muted:#5B6B7F; --line:#DCE4EE;
  --navy:#13315C; --teal:#0E9F8E; --teal-soft:#DDF3F0; --coral:#E4572E; --amber:#E0961A; --sky:#3E8FD0; --purple:#6F5FE8;
  --on-accent:#FFFFFF; --code-bg:#EEF2F8; --c-fn:#0C7F72; --c-str:#A2501B; --c-ref:#2F4FB0; --c-num:#8A3AA0;
  --shadow:0 1px 2px rgba(19,49,92,.05),0 8px 24px rgba(19,49,92,.06);
  --display:"Plus Jakarta Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  --body:"Source Sans 3",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{
  --bg:#0C1420; --surface:#121D2C; --surface-2:#182638; --ink:#E4EBF4; --muted:#9AAABD; --line:#243449;
  --navy:#6E9BDA; --teal:#35C2AF; --teal-soft:#123532; --coral:#F07A5E; --amber:#F0B04A; --sky:#6FB2E8; --purple:#9C91F2;
  --on-accent:#08131F; --code-bg:#0B1522; --c-fn:#5FD3C1; --c-str:#EAA36E; --c-ref:#9DB7FF; --c-num:#D7A1EA;
  --shadow:0 1px 2px rgba(0,0,0,.35); color-scheme:dark}}}}
:root[data-theme="dark"]{{
  --bg:#0C1420; --surface:#121D2C; --surface-2:#182638; --ink:#E4EBF4; --muted:#9AAABD; --line:#243449;
  --navy:#6E9BDA; --teal:#35C2AF; --teal-soft:#123532; --coral:#F07A5E; --amber:#F0B04A; --sky:#6FB2E8; --purple:#9C91F2;
  --on-accent:#08131F; --code-bg:#0B1522; --c-fn:#5FD3C1; --c-str:#EAA36E; --c-ref:#9DB7FF; --c-num:#D7A1EA;
  --shadow:0 1px 2px rgba(0,0,0,.35); color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font:16px/1.6 var(--body)}}
.shell{{max-width:1260px;margin:0 auto;padding-inline:clamp(16px,3vw,32px);padding-block:36px 80px;display:grid;grid-template-columns:230px minmax(0,1fr);gap:52px}}
@media (max-width:960px){{.shell{{grid-template-columns:1fr}} nav.toc{{position:static!important;max-height:none!important}}}}
main{{min-width:0;display:flex;flex-direction:column;gap:64px}}
h1,h2,h3{{font-family:var(--display);margin:0;text-wrap:balance;letter-spacing:-.015em}}
h1{{font-size:clamp(2.1rem,5vw,3.3rem);font-weight:800;line-height:1.04}}
h2{{font-size:1.8rem;font-weight:800;line-height:1.15}}
h3{{font-size:1.15rem;font-weight:700}}
p{{margin:0;max-width:70ch}}
a{{color:var(--teal)}}
a:focus-visible,summary:focus-visible{{outline:2px solid var(--teal);outline-offset:2px;border-radius:4px}}
code{{font-family:var(--mono);font-size:.85em}}
.muted{{color:var(--muted)}}
.eyebrow{{font:600 .74rem/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--teal)}}
nav.toc{{position:sticky;top:calc(env(safe-area-inset-top,0px) + 28px);align-self:start;max-height:calc(100vh - 56px);overflow:auto}}
.toc .brand{{font:800 1rem/1.2 var(--display)}}
.toc .sub{{font-size:.84rem;color:var(--muted);margin:2px 0 18px}}
.toc ol{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;border-left:1px solid var(--line);counter-reset:s}}
.toc a{{display:flex;gap:8px;padding:6px 12px;margin-left:-1px;border-left:2px solid transparent;color:var(--muted);text-decoration:none;font-size:.9rem;line-height:1.35}}
.toc a::before{{counter-increment:s;content:counter(s,decimal-leading-zero);font:500 .74rem/1.6 var(--mono);color:var(--line)}}
.toc a:hover{{color:var(--ink)}}
.toc a.on{{color:var(--teal);border-left-color:var(--teal);font-weight:600}}
.toc a.on::before{{color:var(--teal)}}
.hero{{display:flex;flex-direction:column;gap:18px}}
.lede{{font-size:1.15rem;max-width:62ch}}
.meta{{display:flex;flex-wrap:wrap;gap:6px 22px;font-size:.88rem;color:var(--muted)}}
.meta b{{color:var(--ink);font-weight:600}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}
.kpi{{border-radius:12px;padding:16px 18px;display:flex;flex-direction:column;gap:6px;color:var(--on-accent)}}
.kpi .l{{font-size:.84rem;opacity:.9}} .kpi .v{{font:800 2rem/1 var(--display);font-variant-numeric:tabular-nums}} .kpi .s{{font-size:.8rem;opacity:.85}}
.k1{{background:var(--navy)}} .k2{{background:var(--coral)}} .k3{{background:var(--teal)}} .k4{{background:var(--purple)}}
.stack{{display:flex;height:34px;border-radius:8px;overflow:hidden}}
.stack span{{display:flex;align-items:center;padding-inline:8px;font:600 .78rem/1 var(--body);color:#fff;white-space:nowrap;overflow:hidden}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:.84rem;color:var(--muted)}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
section{{display:flex;flex-direction:column;gap:20px;scroll-margin-top:24px}}
.sec-head{{display:flex;flex-direction:column;gap:8px;border-top:1px solid var(--line);padding-top:22px}}
.panel{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:var(--shadow);min-width:0}}
.grid2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}
@media (max-width:760px){{.grid2,.issues{{grid-template-columns:1fr!important}}}}
.callout{{display:block;padding:14px 16px;border-radius:12px;background:var(--teal-soft);font-size:.95rem}}
.callout.warn{{background:color-mix(in srgb,var(--amber) 16%,var(--surface))}}
.flow{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;align-items:stretch}}
@media (max-width:860px){{.flow{{grid-template-columns:1fr}}}}
.step{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:6px;position:relative}}
.step b{{font-family:var(--display)}} .step span{{font-size:.86rem;color:var(--muted)}}
.step .n{{font:500 .72rem var(--mono);color:var(--teal)}}
.step.key{{border-color:var(--teal);background:var(--teal-soft)}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--surface)}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}
th,td{{text-align:left;padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{font:600 .74rem/1.3 var(--body);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);background:var(--surface-2);white-space:nowrap}}
tr:last-child td{{border-bottom:0}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td code{{white-space:nowrap}}
.tag{{display:inline-block;font:500 .7rem/1 var(--mono);padding:4px 6px;border-radius:5px;background:var(--surface-2);color:var(--muted);white-space:nowrap;margin:1px 0}}
.tag.pk{{background:var(--teal-soft);color:var(--teal)}} .tag.fk{{background:color-mix(in srgb,var(--sky) 18%,transparent);color:var(--sky)}}
.tag.calc{{background:color-mix(in srgb,var(--purple) 16%,transparent);color:var(--purple)}} .tag.hid{{background:transparent;border:1px dashed var(--line)}}
code.fmt{{color:var(--muted)}}
.tcard{{display:flex;flex-direction:column;gap:14px}}
.tcard-head{{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px}}
.tcard-head h3{{font-family:var(--mono);font-size:1.1rem;font-weight:500}}
.role{{font:600 .72rem/1 var(--body);letter-spacing:.06em;text-transform:uppercase;padding:5px 9px;border-radius:999px}}
.role.fact{{background:var(--teal);color:var(--on-accent)}} .role.fact2{{background:var(--navy);color:var(--on-accent)}} .role.aux{{border:1px dashed var(--muted);color:var(--muted)}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{font-size:.84rem;padding:4px 10px;border-radius:999px;background:var(--surface-2);color:var(--muted)}} .chip b{{color:var(--ink);font-weight:600}}
details summary{{cursor:pointer;color:var(--teal);font-size:.9rem}}
pre.m{{margin:8px 0 0;padding:12px 14px;border-radius:8px;background:var(--code-bg);font:.78rem/1.6 var(--mono);overflow-x:auto;white-space:pre-wrap;word-break:break-word}}
.diagram{{overflow-x:auto}}
.diagram svg{{display:block;width:100%;min-width:760px;height:auto}}
.dg-box{{fill:var(--surface);stroke:var(--line);stroke-width:1.2}} .dg-box.dash{{stroke-dasharray:5 4;fill:var(--surface-2)}}
.dg-head.f{{fill:var(--teal)}} .dg-head.a{{fill:var(--navy)}}
.dg-title{{font:700 13.5px var(--display);fill:var(--on-accent)}} .dg-title.dark{{fill:var(--ink)}}
.dg-field{{font:12.5px var(--body);fill:var(--ink)}}
.dg-key{{font:600 10px var(--mono)}} .dg-key.pk{{fill:var(--teal)}} .dg-key.fk{{fill:var(--sky)}}
.dg-rel{{fill:none;stroke:var(--muted);stroke-width:1.8}} .dg-arrow{{fill:var(--muted)}}
.dg-card{{font:700 14px var(--mono);fill:var(--muted)}} .dg-sub{{font:12px var(--body);fill:var(--muted)}}
.formula{{font:500 1rem/1.6 var(--mono);padding:16px 18px;border-radius:10px;background:var(--code-bg);overflow-x:auto;white-space:nowrap}}
.zones{{display:flex;flex-direction:column;gap:6px}}
.zones .bar{{display:grid;grid-template-columns:2.5fr 15.5fr 15fr 7fr 60fr;height:44px;border-radius:8px;overflow:hidden}}
.zones .bar div{{display:flex;align-items:center;justify-content:center;font:600 .74rem var(--body);color:#fff;text-align:center;line-height:1.1;padding:2px;overflow:hidden}}
.zones .ticks{{position:relative;height:18px;font-size:.76rem;color:var(--muted)}}
@media (max-width:600px){{.zones .ticks{{display:none}}}}
.zones .ticks span{{position:absolute;transform:translateX(-50%);font-variant-numeric:tabular-nums}}
.hbars{{display:flex;flex-direction:column;gap:8px}}
.hb{{display:grid;grid-template-columns:minmax(120px,210px) minmax(0,1fr) 56px;align-items:center;gap:10px;font-size:.9rem}}
.hb .track{{height:18px;background:var(--surface-2);border-radius:4px;position:relative;overflow:hidden}}
.hb .fill{{position:absolute;inset:0 auto 0 0;border-radius:4px}}
.hb .v{{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}}
.pair{{display:grid;grid-template-columns:minmax(76px,110px) minmax(0,1fr) auto;gap:6px 12px;align-items:center;font-size:.88rem}}
.pair .bars{{display:flex;flex-direction:column;gap:3px}}
.pair .b{{height:12px;border-radius:3px;display:flex;align-items:center}}
.pair .v{{font-size:.78rem;color:var(--muted);text-align:right;font-variant-numeric:tabular-nums;line-height:1.25;white-space:nowrap}}
.pair .v b{{color:var(--purple)}} .pair .v i{{font-style:normal;color:var(--coral);font-weight:600}}
.legend2{{display:flex;gap:14px;font-size:.8rem;color:var(--muted)}} .legend2 span::before{{content:"";display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px;background:var(--c)}}
.folder{{display:flex;flex-direction:column;gap:12px}}
.folder-head{{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}}
.mgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,430px),1fr));gap:12px}}
.mcard{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:9px;min-width:0}}
.mtop{{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;justify-content:space-between}}
.mname{{font:500 .95rem var(--mono)}}
.mval{{font-size:.8rem;color:var(--muted);display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
.mval b{{color:var(--ink);font-variant-numeric:tabular-nums;background:var(--teal-soft);padding:2px 8px;border-radius:6px}}
.mdesc{{font-size:.9rem;color:var(--muted)}}
pre.dax{{margin:0;padding:11px 13px;border-radius:8px;background:var(--code-bg);font:.8rem/1.6 var(--mono);overflow-x:auto;white-space:pre-wrap;word-break:break-word}}
pre.dax.inline{{padding:6px 9px}}
.k-fn{{color:var(--c-fn);font-weight:500}} .k-str{{color:var(--c-str)}} .k-ref{{color:var(--c-ref)}} .k-num{{color:var(--c-num)}}
.tech{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:12px}}
.tech .panel{{display:flex;flex-direction:column;gap:8px}} .tech p{{font-size:.92rem;color:var(--muted)}}
.issues{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
.issue{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:8px}}
.issue p{{font-size:.92rem;color:var(--muted)}}
.pill{{display:inline-flex;font:600 .7rem/1 var(--body);letter-spacing:.04em;text-transform:uppercase;padding:5px 8px;border-radius:999px;align-self:flex-start}}
.pill.hi{{background:color-mix(in srgb,var(--coral) 16%,transparent);color:var(--coral)}} .pill.md{{background:color-mix(in srgb,var(--amber) 20%,transparent);color:var(--amber)}}
.pill.lo{{background:var(--surface-2);color:var(--muted)}} .pill.ok{{background:var(--teal-soft);color:var(--teal)}}
.check{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}}
.check li{{display:grid;grid-template-columns:22px minmax(0,1fr);gap:10px;font-size:.95rem}}
.check li::before{{content:"✓";display:flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:var(--teal);color:var(--on-accent);font-weight:700;font-size:.8rem}}
.check small{{display:block;color:var(--muted)}}
footer{{font-size:.86rem;color:var(--muted);display:flex;flex-direction:column;gap:4px;border-top:1px solid var(--line);padding-top:18px}}
@media (prefers-reduced-motion:no-preference){{html{{scroll-behavior:smooth}}}}
</style>

<div class="shell">
  <nav class="toc" aria-label="Sumário">
    <div class="brand">Painel de Faltas</div><div class="sub">Documentação técnica · v1.0</div>
    <ol>
      <li><a href="#visao">Visão geral</a></li><li><a href="#arquitetura">Arquitetura</a></li><li><a href="#tabelas">Tabelas e campos</a></li>
      <li><a href="#relacionamentos">Relacionamentos</a></li><li><a href="#logica">Lógica do painel</a></li><li><a href="#medidas">Catálogo de medidas</a></li>
      <li><a href="#calculadas">Colunas calculadas</a></li><li><a href="#tecnicas">Técnicas DAX</a></li><li><a href="#resultados">Resultados atuais</a></li>
      <li><a href="#paginas">Páginas do relatório</a></li><li><a href="#pendencias">Pendências</a></li><li><a href="#historico">Histórico de alterações</a></li>
      <li><a href="#verificacao">Verificação e monitoramento</a></li><li><a href="#fontes">Fontes</a></li>
    </ol>
  </nav>

  <main>
    <header class="hero" id="visao">
      <span class="eyebrow">Documentação técnica · Power BI</span>
      <h1>Painel de faltas em consultas</h1>
      <p class="lede">Modelo semântico e relatório que mostram por que as consultas da rede pública de Vitória (ES) ficam vagas e qual ação tomar com cada consulta da agenda, a partir de um modelo de Machine Learning.</p>
      <div class="meta"><span>Ferramenta <b>Power BI Desktop (.pbip, TMDL)</b></span><span>Cultura <b>{CULTURA}</b></span><span>Dados <b>abr–jun/2016</b></span><span>Gerada em <b>11/10/2026</b></span><span>Autora <b>Jéssica Martins</b></span></div>
      <div class="kpis">
        <div class="kpi k1"><span class="l">Consultas analisadas</span><span class="v">110.514</span><span class="s">{len(NOMES)} tabelas · {n_col} colunas</span></div>
        <div class="kpi k2"><span class="l">Taxa de falta</span><span class="v">20,2%</span><span class="s">22.311 horários vagos</span></div>
        <div class="kpi k3"><span class="l">Medidas DAX</span><span class="v">{n_med}</span><span class="s">{n_calc} colunas calculadas · {len(RELS)} relação</span></div>
        <div class="kpi k4"><span class="l">Economia esperada</span><span class="v">R$ 152 mil</span><span class="s">semana de teste, premissas ilustrativas</span></div>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;gap:10px">
        <h3>Como a agenda da semana de teste foi distribuída entre as ações</h3>
        <div class="stack" role="img" aria-label="Lembrete 34,5%, ligação 34,9%, encaixe 13,1%, reconfirmação 10,3%, nenhuma ação 7,3%">
          <span style="width:7.3%;background:#9AA9B9">7%</span><span style="width:34.5%;background:var(--teal)">Lembrete 34,5%</span>
          <span style="width:34.9%;background:var(--navy)">Ligação 34,9%</span><span style="width:10.3%;background:var(--amber)">10%</span><span style="width:13.0%;background:var(--coral)">Encaixe 13%</span>
        </div>
        <div class="legend"><span><i style="background:#9AA9B9"></i>Nenhuma ação</span><span><i style="background:var(--teal)"></i>Lembrete automático</span><span><i style="background:var(--navy)"></i>Ligação de confirmação</span><span><i style="background:var(--amber)"></i>Reconfirmação obrigatória</span><span><i style="background:var(--coral)"></i>Encaixe (overbooking)</span></div>
      </div>
      <div class="callout"><b>Como esta página foi feita.</b>&nbsp;Um script em Python leu os arquivos do projeto Power BI: tabelas, campos, tipos, fórmulas DAX, relação e consultas vêm direto do modelo. Os valores atuais foram conferidos com consultas DAX executadas no próprio modelo.</div>
    </header>

    <section id="arquitetura">
      <div class="sec-head"><span class="eyebrow">01</span><h2>Arquitetura</h2><p>A lógica pesada fica em Python, onde está testada e documentada nos notebooks. O Power BI recebe dados prontos e só apresenta, o que deixa o modelo leve e fácil de revisar.</p></div>
      <div class="flow">
        <div class="step"><span class="n">1 · ORIGEM</span><b>Base pública</b><span>110.527 agendamentos (Kaggle), em SQLite</span></div>
        <div class="step"><span class="n">2 · PREPARO</span><b>Notebooks 00–06</b><span>SQL, limpeza, modelo de risco e regra de custo</span></div>
        <div class="step"><span class="n">3 · ENTREGA</span><b>3 CSVs + 1 tabela</b><span>separador ; e vírgula decimal</span></div>
        <div class="step key"><span class="n">4 · MODELO</span><b>Power BI</b><span>{len(NOMES)} tabelas · {n_med} medidas · {len(RELS)} relação</span></div>
        <div class="step"><span class="n">5 · CONSUMO</span><b>Relatório publicado</b><span>4 páginas · Publicar na Web</span></div>
      </div>
      <div class="tw"><table><thead><tr><th>Camada</th><th>Ferramenta</th><th>O que faz</th></tr></thead><tbody>
        <tr><td>Dados</td><td>SQLite + pandas</td><td>Modela a base em 3 tabelas e cria a base analítica com funções de janela (faltas anteriores sem vazamento).</td></tr>
        <tr><td>Modelo de ML</td><td>scikit-learn</td><td>Gradient Boosting treinado até 25/05 e testado na semana seguinte; gera o risco de cada consulta.</td></tr>
        <tr><td>Decisão</td><td>Python</td><td>Regra de custo esperado que escolhe a ação de cada consulta.</td></tr>
        <tr><td>Semântica</td><td>Power Query + DAX</td><td>Tipos em pt-BR, relação, medidas e rótulos ordenados.</td></tr>
        <tr><td>Apresentação</td><td>Power BI (PBIR)</td><td>Tema próprio, ícones SVG, filtros por página.</td></tr>
      </tbody></table></div>
    </section>

    <section id="tabelas">
      <div class="sec-head"><span class="eyebrow">02</span><h2>Tabelas e campos</h2><p>Marcadores: <span class="tag pk">PK</span> chave primária, <span class="tag fk">FK</span> chave estrangeira, <span class="tag calc">calculada</span> coluna DAX, <span class="tag hid">oculta</span> escondida do relatório.</p></div>
      {sec_tabelas}
    </section>

    <section id="relacionamentos">
      <div class="sec-head"><span class="eyebrow">03</span><h2>Relacionamentos</h2><p>Uma relação um-para-muitos liga o histórico à agenda. Assim, os filtros de faixa etária e bairro da página da agenda também filtram as consultas da semana de teste.</p></div>
      <div class="panel diagram">{ER}</div>
      <div class="tw"><table><thead><tr><th>De (um)</th><th>Para (muitos)</th><th>Cardinalidade</th><th>Direção do filtro</th><th>Estado</th></tr></thead><tbody>{rel_rows}</tbody></table></div>
    </section>

    <section id="logica">
      <div class="sec-head"><span class="eyebrow">04</span><h2>Lógica do painel</h2><p>O que está por trás dos números, na ordem em que o raciocínio acontece.</p></div>
      <div class="panel" style="display:flex;flex-direction:column;gap:12px">
        <h3>1. A antecedência explica a maior parte das faltas</h3>
        <p class="muted">Taxa de falta por faixa de dias entre o agendamento e a consulta.</p>
        {hbars([('Mesmo dia', .046), ('1 a 2 dias', .227), ('3 a 7 dias', .250), ('8 a 14 dias', .305), ('15 a 30 dias', .326), ('31 a 60 dias', .341), ('61 dias ou mais', .284)], .4)}
      </div>
      <div class="grid2">
        <div class="panel" style="display:flex;flex-direction:column;gap:10px">
          <h3>2. Separação no tempo</h3>
          <p class="muted">O modelo aprende com o passado e é avaliado numa semana que não viu, como aconteceria na prática.</p>
          <div class="stack"><span style="width:68%;background:var(--navy)">Treino · 75.274</span><span style="width:32%;background:var(--coral)">Teste · 35.240</span></div>
          <p class="muted" style="font-size:.82rem;margin-top:6px">Treino: 29/04 a 25/05/2016 · Teste: 30/05 a 08/06/2016</p>
        </div>
        <div class="panel" style="display:flex;flex-direction:column;gap:10px">
          <h3>3. Risco previsto</h3>
          <p class="muted">Gradient Boosting com antecedência, idade, faltas anteriores, bairro e condições de saúde. Ligando para os 20% de maior risco, a equipe encontra 37,7% das faltas, quase o dobro do acaso.</p>
        </div>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;gap:12px">
        <h3>4. Regra de próxima melhor ação</h3>
        <p class="muted">Para cada consulta, com risco previsto <i>p</i> e custo de um horário vago <i>F</i> = R$ 100, calcula-se o custo esperado de cada ação e escolhe-se o menor.</p>
        <div class="formula">custo esperado = custo da ação + p × (1 − redução da falta) × F</div>
        <div class="formula">encaixe = p × F × 20% + (1 − p) × 80% × R$ 50</div>
        <div class="zones">
          <div class="bar"><div style="background:#9AA9B9" title="Nenhuma ação"></div><div style="background:var(--teal)">Lembrete</div><div style="background:var(--navy)">Ligação</div><div style="background:var(--amber)">Reconf.</div><div style="background:var(--coral)">Encaixe (overbooking)</div></div>
          <div class="ticks"><span style="left:0;transform:none">0%</span><span style="left:18%">18%</span><span style="left:33%">33%</span><span style="left:40%">40%</span><span style="left:100%;transform:translateX(-100%)">100%</span></div>
        </div>
        <p class="muted" style="font-size:.84rem">Risco previsto: até 2,5% nenhuma ação · 2,5–18% lembrete · 18–33% ligação · 33–40% reconfirmação · acima de 40% encaixe.</p>
        <div class="callout warn"><b>Premissas ilustrativas.</b>&nbsp;Custos e reduções de falta das ações não foram medidos nesta base. A regra mostra o método; os números precisam vir de um teste A/B.</div>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;gap:12px">
        <h3>5. O paradoxo do SMS</h3>
        <p class="muted">Na base inteira, quem recebeu SMS falta mais (27,6% contra 16,7%). Dentro de cada faixa de antecedência, falta menos. O SMS só foi enviado a partir de 3 dias de antecedência, e não ao acaso: o efeito não é causal.</p>
        <div class="tw"><table><thead><tr><th>Antecedência</th><th class="n">Sem SMS</th><th class="n">Com SMS</th><th class="n">Diferença</th></tr></thead><tbody>
          <tr><td>3 a 7 dias</td><td class="n">26,6%</td><td class="n">23,8%</td><td class="n">−2,8 p.p.</td></tr>
          <tr><td>8 a 14 dias</td><td class="n">33,8%</td><td class="n">28,1%</td><td class="n">−5,7 p.p.</td></tr>
          <tr><td>15 a 30 dias</td><td class="n">36,9%</td><td class="n">29,8%</td><td class="n">−7,1 p.p.</td></tr>
          <tr><td>31 a 60 dias</td><td class="n">38,3%</td><td class="n">31,5%</td><td class="n">−6,8 p.p.</td></tr>
          <tr><td>61 dias ou mais</td><td class="n">33,9%</td><td class="n">25,5%</td><td class="n">−8,4 p.p.</td></tr>
        </tbody></table></div>
      </div>
    </section>

    <section id="medidas">
      <div class="sec-head"><span class="eyebrow">05</span><h2>Catálogo de medidas</h2><p>{n_med} medidas organizadas em pastas. Valor atual: sem nenhum filtro aplicado.</p></div>
      {sec_medidas}
    </section>

    <section id="calculadas">
      <div class="sec-head"><span class="eyebrow">06</span><h2>Colunas calculadas</h2><p>Existem para exibir rótulos limpos e ordená-los do jeito certo nos eixos.</p></div>
      <div class="tw"><table><thead><tr><th>Coluna</th><th>Expressão DAX</th><th>Para que serve</th></tr></thead><tbody>{calc_rows}</tbody></table></div>
    </section>

    <section id="tecnicas">
      <div class="sec-head"><span class="eyebrow">07</span><h2>Técnicas DAX usadas</h2></div>
      <div class="tech">
        <div class="panel"><h3>Taxas como divisão de somas</h3><p>Toda taxa é <code>DIVIDE([Faltas], [Consultas])</code>, nunca média de taxas: o resultado respeita qualquer combinação de filtros e não quebra quando o denominador é zero.</p></div>
        <div class="panel"><h3>CALCULATE com filtro de coluna</h3><p>As versões com e sem SMS e por antecedência reaproveitam a medida base trocando só o filtro, o que mantém uma única definição de "taxa de falta".</p></div>
        <div class="panel"><h3>REMOVEFILTERS para participação</h3><p><code>% da agenda</code> remove o filtro de ação (nas três colunas que a representam) para dividir pelo total da agenda.</p></div>
        <div class="panel"><h3>Ordenação sem dependência circular</h3><p>Uma coluna não pode ser ordenada por outra calculada a partir dela. A saída foi criar cópias de exibição (<code>& ""</code>) ordenadas pelas colunas técnicas.</p></div>
        <div class="panel"><h3>Rótulos limpos com MID</h3><p>Faixas chegam com prefixo numérico ("2 · 3-7 dias") para ordenar; <code>MID(..., 5, 50)</code> exibe só o texto.</p></div>
        <div class="panel"><h3>Filtro de volume no visual</h3><p>O ranking de bairros usa um filtro de nível visual <code>[Consultas] &gt;= 500</code> para não destacar taxas instáveis de bairros pequenos.</p></div>
      </div>
    </section>

    <section id="resultados">
      <div class="sec-head"><span class="eyebrow">08</span><h2>Resultados atuais</h2></div>
      <div class="grid2">
        <div class="panel" style="display:flex;flex-direction:column;gap:12px">
          <h3>Falta pelo histórico do paciente</h3>
          {hbars([('Primeira consulta', .1938), ('Já veio e nunca faltou', .1885), ('Já faltou antes', .2687)], .35)}
          <p class="muted" style="font-size:.88rem">60% das consultas são a primeira do paciente na base (janela de 6 semanas).</p>
        </div>
        <div class="panel" style="display:flex;flex-direction:column;gap:12px">
          <h3>Risco previsto × falta real, por faixa</h3>
          <div class="legend2"><span style="--c:var(--purple)">Previsto</span><span style="--c:var(--coral)">Real</span></div>
          <div class="pair">
            {''.join(f'<span>{l}</span><div class="bars"><div class="b" style="width:{r/0.5*100:.0f}%;background:var(--purple)"></div><div class="b" style="width:{y/0.5*100:.0f}%;background:var(--coral)"></div></div><span class="v"><b>{str(round(r*100,1)).replace(".",",")}%</b><br><i>{str(round(y*100,1)).replace(".",",")}%</i></span>' for l, r, y in [('até 10%', .038, .027), ('10–20%', .165, .167), ('20–30%', .249, .228), ('30–40%', .345, .301), ('acima de 40%', .479, .366)])}
          </div>
          <p class="muted" style="font-size:.88rem">O modelo ordena bem, mas superestima as faixas altas: precisa de recalibração.</p>
        </div>
      </div>
      <div class="tw"><table><thead><tr><th>Ação recomendada</th><th class="n">Consultas</th><th class="n">% da agenda</th><th class="n">Risco previsto</th><th class="n">Falta real</th><th class="n">Economia esperada</th></tr></thead><tbody>
        <tr><td>Nenhuma ação</td><td class="n">2.559</td><td class="n">7,3%</td><td class="n">1,8%</td><td class="n">1,6%</td><td class="n">R$ 0</td></tr>
        <tr><td>Lembrete automático</td><td class="n">12.142</td><td class="n">34,5%</td><td class="n">7,4%</td><td class="n">6,4%</td><td class="n">R$ 5.999</td></tr>
        <tr><td>Ligação de confirmação</td><td class="n">12.299</td><td class="n">34,9%</td><td class="n">25,5%</td><td class="n">23,5%</td><td class="n">R$ 41.565</td></tr>
        <tr><td>Reconfirmação obrigatória</td><td class="n">3.635</td><td class="n">10,3%</td><td class="n">36,5%</td><td class="n">31,3%</td><td class="n">R$ 23.934</td></tr>
        <tr><td>Encaixe (overbooking)</td><td class="n">4.605</td><td class="n">13,1%</td><td class="n">47,9%</td><td class="n">36,6%</td><td class="n">R$ 80.736</td></tr>
        <tr><td><b>Total</b></td><td class="n"><b>35.240</b></td><td class="n"><b>100,0%</b></td><td class="n"><b>21,6%</b></td><td class="n"><b>18,5%</b></td><td class="n"><b>R$ 152.234</b></td></tr>
      </tbody></table></div>
    </section>

    <section id="paginas">
      <div class="sec-head"><span class="eyebrow">09</span><h2>Páginas do relatório</h2></div>
      <div class="tw"><table><thead><tr><th>Página</th><th>Pergunta que responde</th><th>Visuais</th><th>Filtros</th></tr></thead><tbody>
        <tr><td><b>Visão geral</b></td><td>Quanto se falta e onde se concentra?</td><td>4 KPIs, área por dia, colunas por antecedência, rosca por histórico, barras por idade e bairro</td><td>Sexo, faixa etária, bairro, SMS, data</td></tr>
        <tr><td><b>O paradoxo do SMS</b></td><td>O SMS reduz faltas?</td><td>3 KPIs, colunas com e sem SMS por faixa, linha de quem recebe SMS, nota</td><td>Sexo, faixa etária, bairro, histórico</td></tr>
        <tr><td><b>Agenda da semana</b></td><td>O que fazer com cada consulta?</td><td>5 KPIs, rosca por ação, combinado consultas × falta real por faixa, tabela por ação, nota</td><td>Ação, faixa de risco, faixa etária, bairro, data</td></tr>
        <tr><td><b>Premissas e modelo</b></td><td>Em que premissas e modelo isso se apoia?</td><td>4 KPIs, tabelas de premissas e modelos, regra e limitações</td><td>—</td></tr>
      </tbody></table></div>
    </section>

    <section id="pendencias">
      <div class="sec-head"><span class="eyebrow">10</span><h2>Pendências e pontos de atenção</h2></div>
      <div class="issues">
        <div class="issue"><span class="pill hi">Alta</span><h3>Premissas não medidas</h3><p>A economia depende de custos e efeitos ilustrativos. Validar com um teste A/B antes de usar a regra de verdade.</p></div>
        <div class="issue"><span class="pill hi">Alta</span><h3>Calibração do risco</h3><p>Nas faixas acima de 30% o risco previsto passa da falta real. Recalibrar com dados recentes antes de decidir encaixes.</p></div>
        <div class="issue"><span class="pill md">Média</span><h3>Caminho fixo dos arquivos</h3><p>As consultas apontam para <code>D:\\Projetos IA\\Projeto 2 Saude\\powerbi\\</code>. Trocar por um parâmetro do Power Query.</p></div>
        <div class="issue"><span class="pill md">Média</span><h3>Tabela Modelos digitada</h3><p>Métricas copiadas dos notebooks 03 e 04. Se os modelos forem retreinados, atualizar ou passar a ler um CSV.</p></div>
        <div class="issue"><span class="pill lo">Baixa</span><h3>Visuais ocultos antigos</h3><p>14 visuais vazios e ocultos da primeira versão do layout. Podem ser apagados no painel Seleção.</p></div>
        <div class="issue"><span class="pill lo">Baixa</span><h3>Encaixe tem custo humano</h3><p>Em saúde pública, só faz sentido com fila de espera ativa e limite de encaixes por turno.</p></div>
      </div>
    </section>

    <section id="historico">
      <div class="sec-head"><span class="eyebrow">11</span><h2>Histórico de alterações</h2></div>
      <div class="tw"><table><thead><tr><th>Data</th><th>Versão</th><th>Alteração</th></tr></thead><tbody>
        <tr><td>11/10/2026</td><td>0.1</td><td>Modelo criado: 4 tabelas, relação Consultas → Agenda, 17 medidas e colunas de ordenação.</td></tr>
        <tr><td>11/10/2026</td><td>0.2</td><td>Primeiro layout de 4 páginas.</td></tr>
        <tr><td>11/10/2026</td><td>1.0</td><td>Tema próprio, ícones SVG, cards coloridos, filtros por página; relatório publicado na web.</td></tr>
      </tbody></table></div>
    </section>

    <section id="verificacao">
      <div class="sec-head"><span class="eyebrow">12</span><h2>Verificação e monitoramento</h2></div>
      <div class="grid2">
        <div class="panel" style="display:flex;flex-direction:column;gap:12px"><h3>Checklist de verificação</h3><ul class="check">
          <li><span>Totais de consultas e faltas<small>DAX no modelo = notebook 02: 110.514 e 22.311.</small></span></li>
          <li><span>Taxas de falta com e sem SMS<small>DAX = notebook 01: 27,6% e 16,7%.</small></span></li>
          <li><span>Agenda e risco médio<small>DAX = notebook 03: 35.240 consultas, 21,6% de risco.</small></span></li>
          <li><span>Economia esperada<small>DAX = notebook 06: R$ 152.234.</small></span></li>
          <li><span>Estrutura documentada<small>Lida dos arquivos TMDL pelo script, sem digitação manual.</small></span></li>
        </ul></div>
        <div class="panel" style="display:flex;flex-direction:column;gap:12px"><h3>Quando atualizar</h3><ul class="check">
          <li><span>Novos dados<small>Rodar os notebooks 00–06, trocar os CSVs e clicar em Atualizar.</small></span></li>
          <li><span>Mudança de premissas<small>Ajustar em src/apoio.py, rodar o notebook 05 e o 06.</small></span></li>
          <li><span>Modelo retreinado<small>Atualizar a tabela Modelos e a seção Resultados.</small></span></li>
          <li><span>Mudança no modelo do Power BI<small>Rodar de novo o gerar_documentacao.py.</small></span></li>
        </ul></div>
      </div>
    </section>

    <section id="fontes">
      <div class="sec-head"><span class="eyebrow">13</span><h2>Fontes</h2></div>
      <ul class="check">
        <li><span><a href="https://www.kaggle.com/datasets/joniarroba/noshowappointments" target="_blank" rel="noopener">Medical Appointment No Shows</a><small>Kaggle · Joni Hoppen e Aquarela Analytics · CC BY-NC-SA 4.0</small></span></li>
        <li><span><a href="https://github.com/jessicapmartins/previsao-faltas-consultas" target="_blank" rel="noopener">Repositório do projeto</a><small>Notebooks 00–06, src/apoio.py e o script desta documentação</small></span></li>
        <li><span><a href="https://app.powerbi.com/view?r=eyJrIjoiODA0MjQyYzYtNTMwOC00ZGM0LTgxYjUtOTMyMzY2ZjBhNjYzIiwidCI6IjU4NTQwODYwLTQzNDgtNDQwMC05NjI3LTlmMTA4MWNiYWFjMiJ9" target="_blank" rel="noopener">Painel publicado</a><small>Power BI · Publicar na Web</small></span></li>
      </ul>
    </section>

    <footer><span>Documentação gerada a partir do modelo por <code>docs/gerar_documentacao.py</code>.</span><span>Projeto autoral de Jéssica Martins.</span></footer>
  </main>
</div>

<script>
(function(){{
  var links=[].slice.call(document.querySelectorAll('.toc a')), map={{}};
  links.forEach(function(a){{map[a.getAttribute('href').slice(1)]=a;}});
  if(!('IntersectionObserver' in window))return;
  var io=new IntersectionObserver(function(es){{es.forEach(function(en){{if(en.isIntersecting){{links.forEach(function(l){{l.classList.remove('on');}});var a=map[en.target.id];if(a)a.classList.add('on');}}}});}},{{rootMargin:'-20% 0px -70% 0px'}});
  Object.keys(map).forEach(function(id){{var el=document.getElementById(id);if(el)io.observe(el);}});
}})();
</script>
'''
open(OUT, 'w', encoding='utf-8').write(PAGE)
print('ok', OUT, f'{len(NOMES)} tabelas, {n_col} colunas, {n_med} medidas, {n_calc} calculadas, {len(RELS)} relação')
