#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERTA — Painel Operacional do Supervisor v7.9
Base: BASEBOT.csv + VIP (repetida/infância) do GitHub (SalaGpon/Berta-bot)
Telas: Diário | Produção | Repetidos (VIP) | Infância (VIP) | Calendário | Qualidade
"""

import re
import io
import time
import random
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import streamlit as st
import traceback

# =============================================================================
# LIMPAR CACHE AO INICIAR
# =============================================================================

if "cache_cleared" not in st.session_state:
    st.cache_data.clear()
    st.session_state.cache_cleared = True

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    layout="wide",
    page_title="BERTA - Painel Operacional",
    page_icon="📡",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 2. CSS GLOBAL (mantido igual ao original)
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body { margin: 0; padding: 0; }
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="block-container"],
.main, .block-container, section.main > div, div[data-testid="stVerticalBlock"] {
    background-color: #f5f7fa !important; color: #1a2332 !important;
}
[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #dde3ed !important; }
[data-testid="stSidebar"] * { color: #1a2332 !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div {
    background-color: #ffffff !important; border-color: #dde3ed !important;
}
.stButton > button { background-color: #1e3a5f !important; color: #ffffff !important; }
.kpi-card { background: #ffffff; border: 1px solid #dde3ed; border-radius: 10px; padding: 16px 14px;
    text-align: center; position: relative; box-shadow: 0 1px 4px rgba(0,0,0,0.05); min-height: 100px; }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent, #1e3a5f); }
.kpi-label { font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 6px; }
.kpi-value { font-family: 'JetBrains Mono', monospace !important; font-size: 26px; font-weight: 700; color: #1a2332; }
.kpi-sub { font-size: 10px; color: #94a3b8; margin-top: 5px; }
.kpi-blue   { --accent: #1e3a5f; }
.kpi-green  { --accent: #16a34a; }
.kpi-yellow { --accent: #d97706; }
.kpi-red    { --accent: #dc2626; }
.kpi-purple { --accent: #7c3aed; }
.sec { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #1e3a5f;
    border-left: 3px solid #1e3a5f; padding-left: 10px; margin: 22px 0 10px 0; }
.ph { display: flex; align-items: center; gap: 10px; padding: 12px 0 18px 0; border-bottom: 1px solid #dde3ed; margin-bottom: 18px; }
.ph h1 { font-size: 20px; font-weight: 700; color: #1a2332; margin: 0; }
.badge { background: #e8f0fa; border: 1px solid #bdd0ea; color: #1e3a5f; font-size: 10px;
    font-weight: 700; padding: 3px 10px; border-radius: 20px; text-transform: uppercase; }
.badge-sup { background: #f0f4f8; border-color: #cbd5e1; color: #475569; }
.qualidade-table { width: 100%; border-collapse: collapse; font-size: 13px; background: #ffffff;
    border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
.qualidade-table th { background: #f8fafc; border-bottom: 2px solid #dde3ed; padding: 10px;
    text-align: left; font-weight: 600; color: #475569; }
.qualidade-table td { padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }
.qualidade-table tr:hover td { background: #f8fafc; }
.info-box { background: #e8f0fa; border: 1px solid #bdd0ea; border-radius: 6px;
    padding: 10px 14px; margin-bottom: 12px; font-size: 12px; color: #1e3a5f; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 3. CONSTANTES
# =============================================================================

GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = "SalaGpon/Berta-bot"
BASE_CSV = "BASEBOT.csv"
VIP_FOLDER = "bases/bucket/VIP"

ROYAL = "#1e3a5f"
ROYAL_LIGHT = "#4a7db5"

_LYT = dict(
    paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
    font=dict(family="Inter, sans-serif", color="#475569", size=12),
    margin=dict(l=40, r=20, t=44, b=36),
    xaxis=dict(gridcolor="#e8edf3", linecolor="#e8edf3", zeroline=False),
    yaxis=dict(gridcolor="#e8edf3", linecolor="#e8edf3", zeroline=False),
    legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor="#e8edf3", borderwidth=1),
)

_ESTADO_MAP = {
    'CONCLUIDO COM SUCESSO':  'CONCLUÍDO COM SUCESSO',
    'CONCLUIDO SEM SUCESSO':  'CONCLUÍDO SEM SUCESSO',
    'NAO ATRIBUIDO':          'NÃO ATRIBUÍDO',
    'ATRIBUIDO':              'ATRIBUÍDO',
    'EM EXECUCAO':            'EM EXECUÇÃO',
    'CANCELADO':              'CANCELADO',
    'RECEBIDO':               'RECEBIDO',
    'EM DESLOCAMENTO':        'EM DESLOCAMENTO',
}

# =============================================================================
# 4. FUNÇÕES DE CARREGAMENTO (BASEBOT + VIP)
# =============================================================================

def carregar_base_github(file_path, sep=";", dtype=str):
    """Baixa um arquivo CSV do GitHub usando token."""
    if not GITHUB_TOKEN:
        return None
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    cache_buster = f"{int(time.time())}_{random.randint(10000, 99999)}"
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{file_path}?v={cache_buster}"
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text), sep=sep, dtype=dtype, low_memory=False)
            df.columns = df.columns.str.strip()
            return df
    except Exception:
        pass
    return None

def carregar_basebot():
    """Carrega o BASEBOT.csv."""
    return carregar_base_github(BASE_CSV, sep=";")

def carregar_vip_repetida(mes_ref):
    """Carrega o arquivo VIP de repetidos para o mês informado (ex: '2026-04')."""
    ano_mes = mes_ref.replace("-", "_")
    # padrão do nome: 2026_04_ANL_FTTH_REPETIDA_30_DIAS000000000000.csv
    padrao = f"{ano_mes}_ANL_FTTH_REPETIDA_30_DIAS"
    # Tentamos listar os arquivos via API do GitHub (mas é mais simples tentar padrão com 000...)
    # Vamos tentar algumas variações (0, 1, 2 zeros...). Normalmente é 12 zeros.
    for zeros in ["000000000000", "00000000000", "0000000000"]:
        nome = f"{padrao}{zeros}.csv"
        caminho = f"{VIP_FOLDER}/{nome}"
        df = carregar_base_github(caminho, sep=",", dtype=str)
        if df is not None:
            return df
    return None

def carregar_vip_infancia(mes_ref):
    """Carrega o arquivo VIP de infância para o mês informado."""
    ano_mes = mes_ref.replace("-", "_")
    padrao = f"{ano_mes}_ANL_FTTH_INFANCIA_30_DIAS"
    for zeros in ["000000000000", "00000000000", "0000000000"]:
        nome = f"{padrao}{zeros}.csv"
        caminho = f"{VIP_FOLDER}/{nome}"
        df = carregar_base_github(caminho, sep=",", dtype=str)
        if df is not None:
            return df
    return None

def normalizar_gpon(gpon):
    if pd.isna(gpon) or not gpon:
        return ""
    return str(gpon).strip().upper()

@st.cache_data(ttl=300)
def carregar_todas_bases(mes_ref):
    """Carrega BASEBOT, VIP repetida e VIP infância para o mês."""
    df_base = carregar_basebot()
    df_vip_rep = carregar_vip_repetida(mes_ref)
    df_vip_inf = carregar_vip_infancia(mes_ref)
    if df_base is None:
        st.error("❌ Não foi possível carregar BASEBOT.csv")
        return None, None, None
    return df_base, df_vip_rep, df_vip_inf

def processar_basebot(df):
    """Normaliza o BASEBOT (datas, estados, códigos)."""
    df = df.copy()
    if 'DH_FIM_EXEC_REAL' in df.columns:
        df['FIM_DT'] = pd.to_datetime(df['DH_FIM_EXEC_REAL'], dayfirst=True, errors='coerce')
        df['DIA_FIM'] = df['FIM_DT'].dt.date
        df['MES_FIM'] = df['FIM_DT'].dt.to_period('M')
        df['ANO_FIM'] = df['FIM_DT'].dt.year.astype('Int64')
        df['SEM_FIM'] = df['FIM_DT'].dt.isocalendar().week.astype('Int64')
    else:
        df['FIM_DT'] = pd.NaT
        df['DIA_FIM'] = None

    if 'AB_BA' in df.columns:
        df['AB_DT'] = pd.to_datetime(df['AB_BA'], dayfirst=True, errors='coerce')
        df['DIA_AB'] = df['AB_DT'].dt.date
    else:
        df['AB_DT'] = pd.NaT

    if 'INICIO_AG' in df.columns:
        df['INICIO_AG_DT'] = pd.to_datetime(df['INICIO_AG'], dayfirst=True, errors='coerce')
    else:
        df['INICIO_AG_DT'] = pd.NaT

    if 'ESTADO' in df.columns:
        df['ESTADO_NORM'] = df['ESTADO'].astype(str).str.strip().str.upper()
        df['ESTADO_NORM'] = df['ESTADO_NORM'].replace(_ESTADO_MAP)
    else:
        df['ESTADO_NORM'] = ''

    if 'MACRO' in df.columns:
        df['MACRO_NORM'] = df['MACRO'].astype(str).str.strip().str.upper()
    else:
        df['MACRO_NORM'] = ''

    if 'TR' in df.columns:
        df['COD_TEC'] = df['TR'].astype(str).str.strip().str.upper()
    else:
        df['COD_TEC'] = ''

    if 'NOME_FUNC' in df.columns and df['NOME_FUNC'].notna().any():
        df['NOME_TEC'] = df['NOME_FUNC'].astype(str).str.strip().str.title()
    elif 'TECNICO_EXECUTOR' in df.columns:
        df['NOME_TEC'] = df['TECNICO_EXECUTOR'].apply(
            lambda x: str(x).split(' - ')[0].strip().title() if pd.notna(x) else ""
        )
    else:
        df['NOME_TEC'] = ""

    mes_col = next((c for c in ['MÊS', 'MES', 'Mês', 'Mes', 'mês', 'mes'] if c in df.columns), None)
    if mes_col:
        df['MES_REF'] = df[mes_col].astype(str).str.strip()
    elif not df['FIM_DT'].isna().all():
        df['MES_REF'] = df['FIM_DT'].dt.strftime('%Y-%m').fillna('')
    else:
        df['MES_REF'] = ''

    for flag in ['FLAG_REPETIDO', 'FLAG_INFANCIA', 'ALARMADO', 'PZERO_10H', 'PZERO_15H']:
        if flag not in df.columns:
            df[flag] = 'NAO'
        else:
            df[flag] = df[flag].fillna('NAO').replace({'': 'NAO'}).astype(str).str.upper()

    if 'TEC_ANTERIOR' not in df.columns:
        df['TEC_ANTERIOR'] = pd.NA
    if 'GPON' not in df.columns:
        df['GPON'] = pd.NA
    if 'TERRITORIO' not in df.columns:
        df['TERRITORIO'] = ''

    if not df['FIM_DT'].isna().all():
        ultima_data = df['FIM_DT'].max().strftime('%d/%m/%Y %H:%M')
    elif not df['AB_DT'].isna().all():
        ultima_data = df['AB_DT'].max().strftime('%d/%m/%Y %H:%M')
    else:
        ultima_data = 'N/A'

    return df, ultima_data

# =============================================================================
# 5. HELPERS
# =============================================================================

def _endereco_completo(row):
    parts = []
    logr = row.get("LOGRADOURO", "")
    if logr and pd.notna(logr) and str(logr).strip():
        parts.append(str(logr).strip())
    num = row.get("NUMERO", "")
    if num and pd.notna(num) and str(num).strip() and str(num).strip() != "0":
        parts.append(str(num).strip())
    bairro = row.get("BAIRRO", "")
    if bairro and pd.notna(bairro) and str(bairro).strip():
        parts.append(str(bairro).strip())
    cidade = row.get("CIDADE", "")
    if cidade and pd.notna(cidade) and str(cidade).strip():
        parts.append(str(cidade).strip())
    return ", ".join(parts) if parts else "Endereço não disponível"

def _kpi(label, valor, sub="", cls="kpi-blue"):
    s = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f'<div class="kpi-card {cls}"><div class="kpi-label">{label}</div><div class="kpi-value">{valor}</div>{s}</div>'

def _sec(txt):
    st.markdown(f'<div class="sec">{txt}</div>', unsafe_allow_html=True)

def _header(icone, titulo, f):
    mes = f.get("mes", "")
    sup = f.get("supervisor", "")
    sup_b = f'<span class="badge badge-sup">👑 {sup}</span>' if sup else ""
    st.markdown(f'<div class="ph"><h1>{icone} {titulo}</h1><span class="badge">{mes}</span>{sup_b}</div>', unsafe_allow_html=True)

def _lyt(titulo="", h=360):
    return {**_LYT, "height": h, "title": dict(text=titulo, font=dict(size=13, color="#1a2332"), x=0.01)}

def _bar_h(y, x, color, titulo="", h=340, labels=None):
    fig = go.Figure(go.Bar(x=x, y=y, orientation="h", marker_color=color, text=labels, textposition="inside", textfont_color="white"))
    fig.update_layout(**_lyt(titulo, h))
    fig.update_layout(yaxis_autorange="reversed")
    return fig

# =============================================================================
# 6. SIDEBAR / FILTROS (extrai meses do BASEBOT)
# =============================================================================

def sidebar(df_base, ultima_data):
    with st.sidebar:
        st.markdown('<div style="text-align:center;padding:18px 0 10px"><div style="font-size:22px;font-weight:800;color:#1e3a5f;letter-spacing:2px">📡 BERTA</div><div style="font-size:10px;color:#64748b;font-weight:600">PAINEL OPERACIONAL</div></div>', unsafe_allow_html=True)
        st.divider()
        tela = st.radio("Tela", ["📅 Diario", "📊 Producao Diaria", "🔁 Repetidos", "👶 Infancia", "📆 Calendario", "🏆 Qualidade"], label_visibility="collapsed", key="nav")
        st.divider()
        st.markdown("**Filtros**")
        todos_meses = sorted(df_base["MES_REF"].dropna().replace('', pd.NA).dropna().unique(), reverse=True)
        if not todos_meses:
            st.warning("Nenhum mês disponível na base.")
            return {}
        mes_atual = datetime.now().strftime("%Y-%m")
        mes_idx = todos_meses.index(mes_atual) if mes_atual in todos_meses else 0
        mes = st.selectbox("📅 Mes", todos_meses, index=mes_idx, key="f_mes")
        # Supervisores e equipes (apenas para filtro, não afeta VIPs)
        equipes = {}
        if "SUPERVISOR" in df_base.columns and "TR" in df_base.columns:
            for _, row in df_base.iterrows():
                sup = str(row.get("SUPERVISOR", "")).strip()
                if sup and sup.upper() not in ("", "NAN", "NONE"):
                    tr = str(row.get("TR", "")).strip().upper()
                    if tr and tr not in ("NAN", ""):
                        equipes.setdefault(sup, set()).add(tr)
        equipes = {k: list(v) for k, v in equipes.items()}
        sups_originais = sorted(equipes.keys())
        sup_selecionado = st.selectbox("👑 Supervisor", ["— Todos —"] + sups_originais, key="f_sup") if sups_originais else "— Todos —"
        tecs_sup = equipes.get(sup_selecionado, []) if sup_selecionado != "— Todos —" else []
        terrs = sorted(df_base["TERRITORIO"].dropna().replace('', pd.NA).dropna().unique())
        terr = st.multiselect("📍 Territorio", terrs, key="f_terr")
        pool = [t for t in tecs_sup if t in df_base["COD_TEC"].values] if tecs_sup else sorted(df_base["COD_TEC"].dropna().unique())
        tec = st.multiselect("👤 Tecnico", pool, key="f_tec")
        st.divider()
        st.markdown(f'<div class="info-box">📅 Último registro na base:<br><strong>{ultima_data}</strong></div>', unsafe_allow_html=True)
        if st.button("🔄 Recarregar base", use_container_width=True):
            st.cache_data.clear()
            st.session_state.clear()
            st.rerun()
    return {"tela": tela, "mes": mes, "supervisor": sup_selecionado if sup_selecionado != "— Todos —" else "", "tecs_sup": tecs_sup, "territorios": terr, "tecnicos": tec}

def _filtrar(df, f):
    r = df[df["MES_REF"] == f["mes"]].copy()
    if f["tecs_sup"]:
        r = r[r["COD_TEC"].isin(f["tecs_sup"])]
    if f["territorios"] and "TERRITORIO" in r.columns:
        r = r[r["TERRITORIO"].isin(f["territorios"])]
    if f["tecnicos"]:
        r = r[r["COD_TEC"].isin(f["tecnicos"])]
    return r

def _escopo(df, f):
    if f["tecs_sup"]:
        return df[df["COD_TEC"].isin(f["tecs_sup"])].copy()
    return df

# =============================================================================
# 7. TELAS (com base VIP para repetidos/infância)
# =============================================================================

def tela_diario(df, f):
    _header("📅", "Controle do Dia", f)
    df_mes = df[df["MES_REF"] == f["mes"]].copy()
    datas = sorted(df_mes["FIM_DT"].dropna().dt.date.unique(), reverse=True)
    if not datas:
        st.warning(f"Nenhuma atividade concluída no mês {f['mes']}.")
        return
    dia_sel = st.date_input("Data de referência", value=datas[0], min_value=datas[-1], max_value=datas[0], key="dia_ref")
    atividades_dia = df_mes[df_mes["FIM_DT"].dt.date == dia_sel].copy()
    concluidas = atividades_dia[atividades_dia["ESTADO_NORM"] == "CONCLUÍDO COM SUCESSO"]
    sem_sucesso = atividades_dia[atividades_dia["ESTADO_NORM"] == "CONCLUÍDO SEM SUCESSO"]
    canceladas = atividades_dia[atividades_dia["ESTADO_NORM"] == "CANCELADO"]
    abertas = df_mes[((df_mes["AB_DT"].dt.date == dia_sel) | (df_mes["INICIO_AG_DT"].dt.date == dia_sel)) & (df_mes["FIM_DT"].isna()) & (~df_mes["ESTADO_NORM"].isin(["CONCLUÍDO COM SUCESSO", "CONCLUÍDO SEM SUCESSO", "CANCELADO"]))].copy()
    total_concluidas = len(concluidas)
    total_pendencias = len(sem_sucesso)
    tecs_ativos = concluidas["COD_TEC"].nunique()
    efic = round(total_concluidas / (total_concluidas + total_pendencias) * 100, 1) if (total_concluidas + total_pendencias) > 0 else 0
    cols = st.columns(5)
    for col, (lb, vl, sb, cl) in zip(cols, [("Concluídos", f"{total_concluidas}", "c/ sucesso", "kpi-blue"), ("Eficácia", f"{efic}%", "suc/total", "kpi-green" if efic >= 85 else "kpi-yellow"), ("Sem Sucesso", f"{total_pendencias}", "pendências", "kpi-red" if total_pendencias > 0 else "kpi-green"), ("Cancelados", f"{len(canceladas)}", "cancelados", "kpi-yellow"), ("Técnicos", f"{tecs_ativos}", "com atividade", "kpi-blue")]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")
    if not concluidas.empty:
        _sec("✅ ATIVIDADES CONCLUÍDAS COM SUCESSO")
        prod_tec = concluidas.groupby("COD_TEC").agg(Nome=("NOME_TEC", lambda x: x.iloc[0] if not x.empty else ""), Total=("SA", "count"), INST=("MACRO_NORM", lambda x: (x == "INST-FTTH").sum()), REP=("MACRO_NORM", lambda x: (x == "REP-FTTH").sum())).reset_index()
        prod_tec = prod_tec.sort_values("Total", ascending=False).reset_index(drop=True).rename(columns={"COD_TEC": "TR"})
        st.dataframe(prod_tec, use_container_width=True, hide_index=True)
        with st.expander("📋 Ver lista detalhada"):
            cols_detalhe = ["SA", "MACRO", "COD_TEC", "NOME_TEC", "LOGRADOURO", "NUMERO", "BAIRRO", "CIDADE", "DESCRICAO"]
            cols_exist = [c for c in cols_detalhe if c in concluidas.columns]
            if cols_exist:
                st.dataframe(concluidas[cols_exist], use_container_width=True, hide_index=True)
    if not abertas.empty:
        _sec("🔄 ATIVIDADES EM ABERTO (NÃO CONCLUÍDAS)")
        abertas = abertas.sort_values(["AB_DT", "INICIO_AG_DT"])
        cols_aberto = ["SA", "MACRO", "COD_TEC", "NOME_TEC", "ESTADO", "LOGRADOURO", "NUMERO", "BAIRRO", "CIDADE"]
        cols_aberto_exist = [c for c in cols_aberto if c in abertas.columns]
        if cols_aberto_exist:
            st.dataframe(abertas[cols_aberto_exist], use_container_width=True, hide_index=True)
    if not sem_sucesso.empty:
        _sec("⚠️ PENDÊNCIAS (CONCLUÍDOS SEM SUCESSO)")
        cols_ss = [c for c in ["SA", "MACRO", "COD_TEC", "COD_FECHAMENTO", "DESCRICAO"] if c in sem_sucesso.columns]
        st.dataframe(sem_sucesso[cols_ss], use_container_width=True, hide_index=True)
    if atividades_dia.empty and abertas.empty:
        st.info("📭 Nenhuma atividade registrada para esta data.")

def tela_calendario(df, f):
    import calendar as _cal
    _header("📆", "Calendário Mensal", f)
    mes_str = f["mes"]
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        st.error("Mês inválido.")
        return
    hoje = datetime.now()
    dias_mes = _cal.monthrange(ano, mes)[1]
    dia_max = hoje.day if (ano == hoje.year and mes == hoje.month) else dias_mes
    dias_range = list(range(1, dia_max + 1))
    meses_pt = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    lbl_mes = f"{meses_pt[mes-1]}/{ano}"
    df_valido = df.dropna(subset=["FIM_DT"])
    df_mes = df_valido[(df_valido["FIM_DT"].dt.year == ano) & (df_valido["FIM_DT"].dt.month == mes)].copy()
    df_mes["DIA"] = df_mes["FIM_DT"].dt.day.astype(int)
    suc_m = df_mes[df_mes["ESTADO_NORM"] == "CONCLUÍDO COM SUCESSO"]
    semsuc_m = df_mes[df_mes["ESTADO_NORM"] == "CONCLUÍDO SEM SUCESSO"]
    if suc_m.empty:
        st.warning(f"Nenhuma atividade concluída com sucesso em {lbl_mes}.")
        return
    tecs = suc_m["COD_TEC"].nunique()
    total_concluidas = len(suc_m)
    inst_count = (suc_m["MACRO_NORM"] == "INST-FTTH").sum()
    rep_count = (suc_m["MACRO_NORM"] == "REP-FTTH").sum()
    outros_count = total_concluidas - inst_count - rep_count
    cols = st.columns(5)
    for col, (lb, vl, sb, cl) in zip(cols, [("Técnicos Ativos", f"{tecs}", lbl_mes, "kpi-blue"), ("Total Concluídos", f"{total_concluidas:,}", "c/ sucesso", "kpi-blue"), ("INST", f"{inst_count:,}", "Instalações", "kpi-blue"), ("REP", f"{rep_count:,}", "Reparos", "kpi-purple"), ("Outros", f"{outros_count:,}", "MUD/Outros", "kpi-yellow")]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")
    suc_range = suc_m[suc_m["DIA"].isin(dias_range)]
    if suc_range.empty:
        st.warning("Nenhuma atividade no período selecionado.")
        return
    pivot = suc_range.groupby(["COD_TEC", "DIA"]).size().unstack(fill_value=0)
    for d in dias_range:
        if d not in pivot.columns:
            pivot[d] = 0
    pivot = pivot[dias_range]
    nomes = suc_m.groupby("COD_TEC")["NOME_TEC"].first().fillna("").apply(lambda x: x.title() if x else "")
    ss_tec = semsuc_m.groupby("COD_TEC").size().reindex(pivot.index, fill_value=0)
    dias_trab = suc_range.groupby("COD_TEC")["DIA"].nunique().reindex(pivot.index, fill_value=0)
    pivot.insert(0, "Nome", nomes)
    pivot["Total"] = pivot[dias_range].sum(axis=1)
    pivot["Sem Suc."] = ss_tec.values
    pivot["Dias"] = dias_trab.values
    pivot["Media"] = (pivot["Total"] / pivot["Dias"].replace(0, 1)).round(1)
    pivot["Eficácia%"] = (pivot["Total"] / (pivot["Total"] + pivot["Sem Suc."]).replace(0, 1) * 100).round(1)
    pivot = pivot.sort_values("Total", ascending=False).reset_index().rename(columns={"COD_TEC": "TR"})
    cols_order = ["Nome", "TR"] + dias_range + ["Dias", "Total", "Sem Suc.", "Media", "Eficácia%"]
    pivot = pivot[cols_order]
    def _cor_cel(v):
        try:
            v = int(v)
        except: return ""
        if v >= 8: return "background-color:#7c3aed;color:white;font-weight:700;text-align:center"
        if v in (6,7): return "background-color:#000000;color:white;font-weight:700;text-align:center"
        if v == 5: return "background-color:#1e40af;color:white;font-weight:700;text-align:center"
        if v == 4: return "background-color:#d4edda;color:#155724;font-weight:600;text-align:center"
        if v == 3: return "background-color:#fff3cd;color:#856404;font-weight:600;text-align:center"
        if v in (1,2): return "background-color:#ffcccc;color:#721c24;text-align:center"
        return "background-color:#f0f0f0;color:#adb5bd;text-align:center"
    styled = pivot.style.map(_cor_cel, subset=dias_range)
    altura_total = 38 + (len(pivot) * 35)
    st.dataframe(styled, use_container_width=True, hide_index=True, height=altura_total)

def tela_producao(dm, ds, f):
    _header("📊", "Produção Diária", f)
    suc = dm[dm["ESTADO_NORM"] == "CONCLUÍDO COM SUCESSO"]
    conc = dm[dm["ESTADO_NORM"].isin(["CONCLUÍDO COM SUCESSO", "CONCLUÍDO SEM SUCESSO"])]
    inst = suc[suc["MACRO_NORM"] == "INST-FTTH"]
    rep = suc[suc["MACRO_NORM"] == "REP-FTTH"]
    dias = suc["DIA_FIM"].nunique()
    efic = round(len(suc) / len(conc) * 100, 1) if len(conc) > 0 else 0
    med = round(len(suc) / dias, 1) if dias > 0 else 0
    cols = st.columns(6)
    for col, (lb, vl, sb, cl) in zip(cols, [("Concluídos", f"{len(suc):,}", "c/ sucesso", "kpi-blue"), ("Eficácia", f"{efic}%", "suc/total", "kpi-green" if efic>=85 else "kpi-yellow" if efic>=70 else "kpi-red"), ("Instalações", f"{len(inst):,}", "INST-FTTH", "kpi-blue"), ("Reparos", f"{len(rep):,}", "REP-FTTH", "kpi-purple"), ("Dias Trab.", f"{dias}", "c/ encerramento", "kpi-blue"), ("Média/Dia", f"{med}", "atividades/dia", "kpi-blue")]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")
    _sec("Produção por Dia")
    if not suc.empty:
        prod = suc.groupby("DIA_FIM").agg(Total=("SA", "count"), Inst=("MACRO_NORM", lambda x: (x == "INST-FTTH").sum()), Rep=("MACRO_NORM", lambda x: (x == "REP-FTTH").sum())).reset_index()
        sem_suc = dm[dm["ESTADO_NORM"] == "CONCLUÍDO SEM SUCESSO"]
        if not sem_suc.empty:
            ss = sem_suc.groupby("DIA_FIM").size().reset_index(name="SS")
            prod = prod.merge(ss, on="DIA_FIM", how="left")
        else:
            prod["SS"] = 0
        prod["SS"] = prod["SS"].fillna(0).astype(int)
        prod["Efic%"] = (prod["Total"] / (prod["Total"] + prod["SS"]) * 100).round(1)
        prod["Dia"] = pd.to_datetime(prod["DIA_FIM"]).dt.strftime("%d/%m")
        fig = go.Figure()
        fig.add_bar(x=prod["Dia"], y=prod["Inst"], name="INST", marker_color=ROYAL)
        fig.add_bar(x=prod["Dia"], y=prod["Rep"], name="REP", marker_color=ROYAL_LIGHT)
        fig.update_layout(barmode="stack", showlegend=True, **_lyt("Produção Diária - INST + REP", 320))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(prod[["Dia","Total","Inst","Rep","SS","Efic%"]].rename(columns={"Inst":"INST","Rep":"REP","SS":"Sem Suc.","Efic%":"Eficácia%"}), use_container_width=True, hide_index=True)
    _sec("Pareto de Técnicos")
    pt = suc.groupby(["COD_TEC","NOME_TEC"]).size().reset_index(name="Prod")
    pt = pt.sort_values("Prod", ascending=False).reset_index(drop=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top 5 — Maior Produção**")
        t5 = pt.head(5)
        if not t5.empty:
            st.plotly_chart(_bar_h(t5["NOME_TEC"], t5["Prod"], ROYAL, labels=t5["COD_TEC"], h=260), use_container_width=True)
    with c2:
        st.markdown("**Top 5 — Menor Produção**")
        b5 = pt.tail(5).sort_values("Prod")
        if not b5.empty:
            st.plotly_chart(_bar_h(b5["NOME_TEC"], b5["Prod"], ROYAL_LIGHT, labels=b5["COD_TEC"], h=260), use_container_width=True)

def tela_repetidos_vip(df_base, df_vip_rep, f):
    """Tela de repetidos usando a base VIP (oficial)."""
    _header("🔁", "Repetidos (VIP Oficial)", f)
    if df_vip_rep is None:
        st.error("❌ Base VIP de repetidos não disponível para o mês selecionado.")
        return
    # Filtrar pelos técnicos da equipe (se houver filtro)
    tecs_filtro = f["tecs_sup"] if f["tecs_sup"] else []
    if tecs_filtro:
        mask_vip = df_vip_rep['tecnico_anterior'].astype(str).str.upper().isin([t.upper() for t in tecs_filtro])
    else:
        mask_vip = pd.Series(True, index=df_vip_rep.index)
    df_rep = df_vip_rep[mask_vip].copy()
    if df_rep.empty:
        st.info("Nenhum repetido VIP para os filtros selecionados.")
        return
    # Estatísticas
    total_repetidos = len(df_rep)
    # Total de reparos da equipe (BASEBOT) no mês
    df_base_mes = df_base[df_base["MES_REF"] == f["mes"]].copy()
    if tecs_filtro:
        mask_base = df_base_mes['COD_TEC'].isin(tecs_filtro)
    else:
        mask_base = pd.Series(True, index=df_base_mes.index)
    reparos_equipe = df_base_mes[mask_base & (df_base_mes["MACRO_NORM"] == "REP-FTTH") & (df_base_mes["ESTADO_NORM"] == "CONCLUÍDO COM SUCESSO")]
    total_reparos = len(reparos_equipe)
    taxa = round(total_repetidos / total_reparos * 100, 2) if total_reparos > 0 else 0
    cols = st.columns(3)
    cols[0].markdown(_kpi("Repetidos (VIP)", f"{total_repetidos}", "GPONs únicos", "kpi-red" if taxa>9 else "kpi-yellow"), unsafe_allow_html=True)
    cols[1].markdown(_kpi("Total Reparos (BASEBOT)", f"{total_reparos}", "concluídos no mês", "kpi-blue"), unsafe_allow_html=True)
    cols[2].markdown(_kpi("Taxa %", f"{taxa}%", "meta: ≤ 9%", "kpi-red" if taxa>9 else "kpi-green"), unsafe_allow_html=True)
    st.write("")
    # Tabela por técnico (tecnico_anterior)
    _sec("Repetidos por Técnico (como PAI)")
    rep_por_tec = df_rep.groupby('tecnico_anterior').size().reset_index(name='Repetidos')
    # Adicionar nome (buscar no BASEBOT)
    nomes_tec = df_base.drop_duplicates(subset=['COD_TEC']).set_index('COD_TEC')['NOME_TEC'].to_dict()
    rep_por_tec['Nome'] = rep_por_tec['tecnico_anterior'].map(nomes_tec).fillna(rep_por_tec['tecnico_anterior'])
    rep_por_tec = rep_por_tec.rename(columns={'tecnico_anterior': 'TR'})
    rep_por_tec = rep_por_tec[['Nome', 'TR', 'Repetidos']].sort_values('Repetidos', ascending=False)
    st.dataframe(rep_por_tec, use_container_width=True, hide_index=True)
    # Detalhamento dos GPONs repetidos
    _sec("GPONs com repetição")
    # Agrupar por GPON e mostrar quantas repetições e técnicos envolvidos
    gpons = df_rep.groupby('gpon').agg(Repeticoes=('gpon', 'count'), Tecnicos=list).reset_index()
    st.dataframe(gpons, use_container_width=True, hide_index=True)

def tela_infancia_vip(df_base, df_vip_inf, f):
    """Tela de infância usando a base VIP oficial."""
    _header("👶", "Infância (VIP Oficial)", f)
    if df_vip_inf is None:
        st.error("❌ Base VIP de infância não disponível para o mês selecionado.")
        return
    tecs_filtro = f["tecs_sup"] if f["tecs_sup"] else []
    if tecs_filtro:
        mask_vip = df_vip_inf['tecnico_anterior'].astype(str).str.upper().isin([t.upper() for t in tecs_filtro])
    else:
        mask_vip = pd.Series(True, index=df_vip_inf.index)
    df_inf = df_vip_inf[mask_vip].copy()
    if df_inf.empty:
        st.info("Nenhuma infância VIP para os filtros selecionados.")
        return
    total_inf = len(df_inf)
    # Total de instalações da equipe (BASEBOT)
    df_base_mes = df_base[df_base["MES_REF"] == f["mes"]].copy()
    if tecs_filtro:
        mask_base = df_base_mes['COD_TEC'].isin(tecs_filtro)
    else:
        mask_base = pd.Series(True, index=df_base_mes.index)
    instalacoes = df_base_mes[mask_base & (df_base_mes["MACRO_NORM"] == "INST-FTTH") & (df_base_mes["ESTADO_NORM"] == "CONCLUÍDO COM SUCESSO")]
    total_inst = len(instalacoes)
    taxa = round(total_inf / total_inst * 100, 2) if total_inst > 0 else 0
    cols = st.columns(3)
    cols[0].markdown(_kpi("Infância (VIP)", f"{total_inf}", "GPONs únicos", "kpi-red" if taxa>5 else "kpi-yellow"), unsafe_allow_html=True)
    cols[1].markdown(_kpi("Total Instalações", f"{total_inst}", "concluídas no mês", "kpi-blue"), unsafe_allow_html=True)
    cols[2].markdown(_kpi("Taxa %", f"{taxa}%", "meta: ≤ 5%", "kpi-red" if taxa>5 else "kpi-green"), unsafe_allow_html=True)
    st.write("")
    _sec("Infância por Técnico (como instalador)")
    inf_por_tec = df_inf.groupby('tecnico_anterior').size().reset_index(name='Infância')
    nomes_tec = df_base.drop_duplicates(subset=['COD_TEC']).set_index('COD_TEC')['NOME_TEC'].to_dict()
    inf_por_tec['Nome'] = inf_por_tec['tecnico_anterior'].map(nomes_tec).fillna(inf_por_tec['tecnico_anterior'])
    inf_por_tec = inf_por_tec.rename(columns={'tecnico_anterior': 'TR'})
    inf_por_tec = inf_por_tec[['Nome', 'TR', 'Infância']].sort_values('Infância', ascending=False)
    st.dataframe(inf_por_tec, use_container_width=True, hide_index=True)

def tela_qualidade(dm, ds, f):
    _header("🏆", "Qualidade", f)
    tecs = dm["COD_TEC"].dropna().unique()
    if len(tecs) == 0:
        st.warning("Nenhum técnico encontrado.")
        return
    rows = []
    for cod in tecs:
        df_tec = dm[dm["COD_TEC"] == cod].copy()
        if df_tec.empty: continue
        nome = df_tec["NOME_TEC"].iloc[0] if not df_tec.empty else cod
        suc = df_tec[df_tec["ESTADO_NORM"] == "CONCLUÍDO COM SUCESSO"]
        dias_unicos = suc["DIA_FIM"].nunique()
        prod_media = round(len(suc) / dias_unicos, 1) if dias_unicos > 0 else None
        n_suc = len(suc)
        n_ss = len(df_tec[df_tec["ESTADO_NORM"] == "CONCLUÍDO SEM SUCESSO"])
        efic = round(n_suc / (n_suc + n_ss) * 100, 1) if (n_suc + n_ss) > 0 else None
        rep_den = len(df_tec[df_tec["MACRO_NORM"] == "REP-FTTH"])
        rep_num = len(df_tec[(df_tec["MACRO_NORM"] == "REP-FTTH") & (df_tec["FLAG_REPETIDO"] == "SIM")])
        rep_pct = round(rep_num / rep_den * 100, 1) if rep_den > 0 else None
        inst_den = len(df_tec[(df_tec["MACRO_NORM"] == "INST-FTTH") & (df_tec["ESTADO_NORM"] == "CONCLUÍDO COM SUCESSO")])
        inst_num = len(df_tec[(df_tec["MACRO_NORM"] == "INST-FTTH") & (df_tec["ESTADO_NORM"] == "CONCLUÍDO COM SUCESSO") & (df_tec["FLAG_INFANCIA"] == "SIM")])
        inf_pct = round(inst_num / inst_den * 100, 1) if inst_den > 0 else None
        prod_cls = ("S/D","⬜","#94a3b8",0) if prod_media is None else (("EXCELENTE","🏆","#1e3a5f",4) if prod_media >= 6 else ("PARABENS","🟢","#16a34a",3) if prod_media >= 4 else ("ATENCAO","🟡","#d97706",2) if prod_media >= 3 else ("PRECISA MELHORAR","🔴","#dc2626",1))
        efic_cls = ("S/D","⬜","#94a3b8",0) if efic is None else (("EXCELENTE","🏆","#1e3a5f",4) if efic >= 85 else ("PARABENS","🟢","#16a34a",3) if efic >= 82 else ("ATENCAO","🟡","#d97706",2) if efic >= 75 else ("PRECISA MELHORAR","🔴","#dc2626",1))
        rep_cls = ("S/D","⬜","#94a3b8",0) if rep_pct is None else (("EXCELENTE","🏆","#1e3a5f",4) if rep_pct < 2 else ("OTIMO","🟢","#16a34a",3) if rep_pct <= 5 else ("PARABENS","🟢","#16a34a",2) if rep_pct <= 9 else ("PRECISA MELHORAR","🔴","#dc2626",0))
        inf_cls = ("S/D","⬜","#94a3b8",0) if inf_pct is None else (("OTIMO","🟢","#16a34a",3) if inf_pct < 3 else ("PRECISA MELHORAR","🔴","#dc2626",0))
        nota = prod_cls[3] + efic_cls[3] + rep_cls[3] + inf_cls[3]
        rows.append({"cod":cod, "nome":nome, "prod_media":prod_media, "efic_pct":efic, "rep_pct":rep_pct, "inf_pct":inf_pct, "prod_cls":prod_cls, "efic_cls":efic_cls, "rep_cls":rep_cls, "inf_cls":inf_cls, "nota":nota})
    if not rows:
        st.warning("Sem dados suficientes.")
        return
    df_q = pd.DataFrame(rows).sort_values("nota", ascending=False).reset_index(drop=True)
    n_exc = (df_q["nota"] >= 13).sum()
    n_bom = ((df_q["nota"] >= 9) & (df_q["nota"] < 13)).sum()
    n_atc = ((df_q["nota"] >= 5) & (df_q["nota"] < 9)).sum()
    n_mel = (df_q["nota"] < 5).sum()
    cols_kpi = st.columns(5)
    for col, lbl, val, cls in zip(cols_kpi, ["Técnicos","🏆 Excelente","✅ Bom","⚠️ Atenção","🔴 Melhoria"], [len(df_q), n_exc, n_bom, n_atc, n_mel], ["kpi-blue","kpi-blue","kpi-green","kpi-yellow","kpi-red"]):
        col.markdown(_kpi(lbl, val, "", cls), unsafe_allow_html=True)
    _sec("Ranking de Qualidade")
    _cor_map = {"EXCELENTE":("🏆","#1e3a5f"), "PARABENS":("🟢","#16a34a"), "OTIMO":("🟢","#15803d"), "ATENCAO":("🟡","#d97706"), "PRECISA MELHORAR":("🔴","#dc2626"), "S/D":("⬜","#94a3b8")}
    html_table = '<table class="qualidade-table"><thead><tr><th>Nome</th><th>TR</th><th style="text-align:center">Prod.</th><th style="text-align:center">Efic.</th><th style="text-align:center">Repet.</th><th style="text-align:center">Infan.</th><th style="text-align:center">Nota</th></tr></thead><tbody>'
    for _, r in df_q.iterrows():
        pv = f"{r['prod_media']:.1f}" if r['prod_media'] is not None else "S/D"
        ev = f"{r['efic_pct']:.1f}%" if r['efic_pct'] is not None else "S/D"
        rv = f"{r['rep_pct']:.1f}%" if r['rep_pct'] is not None else "S/D"
        iv = f"{r['inf_pct']:.1f}%" if r['inf_pct'] is not None else "S/D"
        nota_num = r['nota']
        nota_cor = "#1e3a5f" if nota_num >= 13 else "#16a34a" if nota_num >= 9 else "#d97706" if nota_num >= 5 else "#dc2626"
        prod_emoji, prod_color = _cor_map.get(r["prod_cls"][0], ("","#94a3b8"))
        efic_emoji, efic_color = _cor_map.get(r["efic_cls"][0], ("","#94a3b8"))
        rep_emoji, rep_color = _cor_map.get(r["rep_cls"][0], ("","#94a3b8"))
        inf_emoji, inf_color = _cor_map.get(r["inf_cls"][0], ("","#94a3b8"))
        html_table += f'<tr><td><strong>{r["nome"]}</strong></td><td style="color:#64748b;font-family:monospace">{r["cod"]}</td><td style="text-align:center;color:{prod_color};font-weight:600">{prod_emoji} {pv}</td><td style="text-align:center;color:{efic_color};font-weight:600">{efic_emoji} {ev}</td><td style="text-align:center;color:{rep_color};font-weight:600">{rep_emoji} {rv}</td><td style="text-align:center;color:{inf_color};font-weight:600">{inf_emoji} {iv}</td><td style="text-align:center;font-weight:700;color:{nota_cor}">{r["nota"]}/16</td></tr>'
    html_table += '</tbody></table>'
    st.markdown(html_table, unsafe_allow_html=True)

# =============================================================================
# 8. MAIN
# =============================================================================

def main():
    try:
        # Carrega as bases (BASEBOT + VIPs)
        df_base, df_vip_rep, df_vip_inf = carregar_todas_bases(datetime.now().strftime("%Y-%m"))
        if df_base is None:
            st.error("❌ Falha ao carregar BASEBOT.csv")
            return
        df_base, ultima_data = processar_basebot(df_base)
        f = sidebar(df_base, ultima_data)
        if not f:
            return
        dm = _filtrar(df_base, f)
        ds = _escopo(df_base, f)
        if f["supervisor"]:
            st.markdown(f'<div class="info-box">👑 Equipe de <strong>{f["supervisor"]}</strong> — {len(f["tecs_sup"])} técnico(s) | {f["mes"]}</div>', unsafe_allow_html=True)
        tela = f["tela"]
        if tela == "📅 Diario":
            tela_diario(ds, f)
        elif tela == "📊 Producao Diaria":
            tela_producao(dm, ds, f)
        elif tela == "🔁 Repetidos":
            tela_repetidos_vip(df_base, df_vip_rep, f)
        elif tela == "👶 Infancia":
            tela_infancia_vip(df_base, df_vip_inf, f)
        elif tela == "📆 Calendario":
            tela_calendario(ds, f)
        elif tela == "🏆 Qualidade":
            tela_qualidade(dm, ds, f)
    except Exception as e:
        st.error("❌ Ocorreu um erro")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
