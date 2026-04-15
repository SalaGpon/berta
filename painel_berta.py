#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERTA — Painel Operacional do Supervisor v3.1
Telas: Producao Diaria | Repetidos | Infancia
CORRIGIDO: Repetidos contabiliza cada reparo repetido (não GPON único)
"""

import os
import re
import base64
import uuid
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import streamlit as st

# =============================================================================
# 1. CONFIGURACAO DA PAGINA — primeira chamada obrigatoria
# =============================================================================

st.set_page_config(
    layout="wide",
    page_title="BERTA - Painel Operacional",
    page_icon="📡",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 2. CSS GLOBAL — injetado UMA unica vez
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* Reset global */
html, body { margin: 0; padding: 0; }
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* Fundo branco em TODOS os containers do Streamlit */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
.main, .block-container,
section.main > div,
div[data-testid="stVerticalBlock"] {
    background-color: #f5f7fa !important;
    color: #1a2332 !important;
}

/* Sidebar branca */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #dde3ed !important;
}
[data-testid="stSidebar"] * { color: #1a2332 !important; }
[data-testid="stSidebar"] hr { border-color: #dde3ed !important; }

/* Inputs e selects */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background-color: #ffffff !important;
    border-color: #dde3ed !important;
    color: #1a2332 !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div { color: #1a2332 !important; }
[data-baseweb="popover"] { background: #ffffff !important; }
[role="listbox"] { background: #ffffff !important; }
[role="option"] { color: #1a2332 !important; }

/* Tabs */
[data-baseweb="tab-list"] {
    background-color: #ffffff !important;
    border-bottom: 2px solid #dde3ed !important;
}
[data-baseweb="tab"] {
    color: #64748b !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    background: transparent !important;
}
[aria-selected="true"] {
    color: #1e3a5f !important;
    border-bottom: 2px solid #1e3a5f !important;
    background: transparent !important;
}
[data-baseweb="tab-panel"] {
    background-color: transparent !important;
}
[data-baseweb="tab-border"] { background-color: #dde3ed !important; }

/* DataFrames */
.stDataFrame,
[data-testid="stDataFrameResizable"],
[data-testid="stDataFrameContainer"] {
    background-color: #ffffff !important;
    border: 1px solid #dde3ed !important;
    border-radius: 8px !important;
}

/* Botoes */
.stButton > button {
    background-color: #1e3a5f !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}
.stButton > button:hover { background-color: #163050 !important; }

/* Multiselect tags */
[data-baseweb="tag"] {
    background-color: #e8f0fa !important;
    color: #1e3a5f !important;
}

/* Radio buttons */
.stRadio label { color: #1a2332 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f5f7fa; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

/* KPI Cards */
.kpi-card {
    background: #ffffff;
    border: 1px solid #dde3ed;
    border-radius: 10px;
    padding: 16px 14px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    min-height: 100px;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #1e3a5f);
}
.kpi-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 26px;
    font-weight: 700;
    color: #1a2332;
    line-height: 1;
}
.kpi-sub { font-size: 10px; color: #94a3b8; margin-top: 5px; }
.kpi-blue   { --accent: #1e3a5f; }
.kpi-green  { --accent: #16a34a; }
.kpi-yellow { --accent: #d97706; }
.kpi-red    { --accent: #dc2626; }
.kpi-purple { --accent: #7c3aed; }

/* Secao titulo */
.sec {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: #1e3a5f;
    border-left: 3px solid #1e3a5f;
    padding-left: 10px;
    margin: 22px 0 10px 0;
}

/* Header de tela */
.ph {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 0 18px 0;
    border-bottom: 1px solid #dde3ed;
    margin-bottom: 18px;
}
.ph h1 { font-size: 20px; font-weight: 700; color: #1a2332; margin: 0; }
.badge {
    background: #e8f0fa;
    border: 1px solid #bdd0ea;
    color: #1e3a5f;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    white-space: nowrap;
}
.badge-sup { background: #f0f4f8; border-color: #cbd5e1; color: #475569; }

/* Banner supervisor */
.banner-sup {
    background: #e8f0fa;
    border: 1px solid #bdd0ea;
    border-radius: 6px;
    padding: 8px 14px;
    margin-bottom: 16px;
    font-size: 12px;
    color: #1e3a5f;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 3. CONSTANTES
# =============================================================================

SUPABASE_URL = "https://bfamfgjjitrfcdyzuibd.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJmYW1mZ2pqaXRyZmNkeXp1aWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwODA1NjksImV4cCI6MjA4NjY1NjU2OX0."
    "BUWI_spoZoF-XC7DDaexsj2aNVO_sA7gODVEtcBRck0"
)
SUPABASE_HDR = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

SUPABASE_STORAGE_URL = (
    f"{SUPABASE_URL}/storage/v1/object/public/berta/BASEBOT.csv"
)

_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE_LOCAL = next(
    (p for p in [
        os.path.join(_DIR, "BASEBOT.csv"),
        os.path.join(_DIR, "bases", "BASEBOT.csv"),
    ] if os.path.exists(p)),
    None,
)

# Cores para graficos — tema branco
C = {
    "bg":     "#ffffff",
    "paper":  "#ffffff",
    "grid":   "#e8edf3",
    "txt":    "#475569",
    "navy":   "#1e3a5f",
    "navy2":  "#2d5a8e",
    "navy3":  "#4a7db5",
    "green":  "#16a34a",
    "yellow": "#d97706",
    "red":    "#dc2626",
    "purple": "#7c3aed",
}

_LYT = dict(
    paper_bgcolor=C["paper"],
    plot_bgcolor=C["bg"],
    font=dict(family="Inter, sans-serif", color=C["txt"], size=12),
    margin=dict(l=40, r=20, t=44, b=36),
    xaxis=dict(gridcolor=C["grid"], linecolor=C["grid"], zeroline=False, tickfont_color=C["txt"]),
    yaxis=dict(gridcolor=C["grid"], linecolor=C["grid"], zeroline=False, tickfont_color=C["txt"]),
    legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor=C["grid"], borderwidth=1, font_color=C["txt"]),
)

# =============================================================================
# 4. FUNCOES AUXILIARES PARA REPETIDOS (CORRIGIDAS)
# =============================================================================

def contar_reparos_repetidos_por_dia(df: pd.DataFrame, mes_str: str) -> pd.DataFrame:
    """
    Conta Total de Reparos e Reparos Repetidos por dia do mês.
    CORRIGIDO: Cada reparo repetido conta individualmente (não GPON único)
    
    Retorna DataFrame com:
        Dia, Total Reparos, Reparos Repetidos, Taxa %,
        Total Acumulado, Repetidos Acumulado, Taxa Acumulada %
    """
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        return pd.DataFrame()
    
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, mes + 1, 1) - timedelta(days=1)
    
    # Garantir colunas de data
    df = df.copy()
    if "AB_DT" not in df.columns:
        df["AB_DT"] = pd.to_datetime(df["Data de criação"], dayfirst=True, errors="coerce")
    if "FIM_DT" not in df.columns:
        df["FIM_DT"] = pd.to_datetime(df["Fim Execução"], dayfirst=True, errors="coerce")
    
    # Preparar base de reparos concluídos com sucesso
    df_rep = df[
        (df["Macro Atividade"] == "REP-FTTH") &
        (df["Estado"] == "CONCLUÍDO COM SUCESSO") &
        df["FIM_DT"].notna()
    ].copy()
    
    # Marcar quais reparos são repetições (delta <= 30 dias do anterior no mesmo GPON)
    df_rep["_GPON"] = df_rep["FSLOI_GPONAccess"].astype(str).str.strip().str.upper()
    df_rep = df_rep.sort_values(["_GPON", "FIM_DT"]).reset_index(drop=True)
    df_rep["is_repetido"] = False
    
    for gpon, grupo in df_rep.groupby("_GPON"):
        if len(grupo) < 2:
            continue
        for i in range(1, len(grupo)):
            delta = (grupo.iloc[i]["FIM_DT"] - grupo.iloc[i-1]["FIM_DT"]).days
            if delta <= 30:
                df_rep.loc[grupo.iloc[i].name, "is_repetido"] = True
    
    # Se tiver vip_flag_repetido (fonte oficial), usar ela como prioridade
    if "vip_flag_repetido" in df.columns:
        df_rep["is_repetido"] = df_rep["vip_flag_repetido"] == "SIM"
    
    # Gerar dias do mês
    dias_range = pd.date_range(primeiro_dia, ultimo_dia, freq='D')
    
    resultados = []
    total_acum = 0
    rep_acum = 0
    
    for dia in dias_range:
        # Reparos do dia (Data de criação no dia)
        reparos_dia = df_rep[
            (df_rep["AB_DT"].dt.date == dia.date())
        ]
        total_dia = len(reparos_dia)
        rep_dia = reparos_dia["is_repetido"].sum()
        
        total_acum += total_dia
        rep_acum += rep_dia
        
        taxa_dia = round(rep_dia / total_dia * 100, 2) if total_dia > 0 else 0
        taxa_acum = round(rep_acum / total_acum * 100, 2) if total_acum > 0 else 0
        
        resultados.append({
            "Dia": dia.strftime("%d/%m/%Y"),
            "Total Reparos": total_dia,
            "Reparos Repetidos": int(rep_dia),
            "Taxa %": taxa_dia,
            "Total Acumulado": total_acum,
            "Repetidos Acumulado": int(rep_acum),
            "Taxa Acumulada %": taxa_acum,
        })
    
    return pd.DataFrame(resultados)


def contar_reparos_repetidos_por_tecnico(df: pd.DataFrame, codigo_tecnico: str, mes_str: str) -> dict:
    """
    Retorna total_reparos e reparos_repetidos para um técnico no mês.
    CORRIGIDO: Cada reparo repetido conta individualmente.
    """
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        return {"total_reparos": 0, "reparos_repetidos": 0, "taxa": 0}
    
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, mes + 1, 1) - timedelta(days=1)
    
    df = df.copy()
    if "AB_DT" not in df.columns:
        df["AB_DT"] = pd.to_datetime(df["Data de criação"], dayfirst=True, errors="coerce")
    if "FIM_DT" not in df.columns:
        df["FIM_DT"] = pd.to_datetime(df["Fim Execução"], dayfirst=True, errors="coerce")
    
    # Filtrar pelo técnico
    df_tec = df[df["CODIGO_TECNICO_EXTRAIDO"] == codigo_tecnico]
    
    # Reparos válidos no período
    den_df = df_tec[
        (df_tec["Macro Atividade"] == "REP-FTTH") &
        (df_tec["Estado"] == "CONCLUÍDO COM SUCESSO") &
        (df_tec["AB_DT"] >= primeiro_dia) &
        (df_tec["AB_DT"] <= ultimo_dia) &
        df_tec["AB_DT"].notna()
    ]
    total_reparos = len(den_df)
    
    if total_reparos == 0:
        return {"total_reparos": 0, "reparos_repetidos": 0, "taxa": 0}
    
    # Usar vip_flag_repetido se disponível
    if "vip_flag_repetido" in df.columns:
        reparos_repetidos = (den_df["vip_flag_repetido"] == "SIM").sum()
    else:
        # Calcular repetições manualmente
        df_rep = df[
            (df["Macro Atividade"] == "REP-FTTH") &
            (df["Estado"] == "CONCLUÍDO COM SUCESSO") &
            df["FIM_DT"].notna()
        ].copy()
        df_rep["_GPON"] = df_rep["FSLOI_GPONAccess"].astype(str).str.strip().str.upper()
        df_rep = df_rep.sort_values(["_GPON", "FIM_DT"]).reset_index(drop=True)
        df_rep["is_repetido"] = False
        
        for gpon, grupo in df_rep.groupby("_GPON"):
            if len(grupo) < 2:
                continue
            for i in range(1, len(grupo)):
                delta = (grupo.iloc[i]["FIM_DT"] - grupo.iloc[i-1]["FIM_DT"]).days
                if delta <= 30:
                    df_rep.loc[grupo.iloc[i].name, "is_repetido"] = True
        
        # Filtrar pelo técnico
        df_rep_tec = df_rep[df_rep["CODIGO_TECNICO_EXTRAIDO"] == codigo_tecnico]
        mask_periodo = (df_rep_tec["AB_DT"] >= primeiro_dia) & (df_rep_tec["AB_DT"] <= ultimo_dia)
        reparos_repetidos = df_rep_tec[mask_periodo & df_rep_tec["is_repetido"]].shape[0]
    
    taxa = round(reparos_repetidos / total_reparos * 100, 2) if total_reparos > 0 else 0
    
    return {
        "total_reparos": total_reparos,
        "reparos_repetidos": int(reparos_repetidos),
        "taxa": taxa
    }


def contar_reparos_repetidos_geral(df: pd.DataFrame, mes_str: str) -> dict:
    """
    Retorna total_reparos e reparos_repetidos para todos os técnicos no mês.
    CORRIGIDO: Cada reparo repetido conta individualmente.
    """
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        return {"total_reparos": 0, "reparos_repetidos": 0, "taxa": 0}
    
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, mes + 1, 1) - timedelta(days=1)
    
    df = df.copy()
    if "AB_DT" not in df.columns:
        df["AB_DT"] = pd.to_datetime(df["Data de criação"], dayfirst=True, errors="coerce")
    
    # Reparos válidos no período
    den_df = df[
        (df["Macro Atividade"] == "REP-FTTH") &
        (df["Estado"] == "CONCLUÍDO COM SUCESSO") &
        (df["AB_DT"] >= primeiro_dia) &
        (df["AB_DT"] <= ultimo_dia) &
        df["AB_DT"].notna()
    ]
    total_reparos = len(den_df)
    
    if total_reparos == 0:
        return {"total_reparos": 0, "reparos_repetidos": 0, "taxa": 0}
    
    # Usar vip_flag_repetido se disponível
    if "vip_flag_repetido" in df.columns:
        reparos_repetidos = (den_df["vip_flag_repetido"] == "SIM").sum()
    else:
        # Calcular repetições manualmente
        df_rep = df[
            (df["Macro Atividade"] == "REP-FTTH") &
            (df["Estado"] == "CONCLUÍDO COM SUCESSO") &
            df["FIM_DT"].notna()
        ].copy()
        df_rep["_GPON"] = df_rep["FSLOI_GPONAccess"].astype(str).str.strip().str.upper()
        df_rep = df_rep.sort_values(["_GPON", "FIM_DT"]).reset_index(drop=True)
        df_rep["is_repetido"] = False
        
        for gpon, grupo in df_rep.groupby("_GPON"):
            if len(grupo) < 2:
                continue
            for i in range(1, len(grupo)):
                delta = (grupo.iloc[i]["FIM_DT"] - grupo.iloc[i-1]["FIM_DT"]).days
                if delta <= 30:
                    df_rep.loc[grupo.iloc[i].name, "is_repetido"] = True
        
        mask_periodo = (df_rep["AB_DT"] >= primeiro_dia) & (df_rep["AB_DT"] <= ultimo_dia)
        reparos_repetidos = df_rep[mask_periodo & df_rep["is_repetido"]].shape[0]
    
    taxa = round(reparos_repetidos / total_reparos * 100, 2) if total_reparos > 0 else 0
    
    return {
        "total_reparos": total_reparos,
        "reparos_repetidos": int(reparos_repetidos),
        "taxa": taxa
    }


def obter_reparos_repetidos_detalhados(df: pd.DataFrame, mes_str: str) -> pd.DataFrame:
    """
    Retorna DataFrame com os reparos que são repetições (detalhado por SA).
    """
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        return pd.DataFrame()
    
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, mes + 1, 1) - timedelta(days=1)
    
    df = df.copy()
    if "AB_DT" not in df.columns:
        df["AB_DT"] = pd.to_datetime(df["Data de criação"], dayfirst=True, errors="coerce")
    if "FIM_DT" not in df.columns:
        df["FIM_DT"] = pd.to_datetime(df["Fim Execução"], dayfirst=True, errors="coerce")
    
    df_rep = df[
        (df["Macro Atividade"] == "REP-FTTH") &
        (df["Estado"] == "CONCLUÍDO COM SUCESSO") &
        df["FIM_DT"].notna()
    ].copy()
    
    df_rep["_GPON"] = df_rep["FSLOI_GPONAccess"].astype(str).str.strip().str.upper()
    df_rep = df_rep.sort_values(["_GPON", "FIM_DT"]).reset_index(drop=True)
    df_rep["is_repetido"] = False
    df_rep["pai_sa"] = None
    df_rep["pai_tecnico"] = None
    df_rep["pai_codigo"] = None
    df_rep["dias_entre"] = None
    
    for gpon, grupo in df_rep.groupby("_GPON"):
        if len(grupo) < 2:
            continue
        for i in range(1, len(grupo)):
            delta = (grupo.iloc[i]["FIM_DT"] - grupo.iloc[i-1]["FIM_DT"]).days
            if delta <= 30:
                idx = grupo.iloc[i].name
                df_rep.loc[idx, "is_repetido"] = True
                df_rep.loc[idx, "pai_sa"] = grupo.iloc[i-1].get("Número SA", "")
                df_rep.loc[idx, "pai_tecnico"] = grupo.iloc[i-1].get("Técnico Atribuído", "")
                df_rep.loc[idx, "pai_codigo"] = grupo.iloc[i-1].get("CODIGO_TECNICO_EXTRAIDO", "")
                df_rep.loc[idx, "dias_entre"] = delta
    
    # Se tiver vip_flag_repetido, usar como fonte oficial
    if "vip_flag_repetido" in df.columns:
        df_rep["is_repetido"] = df_rep["vip_flag_repetido"] == "SIM"
    
    # Filtrar apenas repetições no período
    mask_periodo = (df_rep["AB_DT"] >= primeiro_dia) & (df_rep["AB_DT"] <= ultimo_dia)
    resultado = df_rep[mask_periodo & df_rep["is_repetido"]].copy()
    
    # Colunas úteis para exibição
    cols = ["Número SA", "FSLOI_GPONAccess", "CODIGO_TECNICO_EXTRAIDO", 
            "Técnico Atribuído", "AB_DT", "FIM_DT", "Cidade", "Bairro",
            "pai_sa", "pai_tecnico", "pai_codigo", "dias_entre"]
    cols = [c for c in cols if c in resultado.columns]
    
    return resultado[cols]

# =============================================================================
# 5. DADOS
# =============================================================================

@st.cache_data(ttl=300)
def ultima_atualizacao_base():
    try:
        url = f"{SUPABASE_URL}/storage/v1/object/info/public/berta/BASEBOT.csv"
        r = requests.get(url, headers=SUPABASE_HDR, timeout=10)
        if r.status_code == 200:
            info = r.json()
            updated = info.get("updated_at") or info.get("created_at", "")
            if updated:
                dt = pd.to_datetime(updated, utc=True).tz_convert("America/Sao_Paulo")
                return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    return None


@st.cache_data(ttl=300)
def carregar_base(_dummy=None):
    import io

    try:
        r = requests.get(SUPABASE_STORAGE_URL, timeout=90)
        if r.status_code == 200:
            texto = r.content.decode("utf-8-sig", errors="replace")
            df = pd.read_csv(io.StringIO(texto), sep=";", dtype=str, low_memory=False)
            if len(df) > 0:
                return _processar_df(df)
            st.warning("Base do Supabase veio vazia — tentando arquivo local...")
        else:
            st.warning(f"Supabase Storage: HTTP {r.status_code} — tentando arquivo local...")
    except requests.exceptions.Timeout:
        st.warning("Timeout ao baixar base do Supabase — tentando arquivo local...")
    except Exception as e:
        st.warning(f"Erro Supabase Storage: {e} — tentando arquivo local...")

    if CAMINHO_BASE_LOCAL:
        try:
            df = pd.read_csv(CAMINHO_BASE_LOCAL, sep=";", encoding="utf-8-sig",
                             dtype=str, low_memory=False)
            return _processar_df(df)
        except Exception as e:
            st.error(f"Erro ao carregar arquivo local: {e}")

    return None


def _processar_df(df):
    df.columns = df.columns.str.strip()
    df["FIM_DT"] = pd.to_datetime(df["Fim Execução"],    dayfirst=True, errors="coerce")
    df["AB_DT"]  = pd.to_datetime(df["Data de criação"], dayfirst=True, errors="coerce")
    df["Estado"]          = df["Estado"].str.strip().str.upper()
    df["Macro Atividade"] = df["Macro Atividade"].str.strip().str.upper()
    df["NOME_TEC"] = df["Técnico Atribuído"].apply(
        lambda v: str(v).split(" - ")[0].strip().title() if pd.notna(v) else "")
    df["DIA_FIM"] = df["FIM_DT"].dt.date
    df["MES_FIM"] = df["FIM_DT"].dt.to_period("M")
    df["SEM_FIM"] = df["FIM_DT"].dt.isocalendar().week.astype("Int64")
    df["ANO_FIM"] = df["FIM_DT"].dt.year.astype("Int64")
    df["DIA_AB"]  = df["AB_DT"].dt.date
    df["MES_AB"]  = df["AB_DT"].dt.to_period("M")
    df["SEM_AB"]  = df["AB_DT"].dt.isocalendar().week.astype("Int64")

    _vip_defaults = {
        "vip_flag_repetido"     : "NAO",
        "vip_flag_infancia"     : "NAO",
        "flag_reparo_consolidado": "",
        "rep_dias_anterior"     : "",
        "rep_cod_fech_anterior" : "",
        "rep_tecnico_pai"       : "",
        "rep_tecnico_filho"     : "",
        "rep_agrupador_anterior": "",
        "rep_dat_fech_anterior" : "",
        "inf_dias_anterior"     : "",
        "inf_tecnico_pai"       : "",
        "inf_tecnico_filho"     : "",
        "inf_dat_fech_anterior" : "",
        "vip_den_rep"           : 0,
        "vip_num_rep"           : 0,
        "vip_taxa_rep"          : 0.0,
        "vip_den_inf"           : 0,
        "vip_num_inf"           : 0,
        "vip_taxa_inf"          : 0.0,
    }
    for col, default in _vip_defaults.items():
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)

    return df


@st.cache_data(ttl=300)
def carregar_equipes():
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/tecnicos?select=tr,tt,tc,supervisor,funcionario",
            headers=SUPABASE_HDR, timeout=10)
        if r.status_code != 200:
            return {}
        pat = re.compile(r"^(TR|TT|TC)\d+$", re.I)
        eq = {}
        for row in r.json():
            sup = str(row.get("supervisor") or "").strip()
            if not sup or sup.upper() in ("", "NAN", "NONE"):
                continue
            sup = sup.title()
            cod = None
            func = str(row.get("funcionario") or "")
            m = re.search(r"(TR|TT|TC)\d+", func, re.I)
            if m:
                cod = m.group(0).upper()
            else:
                for campo in ("tc", "tr", "tt"):
                    v = str(row.get(campo) or "").strip().upper()
                    if v and pat.match(v):
                        cod = v
                        break
            if cod:
                eq.setdefault(sup, [])
                if cod not in eq[sup]:
                    eq[sup].append(cod)
        return eq
    except Exception:
        return {}

# =============================================================================
# 6. HELPERS
# =============================================================================

def _kpi(label, valor, sub="", cls="kpi-blue"):
    s = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="kpi-card {cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{valor}</div>'
            f'{s}</div>')


def _sec(txt):
    st.markdown(f'<div class="sec">{txt}</div>', unsafe_allow_html=True)


def _header(icone, titulo, f):
    mes = f.get("mes", "")
    sup = f.get("supervisor", "")
    sup_b = f'<span class="badge badge-sup">👑 {sup}</span>' if sup else ""
    st.markdown(
        f'<div class="ph"><h1>{icone} {titulo}</h1>'
        f'<span class="badge">{mes}</span>{sup_b}</div>',
        unsafe_allow_html=True)


def _lyt(titulo="", h=360):
    return {**_LYT, "height": h,
            "title": dict(text=titulo, font=dict(size=13, color="#1a2332"), x=0.01)}


def _bar_h(y, x, color, titulo="", h=340, labels=None):
    fig = go.Figure(go.Bar(
        x=x, y=y, orientation="h", marker_color=color,
        text=labels, textposition="inside", textfont_color="white"))
    fig.update_layout(**_lyt(titulo, h))
    fig.update_layout(yaxis_autorange="reversed")
    return fig


def _ev_dual(x, bars, line, bcolor, titulo, h=300, meta=None):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=x, y=bars, name="Qtd", marker_color=bcolor)
    fig.add_scatter(x=x, y=line, name="Taxa%", mode="lines+markers",
                    line=dict(color=C["yellow"], width=2), marker_size=6, secondary_y=True)
    if meta is not None:
        fig.add_hline(y=meta, line_dash="dash", line_color=C["red"],
                      annotation_text=f"Meta {meta}%", secondary_y=True)
    fig.update_layout(**_lyt(titulo, h))
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return fig

# =============================================================================
# 7. SIDEBAR
# =============================================================================

def sidebar(df):
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:18px 0 10px">'
            '<div style="font-size:22px;font-weight:800;color:#1e3a5f;letter-spacing:2px">📡 BERTA</div>'
            '<div style="font-size:10px;color:#64748b;font-weight:600;letter-spacing:1px;margin-top:3px">PAINEL OPERACIONAL</div>'
            '</div>', unsafe_allow_html=True)
        st.divider()

        tela = st.radio("Tela",
            ["📅 Diario", "📊 Producao Diaria", "🔁 Repetidos", "👶 Infancia", "📆 Calendario", "🏆 Qualidade"],
            label_visibility="collapsed", key="nav")
        st.divider()

        st.markdown("**Filtros**")

        meses = sorted(df["MES_FIM"].dropna().astype(str).unique(), reverse=True)
        mes   = st.selectbox("📅 Mes", meses, key="f_mes")

        eq   = carregar_equipes()
        sups = sorted(eq.keys())
        if sups:
            sup = st.selectbox("👑 Supervisor", ["— Todos —"] + sups, key="f_sup")
            tecs_sup = eq.get(sup, []) if sup != "— Todos —" else []
            if tecs_sup:
                st.caption(f"Equipe: {len(tecs_sup)} tecnico(s)")
        else:
            sup, tecs_sup = "— Todos —", []
            st.caption("Supervisores nao carregados")

        terrs = sorted(df["Território de serviço: Nome"].dropna().unique())
        terr  = st.multiselect("📍 Territorio", terrs, key="f_terr")

        pool = ([t for t in tecs_sup if t in df["CODIGO_TECNICO_EXTRAIDO"].values]
                if tecs_sup else sorted(df["CODIGO_TECNICO_EXTRAIDO"].dropna().unique()))
        tec  = st.multiselect("👤 Tecnico", pool, key="f_tec")

        st.divider()
        if st.button("🔄 Recarregar base", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    return {
        "tela": tela, "mes": mes,
        "supervisor": "" if sup == "— Todos —" else sup,
        "tecs_sup": tecs_sup,
        "territorios": terr,
        "tecnicos": tec,
    }


def _filtrar(df, f):
    r = df[df["MES_FIM"].astype(str) == f["mes"]].copy()
    if f["tecs_sup"]:    r = r[r["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecs_sup"])]
    if f["territorios"]: r = r[r["Território de serviço: Nome"].isin(f["territorios"])]
    if f["tecnicos"]:    r = r[r["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecnicos"])]
    return r


def _escopo(df, f):
    if f["tecs_sup"]:
        return df[df["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecs_sup"])].copy()
    return df

# =============================================================================
# 8. TELA — PRODUCAO DIARIA
# =============================================================================

def tela_producao(dm, ds, f):
    _header("📊", "Producao Diaria", f)

    suc  = dm[dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
    conc = dm[dm["Estado"].isin(["CONCLUÍDO COM SUCESSO", "CONCLUÍDO SEM SUCESSO"])]
    inst = suc[suc["Macro Atividade"] == "INST-FTTH"]
    rep  = suc[suc["Macro Atividade"] == "REP-FTTH"]
    dias = suc["DIA_FIM"].nunique()
    efic = round(len(suc) / len(conc) * 100, 1) if len(conc) > 0 else 0
    med  = round(len(suc) / dias, 1) if dias > 0 else 0

    cols = st.columns(6)
    for col, (lb, vl, sb, cl) in zip(cols, [
        ("Concluidos",  f"{len(suc):,}",  "c/ sucesso",       "kpi-blue"),
        ("Eficacia",    f"{efic}%",        "suc / total",      "kpi-green" if efic>=85 else "kpi-yellow" if efic>=70 else "kpi-red"),
        ("Instalacoes", f"{len(inst):,}",  "INST-FTTH",        "kpi-blue"),
        ("Reparos",     f"{len(rep):,}",   "REP-FTTH",         "kpi-purple"),
        ("Dias Trab.",  f"{dias}",         "c/ encerramento",  "kpi-blue"),
        ("Media/Dia",   f"{med}",          "atividades/dia",   "kpi-blue"),
    ]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")

    _sec("Producao por Dia")
    prod = suc.groupby("DIA_FIM").agg(
        Total=("Número SA", "count"),
        Inst =("Macro Atividade", lambda x: (x=="INST-FTTH").sum()),
        Rep  =("Macro Atividade", lambda x: (x=="REP-FTTH").sum()),
    ).reset_index()
    ss = dm[dm["FLAG_CONCLUIDO_SEM_SUCESSO"]=="SIM"].groupby("DIA_FIM").size().reset_index(name="SS")
    prod = prod.merge(ss, on="DIA_FIM", how="left")
    prod["SS"]    = prod["SS"].fillna(0).astype(int)
    prod["Efic%"] = (prod["Total"]/(prod["Total"]+prod["SS"])*100).round(1)
    prod["Dia"]   = pd.to_datetime(prod["DIA_FIM"]).dt.strftime("%d/%m")

    fig = go.Figure()
    fig.add_bar(x=prod["Dia"], y=prod["Inst"], name="INST", marker_color=C["navy"])
    fig.add_bar(x=prod["Dia"], y=prod["Rep"],  name="REP",  marker_color=C["purple"])
    fig.update_layout(barmode="stack", showlegend=True, **_lyt("Producao Diaria - INST + REP", 320))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        prod[["Dia","Total","Inst","Rep","SS","Efic%"]].rename(
            columns={"Inst":"INST","Rep":"REP","SS":"Sem Suc.","Efic%":"Eficacia%"}),
        use_container_width=True, hide_index=True,
        column_config={"Eficacia%": st.column_config.ProgressColumn(
            "Eficacia%", format="%.1f%%", min_value=0, max_value=100)})

    _sec("Pareto de Tecnicos")
    pt = suc.groupby(["CODIGO_TECNICO_EXTRAIDO","NOME_TEC"]).size().reset_index(name="Prod")
    pt = pt.sort_values("Prod", ascending=False).reset_index(drop=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top 5 — Maior Producao**")
        t5 = pt.head(5)
        st.plotly_chart(
            _bar_h(t5["NOME_TEC"], t5["Prod"], C["green"],
                   labels=t5["CODIGO_TECNICO_EXTRAIDO"], h=260),
            use_container_width=True)
    with c2:
        st.markdown("**Top 5 — Menor Producao**")
        b5 = pt.tail(5).sort_values("Prod")
        st.plotly_chart(
            _bar_h(b5["NOME_TEC"], b5["Prod"], C["yellow"],
                   labels=b5["CODIGO_TECNICO_EXTRAIDO"], h=260),
            use_container_width=True)

    _sec("Ranking Completo")
    pt["#"] = range(1, len(pt)+1)
    st.dataframe(
        pt[["#","NOME_TEC","CODIGO_TECNICO_EXTRAIDO","Prod"]].rename(
            columns={"NOME_TEC":"Nome","CODIGO_TECNICO_EXTRAIDO":"TR","Prod":"Producao"}),
        use_container_width=True, hide_index=True,
        column_config={"Producao": st.column_config.ProgressColumn(
            "Producao", format="%d", min_value=0, max_value=int(pt["Prod"].max()))})

    _sec("Evolucoes")
    tab1, tab2 = st.tabs(["📅 Semanal","📆 Mensal"])
    suc_sc = ds[ds["FLAG_CONCLUIDO_SUCESSO"]=="SIM"].copy()
    with tab1:
        suc_sc["AW"] = suc_sc["ANO_FIM"].astype(str)+"-S"+suc_sc["SEM_FIM"].astype(str).str.zfill(2)
        ev = suc_sc.groupby("AW").size().reset_index(name="T").sort_values("AW").tail(12)
        fig2 = go.Figure(go.Scatter(x=ev["AW"],y=ev["T"],mode="lines+markers",
                                    line=dict(color=C["navy"],width=2),marker_size=7))
        fig2.update_layout(**_lyt("Producao Semanal - ultimas 12 semanas",300))
        st.plotly_chart(fig2, use_container_width=True)
    with tab2:
        ev2 = suc_sc.groupby("MES_FIM").size().reset_index(name="T")
        ev2["MES_FIM"] = ev2["MES_FIM"].astype(str)
        ev2 = ev2.sort_values("MES_FIM").tail(12)
        fig3 = go.Figure(go.Bar(x=ev2["MES_FIM"],y=ev2["T"],marker_color=C["navy"]))
        fig3.update_layout(**_lyt("Producao Mensal",300))
        st.plotly_chart(fig3, use_container_width=True)

# =============================================================================
# 9. TELA — REPETIDOS (CORRIGIDA)
# =============================================================================

def tela_repetidos(dm, ds, f):
    _header("🔁", "Repetidos", f)

    # Calcular totais usando as funções corrigidas
    geral = contar_reparos_repetidos_geral(ds, f["mes"])
    total_reparos = geral["total_reparos"]
    reparos_repetidos = geral["reparos_repetidos"]
    taxa = geral["taxa"]

    # Verificar se usa fonte VIP
    _usa_vip = "vip_flag_repetido" in ds.columns and (ds["vip_flag_repetido"] == "SIM").any()
    fonte_label = "🏛️ Fonte: VIP Oficial (cada reparo repetido)" if _usa_vip else "⚙️ Fonte: Cálculo Interno (cada reparo repetido)"

    # Reparos em garantia (abertos dentro da janela)
    rep_ab = ds[ds["FLAG_REPETIDO_ABERTO"] == "SIM"] if "FLAG_REPETIDO_ABERTO" in ds.columns else pd.DataFrame()
    
    # Reparos alarmados
    if _usa_vip and "ALARMADO" in ds.columns:
        rep_alrm = ds[
            (ds["Macro Atividade"] == "REP-FTTH") &
            (ds["Estado"] == "CONCLUÍDO COM SUCESSO") &
            (ds["vip_flag_repetido"] == "SIM") &
            (ds["ALARMADO"] == "SIM")
        ]
        rep_alrm_count = len(rep_alrm)
    else:
        rep_alrm_count = 0

    cols = st.columns(5)
    for col, (lb, vl, sb, cl) in zip(cols, [
        ("Total Reparos", f"{total_reparos:,}",   "abertos no mes",  "kpi-blue"),
        ("Reparos Repetidos", f"{reparos_repetidos:,}",   "cada SA repetido",    "kpi-red" if taxa > 9 else "kpi-yellow"),
        ("Taxa %",        f"{taxa}%",              "meta: <= 9%",     "kpi-red" if taxa > 9 else "kpi-green"),
        ("Em Garantia",   f"{len(rep_ab):,}",      "abertos 30d",     "kpi-yellow"),
        ("Alarmados",     f"{rep_alrm_count}",     "GPON alarmado",   "kpi-red" if rep_alrm_count > 0 else "kpi-green"),
    ]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:#64748b;margin:6px 0 14px 2px;">{fonte_label}</div>',
        unsafe_allow_html=True)

    # TABELA POR DIA (igual ao exemplo solicitado)
    _sec("Repetidos por Dia — Visão Acumulada")
    
    tabela_dia = contar_reparos_repetidos_por_dia(ds, f["mes"])
    
    if not tabela_dia.empty:
        # Formatar para exibição
        display_dia = tabela_dia.copy()
        display_dia["Taxa %"] = display_dia["Taxa %"].apply(lambda x: f"{x:.2f}%")
        display_dia["Taxa Acumulada %"] = display_dia["Taxa Acumulada %"].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            display_dia,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Dia": st.column_config.TextColumn("Dia / Mês", width="small"),
                "Total Reparos": st.column_config.NumberColumn("Total Reparos", format="%d"),
                "Reparos Repetidos": st.column_config.NumberColumn("Reparos Repetidos", format="%d"),
                "Taxa %": st.column_config.TextColumn("Indicador Real %", width="small"),
                "Total Acumulado": st.column_config.NumberColumn("Total Reparos Acum.", format="%d"),
                "Repetidos Acumulado": st.column_config.NumberColumn("Repetida Acum.", format="%d"),
                "Taxa Acumulada %": st.column_config.TextColumn("Indicador % Acumulado", width="small"),
            }
        )
        
        # Linha de total
        total_linha = tabela_dia.iloc[-1] if not tabela_dia.empty else None
        if total_linha is not None:
            st.markdown(
                f'<div style="margin-top:8px;padding:8px;background:#f0f4f8;border-radius:6px;font-size:13px;">'
                f'<strong>Total</strong> — Total Reparos: {total_linha["Total Acumulado"]:,} | '
                f'Reparos Repetidos: {total_linha["Repetidos Acumulado"]} | '
                f'Taxa: {total_linha["Taxa Acumulada %"]:.2f}%'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # Indicador por Técnico (corrigido)
    _sec("Indicador por Tecnico (cada reparo repetido)")

    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    tecnicos = ds["CODIGO_TECNICO_EXTRAIDO"].dropna().unique()
    rows_tec = []
    for cod in tecnicos:
        if not cod:
            continue
        dados = contar_reparos_repetidos_por_tecnico(ds, cod, f["mes"])
        if dados["total_reparos"] > 0:
            nome = _n(ds[ds["CODIGO_TECNICO_EXTRAIDO"] == cod]["Técnico Atribuído"].iloc[0] if len(ds[ds["CODIGO_TECNICO_EXTRAIDO"] == cod]) > 0 else cod)
            rows_tec.append({
                "TR": cod,
                "Nome": nome,
                "Total": dados["total_reparos"],
                "Repetidos": dados["reparos_repetidos"],
                "Taxa%": dados["taxa"],
            })
    
    if rows_tec:
        df_tec = pd.DataFrame(rows_tec).sort_values("Taxa%", ascending=False).reset_index(drop=True)
        df_tec["Status"] = df_tec["Taxa%"].apply(lambda t: "🔴" if t > 15 else "🟡" if t > 9 else "🟢" if t > 0 else "⚪")
        
        st.dataframe(
            df_tec[["Status", "Nome", "TR", "Repetidos", "Total", "Taxa%"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Taxa%": st.column_config.ProgressColumn(
                    "Taxa%", format="%.1f%%", min_value=0,
                    max_value=max(float(df_tec["Taxa%"].max()) if not df_tec.empty else 1, 1)
                )
            }
        )
    else:
        st.info("Nenhum dado de repetidos por técnico.")

    # Detalhamento dos reparos repetidos
    _sec("Detalhamento — Reparos Repetidos")
    
    reparos_detalhe = obter_reparos_repetidos_detalhados(ds, f["mes"])
    
    if not reparos_detalhe.empty:
        cols_det = ["Número SA", "FSLOI_GPONAccess", "CODIGO_TECNICO_EXTRAIDO", 
                    "Técnico Atribuído", "AB_DT", "Cidade", "pai_sa", "pai_tecnico", "dias_entre"]
        cols_det = [c for c in cols_det if c in reparos_detalhe.columns]
        
        display_det = reparos_detalhe[cols_det].copy()
        if "AB_DT" in display_det.columns:
            display_det["AB_DT"] = display_det["AB_DT"].dt.strftime("%d/%m/%Y")
        
        st.dataframe(
            display_det.rename(columns={
                "Número SA": "SA Repetido",
                "FSLOI_GPONAccess": "GPON",
                "CODIGO_TECNICO_EXTRAIDO": "TR",
                "Técnico Atribuído": "Tecnico",
                "AB_DT": "Abertura",
                "pai_sa": "SA Pai",
                "pai_tecnico": "Tecnico Pai",
                "dias_entre": "Dias",
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("Nenhum reparo repetido encontrado no período.")

    # Pareto de causas
    c1, c2 = st.columns(2)
    with c1:
        _sec("Pareto - Causas")
        if not reparos_detalhe.empty and "Descrição" in reparos_detalhe.columns:
            caus = reparos_detalhe["Descrição"].value_counts().head(10).reset_index()
            caus.columns = ["Causa", "Qtd"]
            caus["L"] = caus["Causa"].astype(str).str[:50] + "..."
            st.plotly_chart(_bar_h(caus["L"], caus["Qtd"], C["red"], "Top 10 Causas", h=380),
                            use_container_width=True)
        else:
            st.info("Sem dados de causa.")
    
    with c2:
        _sec("Pareto - Tecnicos")
        if rows_tec:
            top = df_tec[df_tec["Repetidos"] > 0].sort_values("Repetidos", ascending=False).head(15)
            if not top.empty:
                st.plotly_chart(_bar_h(top["Nome"], top["Repetidos"], C["red"],
                                       "Tecnicos com mais Repetidos", h=380, labels=top["TR"]),
                                use_container_width=True)
            else:
                st.success("Nenhum tecnico com repetidos.")
        else:
            st.success("Nenhum tecnico com repetidos.")

    # Evoluções
    _sec("Evolucoes")
    tab1, tab2 = st.tabs(["📅 Semanal", "📆 Mensal"])
    
    with tab1:
        if "SEM_AB" in ds.columns:
            # Calcular evolução semanal com a nova métrica
            ev_semanal = []
            semanas = sorted(ds["SEM_AB"].dropna().unique())
            for sem in semanas[-12:]:
                total_sem = len(ds[
                    (ds["Macro Atividade"] == "REP-FTTH") &
                    (ds["Estado"] == "CONCLUÍDO COM SUCESSO") &
                    (ds["SEM_AB"] == sem)
                ])
                rep_sem = len(obter_reparos_repetidos_detalhados(
                    ds[ds["SEM_AB"] == sem], f["mes"]
                )) if total_sem > 0 else 0
                taxa_sem = round(rep_sem / total_sem * 100, 2) if total_sem > 0 else 0
                ev_semanal.append({"semana": f"S{int(sem)}", "total": total_sem, "rep": rep_sem, "taxa": taxa_sem})
            
            if ev_semanal:
                df_ev = pd.DataFrame(ev_semanal)
                st.plotly_chart(_ev_dual(df_ev["semana"], df_ev["rep"], df_ev["taxa"],
                                          C["red"], "Evolucao Semanal", meta=9), 
                                use_container_width=True)
            else:
                st.info("Sem dados para evolução semanal.")
        else:
            st.info("Sem dados para evolução semanal.")
    
    with tab2:
        if "MES_AB" in ds.columns:
            ev_mensal = []
            meses_ev = sorted(ds["MES_AB"].dropna().unique())[-12:]
            for mes_ev in meses_ev:
                total_mes = len(ds[
                    (ds["Macro Atividade"] == "REP-FTTH") &
                    (ds["Estado"] == "CONCLUÍDO COM SUCESSO") &
                    (ds["MES_AB"] == mes_ev)
                ])
                rep_mes = len(obter_reparos_repetidos_detalhados(
                    ds[ds["MES_AB"] == mes_ev], str(mes_ev)
                )) if total_mes > 0 else 0
                taxa_mes = round(rep_mes / total_mes * 100, 2) if total_mes > 0 else 0
                ev_mensal.append({"mes": str(mes_ev), "total": total_mes, "rep": rep_mes, "taxa": taxa_mes})
            
            if ev_mensal:
                df_ev = pd.DataFrame(ev_mensal)
                st.plotly_chart(_ev_dual(df_ev["mes"], df_ev["rep"], df_ev["taxa"],
                                          C["red"], "Evolucao Mensal", meta=9),
                                use_container_width=True)
            else:
                st.info("Sem dados para evolução mensal.")
        else:
            st.info("Sem dados para evolução mensal.")

# =============================================================================
# 10. TELA — INFANCIA
# =============================================================================

def tela_infancia(dm, ds, f):
    _header("👶", "Infancia", f)

    _usa_vip_inf = "vip_flag_infancia" in dm.columns and (dm["vip_flag_infancia"] == "SIM").any()

    inst = dm[
        (dm["Macro Atividade"] == "INST-FTTH") &
        (dm["Estado"] == "CONCLUÍDO COM SUCESSO")
    ]

    if _usa_vip_inf:
        inf = inst[inst["vip_flag_infancia"] == "SIM"]
        fonte_label = "🏛️ Fonte: VIP Oficial"
    else:
        inf = inst[inst["FLAG_INFANCIA_30D"] == "SIM"] if "FLAG_INFANCIA_30D" in inst.columns else pd.DataFrame()
        fonte_label = "⚙️ Fonte: Cálculo Interno"

    taxa = round(len(inf) / len(inst) * 100, 2) if len(inst) > 0 else 0
    estados_ab = ["ATRIBUÍDO", "NÃO ATRIBUÍDO", "RECEBIDO", "EM EXECUÇÃO", "EM DESLOCAMENTO"]
    gpons = set(inf["FSLOI_GPONAccess"].dropna().str.upper())
    rep_ab = ds[(ds["Macro Atividade"] == "REP-FTTH") &
                (ds["Estado"].isin(estados_ab)) &
                (ds["FSLOI_GPONAccess"].str.upper().isin(gpons))] if gpons else pd.DataFrame()
    inf_alrm = inf[inf["ALARMADO"] == "SIM"] if "ALARMADO" in inf.columns else pd.DataFrame()

    cols = st.columns(5)
    for col, (lb, vl, sb, cl) in zip(cols, [
        ("Total Inst.",  f"{len(inst):,}", "INST concluidas",  "kpi-blue"),
        ("Infancia",     f"{len(inf):,}",  "reparo em 30d",    "kpi-red" if taxa > 5 else "kpi-yellow"),
        ("Taxa %",       f"{taxa}%",       "meta: <= 5%",      "kpi-red" if taxa > 5 else "kpi-green"),
        ("Inf. Aberta",  f"{len(rep_ab):,}", "reparo aberto",   "kpi-yellow"),
        ("Alarmados",    f"{len(inf_alrm):,}", "GPON alarmado", "kpi-red" if len(inf_alrm) > 0 else "kpi-green"),
    ]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:#64748b;margin:6px 0 14px 2px;">{fonte_label}</div>',
        unsafe_allow_html=True)

    _sec("Indicador por Tecnico")
    
    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""
    
    di = inst.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
        Total=("Número SA", "count"),
        Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0]) if len(x) else "")
    ).reset_index()
    
    ni = inf.groupby("CODIGO_TECNICO_EXTRAIDO").size().reset_index(name="Inf") if not inf.empty else pd.DataFrame(columns=["CODIGO_TECNICO_EXTRAIDO", "Inf"])
    tb = di.merge(ni, on="CODIGO_TECNICO_EXTRAIDO", how="left")
    tb["Inf"] = tb["Inf"].fillna(0).astype(int)
    tb["Taxa%"] = (tb["Inf"] / tb["Total"] * 100).round(2)
    tb = tb.sort_values("Taxa%", ascending=False).reset_index(drop=True)
    tb.columns = ["TR", "Total", "Nome", "Infancia", "Taxa%"]
    tb["Status"] = tb["Taxa%"].apply(lambda t: "🔴" if t > 8 else "🟡" if t > 5 else "🟢" if t > 0 else "⚪")
    
    st.dataframe(tb[["Status", "Nome", "TR", "Infancia", "Total", "Taxa%"]], 
                 use_container_width=True, hide_index=True,
                 column_config={"Taxa%": st.column_config.ProgressColumn(
                     "Taxa%", format="%.1f%%", min_value=0, 
                     max_value=max(float(tb["Taxa%"].max()) if not tb.empty else 1, 1))})

    if _usa_vip_inf and not inf.empty:
        _sec("Detalhamento — Historico da Instalacao Anterior (VIP)")
        cols_det = [c for c in [
            "CODIGO_TECNICO_EXTRAIDO", "NOME_TEC", "FSLOI_GPONAccess", "Número SA",
            "inf_dias_anterior", "inf_tecnico_filho", "inf_dat_fech_anterior", "Cidade",
        ] if c in inf.columns]
        det = inf[cols_det].drop_duplicates(subset=["FSLOI_GPONAccess"]).rename(columns={
            "CODIGO_TECNICO_EXTRAIDO": "TR (PAI Inst.)",
            "NOME_TEC": "Tecnico (PAI)",
            "FSLOI_GPONAccess": "GPON",
            "Número SA": "SA Inst.",
            "inf_dias_anterior": "Dias p/ Reparo",
            "inf_tecnico_filho": "Tec. que Reparou",
            "inf_dat_fech_anterior": "Data Inst. Anterior",
        })
        st.dataframe(det, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        _sec("Pareto - Causas")
        if not inf.empty and "SA_REPARO_INFANCIA" in inf.columns:
            sas = inf["SA_REPARO_INFANCIA"].dropna().unique()
            rows = ds[ds["Número SA"].isin(sas)] if len(sas) else pd.DataFrame()
            if not rows.empty and "Descrição" in rows.columns:
                caus = rows["Descrição"].value_counts().head(10).reset_index()
                caus.columns = ["Causa", "Qtd"]
                caus["L"] = caus["Causa"].astype(str).str[:50] + "..."
                st.plotly_chart(_bar_h(caus["L"], caus["Qtd"], C["purple"], "Top 10 Causas Infancia", h=380),
                                use_container_width=True)
            else:
                st.info("Sem dados de causa.")
        else:
            st.info("Sem dados de causa.")
    
    with c2:
        _sec("Pareto - Tecnicos")
        top = tb[tb["Infancia"] > 0].sort_values("Infancia", ascending=False).head(15)
        if not top.empty:
            st.plotly_chart(_bar_h(top["Nome"], top["Infancia"], C["purple"],
                                   "Tecnicos c/ mais Infancia", h=380, labels=top["TR"]),
                            use_container_width=True)
        else:
            st.success("Nenhum tecnico com infancia.")

    _sec("Evolucoes")
    tab1, tab2 = st.tabs(["📅 Semanal", "📆 Mensal"])
    inst_sc = ds[
        (ds["Macro Atividade"] == "INST-FTTH") &
        (ds["Estado"] == "CONCLUÍDO COM SUCESSO")
    ].copy()
    _flag_inf_col = "vip_flag_infancia" if _usa_vip_inf else "FLAG_INFANCIA_30D"
    inf_sc = ds[ds[_flag_inf_col] == "SIM"].copy() if _flag_inf_col in ds.columns else pd.DataFrame()
    
    with tab1:
        if not inf_sc.empty and "SEM_FIM" in inf_sc.columns:
            is_ = inf_sc.groupby("SEM_FIM").size().reset_index(name="Inf")
            ds2 = inst_sc.groupby("SEM_FIM").size().reset_index(name="Den") if not inst_sc.empty else pd.DataFrame(columns=["SEM_FIM", "Den"])
            ev = is_.merge(ds2, on="SEM_FIM", how="outer").fillna(0)
            ev["Taxa"] = (ev["Inf"] / ev["Den"].replace(0, 1) * 100).round(2)
            ev = ev[ev["SEM_FIM"].notna()].sort_values("SEM_FIM").tail(12)
            ev["SEM_FIM"] = "S" + ev["SEM_FIM"].astype(str).str.zfill(2)
            st.plotly_chart(_ev_dual(ev["SEM_FIM"], ev["Inf"], ev["Taxa"],
                                      C["purple"], "Evolucao Semanal"), use_container_width=True)
        else:
            st.info("Sem dados para evolução semanal.")
    
    with tab2:
        if not inf_sc.empty and "MES_FIM" in inf_sc.columns:
            im = inf_sc.groupby("MES_FIM").size().reset_index(name="Inf")
            dm2 = inst_sc.groupby("MES_FIM").size().reset_index(name="Den") if not inst_sc.empty else pd.DataFrame(columns=["MES_FIM", "Den"])
            ev2 = im.merge(dm2, on="MES_FIM", how="outer").fillna(0)
            ev2["Taxa"] = (ev2["Inf"] / ev2["Den"].replace(0, 1) * 100).round(2)
            ev2["MES_FIM"] = ev2["MES_FIM"].astype(str)
            ev2 = ev2.sort_values("MES_FIM").tail(12)
            st.plotly_chart(_ev_dual(ev2["MES_FIM"], ev2["Inf"], ev2["Taxa"],
                                      C["purple"], "Evolucao Mensal"), use_container_width=True)
        else:
            st.info("Sem dados para evolução mensal.")

    ta, tb2 = st.tabs(["📂 Infancia Aberta", "🚨 Infancia Alarmada"])
    with ta:
        _sec("Instalacoes com Reparo em Andamento")
        if rep_ab.empty:
            st.success("Nenhuma instalacao com reparo aberto.")
        else:
            ok = [c for c in ["Número SA", "FSLOI_GPONAccess", "CODIGO_TECNICO_EXTRAIDO",
                               "NOME_TEC", "Estado", "DIA_AB", "ALARMADO"] if c in rep_ab.columns]
            st.dataframe(rep_ab[ok].rename(columns={
                "Número SA": "SA", "FSLOI_GPONAccess": "GPON",
                "CODIGO_TECNICO_EXTRAIDO": "TR", "NOME_TEC": "Tecnico", "DIA_AB": "Abertura"}),
                use_container_width=True, hide_index=True)
    with tb2:
        _sec("Instalacoes com GPON Alarmado")
        if inf_alrm.empty:
            st.success("Nenhuma infancia alarmada.")
        else:
            ok = [c for c in ["Número SA", "FSLOI_GPONAccess", "CODIGO_TECNICO_EXTRAIDO",
                               "NOME_TEC", "SA_REPARO_INFANCIA", "Alarm ID"] if c in inf_alrm.columns]
            st.dataframe(inf_alrm[ok].rename(columns={
                "Número SA": "SA Inst.", "FSLOI_GPONAccess": "GPON",
                "CODIGO_TECNICO_EXTRAIDO": "TR", "NOME_TEC": "Tecnico",
                "SA_REPARO_INFANCIA": "SA Reparo", "Alarm ID": "Alarme"}),
                use_container_width=True, hide_index=True)

# =============================================================================
# 11. TELA — DIARIO
# =============================================================================

def tela_diario(df, ds, f):
    _header("📅", "Controle do Dia", f)

    datas_disp = sorted(ds["FIM_DT"].dropna().dt.date.unique(), reverse=True)
    if not datas_disp:
        st.warning("Nenhuma data disponivel.")
        return

    c_pick, c_info = st.columns([2, 5])
    with c_pick:
        dia_sel = st.date_input("Data de referencia",
            value=datas_disp[0],
            min_value=datas_disp[-1],
            max_value=datas_disp[0],
            key="dia_ref")

    dm = ds[ds["FIM_DT"].dt.date == dia_sel].copy()
    dm_ab = ds[ds["AB_DT"].dt.date == dia_sel].copy()

    suc = dm[dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
    sem_suc = dm[dm["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM"]
    inst_d = suc[suc["Macro Atividade"] == "INST-FTTH"]
    rep_d = suc[suc["Macro Atividade"] == "REP-FTTH"]
    tecs_atv = suc["CODIGO_TECNICO_EXTRAIDO"].nunique()
    efic = round(len(suc) / (len(suc) + len(sem_suc)) * 100, 1) if (len(suc) + len(sem_suc)) > 0 else 0

    with c_info:
        st.markdown(
            f"<div style='margin-top:28px;font-size:12px;color:#64748b;'>"
            f"<b>{dia_sel.strftime('%d/%m/%Y')}</b> — "
            f"{tecs_atv} tecnicos ativos | {len(suc)+len(sem_suc)} atividades concluidas</div>",
            unsafe_allow_html=True)

    rep_dia_ab = dm_ab[dm_ab["FLAG_REPETIDO_30D"] == "SIM"] if "FLAG_REPETIDO_30D" in dm_ab.columns else pd.DataFrame()
    rep_ab_tot = ds[ds["FLAG_REPETIDO_ABERTO"] == "SIM"] if "FLAG_REPETIDO_ABERTO" in ds.columns else pd.DataFrame()
    inf_dia = suc[suc["FLAG_INFANCIA_30D"] == "SIM"] if "FLAG_INFANCIA_30D" in suc.columns else pd.DataFrame()
    p0_10 = ds[(ds["FIM_DT"].dt.date == dia_sel) & (ds["FLAG_P0_10_DIA"] == "SIM")] if "FLAG_P0_10_DIA" in ds.columns else pd.DataFrame()
    p0_15 = ds[(ds["FIM_DT"].dt.date == dia_sel) & (ds["FLAG_P0_15_DIA"] == "SIM")] if "FLAG_P0_15_DIA" in ds.columns else pd.DataFrame()

    cols = st.columns(7)
    for col, (lb, vl, sb, cl) in zip(cols, [
        ("Concluidos",    f"{len(suc):,}",  f"INST:{len(inst_d)} REP:{len(rep_d)}", "kpi-blue"),
        ("Eficacia",      f"{efic}%",        "suc/total",   "kpi-green" if efic>=85 else "kpi-yellow" if efic>=70 else "kpi-red"),
        ("Sem Sucesso",   f"{len(sem_suc):,}", "pendencias",  "kpi-red" if len(sem_suc)>0 else "kpi-green"),
        ("Rep. Dia",      f"{len(rep_dia_ab):,}", "abertos hoje", "kpi-red" if len(rep_dia_ab)>0 else "kpi-green"),
        ("Rep. Abertos",  f"{len(rep_ab_tot):,}", "em garantia", "kpi-yellow" if len(rep_ab_tot)>0 else "kpi-green"),
        ("P0 10h",        f"{p0_10['CODIGO_TECNICO_EXTRAIDO'].nunique()}", "tecnicos", "kpi-red" if not p0_10.empty else "kpi-green"),
        ("P0 15h",        f"{p0_15['CODIGO_TECNICO_EXTRAIDO'].nunique()}", "tecnicos", "kpi-red" if not p0_15.empty else "kpi-green"),
    ]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")

    _sec("Produtividade por Tecnico")
    
    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""
    
    if suc.empty:
        st.info("Nenhuma atividade concluida neste dia.")
    else:
        pt = suc.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
            Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])),
            Total=("Número SA", "count"),
            INST=("Macro Atividade", lambda x: (x == "INST-FTTH").sum()),
            REP=("Macro Atividade", lambda x: (x == "REP-FTTH").sum()),
        ).reset_index()
        ss_tec = sem_suc.groupby("CODIGO_TECNICO_EXTRAIDO").size().reset_index(name="SemSuc")
        pt = pt.merge(ss_tec, on="CODIGO_TECNICO_EXTRAIDO", how="left")
        pt["SemSuc"] = pt["SemSuc"].fillna(0).astype(int)
        pt["Efic%"] = (pt["Total"] / (pt["Total"] + pt["SemSuc"]).replace(0, 1) * 100).round(1)
        pt = pt.sort_values("Total", ascending=False).reset_index(drop=True)
        pt.columns = ["TR", "Nome", "Total", "INST", "REP", "Sem Suc.", "Eficacia%"]
        st.dataframe(pt, use_container_width=True, hide_index=True,
                     column_config={
                         "Total": st.column_config.ProgressColumn("Total", format="%d", min_value=0,
                                   max_value=int(pt["Total"].max()) if not pt.empty else 1),
                         "Eficacia%": st.column_config.ProgressColumn("Eficacia%", format="%.1f%%", min_value=0, max_value=100),
                     })

    _sec("Sem Sucesso — Pendencias do Dia")
    if sem_suc.empty:
        st.success("Nenhuma pendencia no dia.")
    else:
        ok = [c for c in ["Número SA", "CODIGO_TECNICO_EXTRAIDO", "NOME_TEC",
                           "Macro Atividade", "Descrição", "Observação",
                           "Código de encerramento"] if c in sem_suc.columns]
        st.dataframe(sem_suc[ok].rename(columns={
            "Número SA": "SA", "CODIGO_TECNICO_EXTRAIDO": "TR", "NOME_TEC": "Tecnico",
            "Macro Atividade": "Tipo", "Código de encerramento": "Cod. Enc."}),
            use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        _sec("Repetidos Abertos no Dia")
        if rep_dia_ab.empty:
            st.success("Nenhum repetido aberto hoje.")
        else:
            ok = [c for c in ["Número SA", "CODIGO_TECNICO_EXTRAIDO", "NOME_TEC",
                               "FSLOI_GPONAccess", "ALARMADO"] if c in rep_dia_ab.columns]
            st.dataframe(rep_dia_ab[ok].rename(columns={
                "Número SA": "SA", "CODIGO_TECNICO_EXTRAIDO": "TR",
                "NOME_TEC": "Tecnico", "FSLOI_GPONAccess": "GPON"}),
                use_container_width=True, hide_index=True)
    with c2:
        _sec("Repetidos em Garantia (Abertos)")
        if rep_ab_tot.empty:
            st.success("Nenhum reparo em garantia.")
        else:
            ok = [c for c in ["Número SA", "CODIGO_TECNICO_EXTRAIDO", "NOME_TEC",
                               "FSLOI_GPONAccess", "DIA_AB", "ALARMADO"] if c in rep_ab_tot.columns]
            st.dataframe(rep_ab_tot[ok].rename(columns={
                "Número SA": "SA", "CODIGO_TECNICO_EXTRAIDO": "TR",
                "NOME_TEC": "Tecnico", "FSLOI_GPONAccess": "GPON", "DIA_AB": "Abertura"}),
                use_container_width=True, hide_index=True)

    c3, c4 = st.columns(2)
    with c3:
        _sec("Infancia — Instalacoes do Dia")
        if inf_dia.empty:
            st.success("Nenhuma infancia hoje.")
        else:
            ok = [c for c in ["Número SA", "CODIGO_TECNICO_EXTRAIDO", "NOME_TEC",
                               "FSLOI_GPONAccess", "SA_REPARO_INFANCIA"] if c in inf_dia.columns]
            st.dataframe(inf_dia[ok].rename(columns={
                "Número SA": "SA Inst.", "CODIGO_TECNICO_EXTRAIDO": "TR",
                "NOME_TEC": "Tecnico", "FSLOI_GPONAccess": "GPON",
                "SA_REPARO_INFANCIA": "SA Reparo"}),
                use_container_width=True, hide_index=True)
    with c4:
        _sec("Infancia Aberta (Reparo em Andamento)")
        estados_ab = ["ATRIBUÍDO", "NÃO ATRIBUÍDO", "RECEBIDO", "EM EXECUÇÃO", "EM DESLOCAMENTO"]
        gpons_suc = set(suc["FSLOI_GPONAccess"].dropna().str.upper())
        inf_ab_dia = ds[
            (ds["Macro Atividade"] == "REP-FTTH") &
            (ds["Estado"].isin(estados_ab)) &
            (ds["FLAG_INFANCIA_30D"] == "SIM") &
            (ds["FSLOI_GPONAccess"].str.upper().isin(gpons_suc))
        ] if "FLAG_INFANCIA_30D" in ds.columns else pd.DataFrame()
        if inf_ab_dia.empty:
            st.success("Nenhuma infancia aberta.")
        else:
            ok = [c for c in ["Número SA", "CODIGO_TECNICO_EXTRAIDO", "NOME_TEC",
                               "FSLOI_GPONAccess", "Estado"] if c in inf_ab_dia.columns]
            st.dataframe(inf_ab_dia[ok].rename(columns={
                "Número SA": "SA", "CODIGO_TECNICO_EXTRAIDO": "TR",
                "NOME_TEC": "Tecnico", "FSLOI_GPONAccess": "GPON"}),
                use_container_width=True, hide_index=True)

    _sec("P0 — Controle de Encerramento")
    cp1, cp2 = st.columns(2)
    with cp1:
        st.markdown("**P0 10h — Nao encerraram ate as 10h**")
        if p0_10.empty:
            st.success("Todos encerraram ate 10h.")
        else:
            t10 = p0_10.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
                Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])),
                Qtd=("Número SA", "count")).reset_index()
            t10.columns = ["TR", "Nome", "Qtd"]
            st.dataframe(t10, use_container_width=True, hide_index=True)
    with cp2:
        st.markdown("**P0 15h — Nao encerraram ate as 15h**")
        if p0_15.empty:
            st.success("Todos encerraram ate 15h.")
        else:
            t15 = p0_15.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
                Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])),
                Qtd=("Número SA", "count")).reset_index()
            t15.columns = ["TR", "Nome", "Qtd"]
            st.dataframe(t15, use_container_width=True, hide_index=True)

# =============================================================================
# 12. TELA — CALENDARIO MENSAL
# =============================================================================

def tela_calendario(df, ds, f):
    import calendar as _cal
    _header("📆", "Calendario Mensal", f)

    mes_str = f["mes"]
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        st.error("Mes invalido.")
        return

    hoje = datetime.now()
    dias_mes = _cal.monthrange(ano, mes)[1]
    dia_max = hoje.day if (ano == hoje.year and mes == hoje.month) else dias_mes
    dias_range = list(range(1, dia_max + 1))
    meses_pt = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    lbl_mes = f"{meses_pt[mes-1]}/{ano}"

    df_m = ds[(ds["FIM_DT"].dt.year == ano) & (ds["FIM_DT"].dt.month == mes)].copy()
    df_m["DIA"] = df_m["FIM_DT"].dt.day.astype(int)
    suc_m = df_m[df_m["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
    semsuc_m = df_m[df_m["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM"]

    if suc_m.empty:
        st.warning("Sem dados de producao para o mes selecionado.")
        return

    tecs = suc_m["CODIGO_TECNICO_EXTRAIDO"].nunique()
    efic = round(len(suc_m) / (len(suc_m) + len(semsuc_m)) * 100, 1) if (len(suc_m) + len(semsuc_m)) > 0 else 0
    
    cols = st.columns(5)
    for col, (lb, vl, sb, cl) in zip(cols, [
        ("Tecnicos Ativos", f"{tecs}", lbl_mes, "kpi-blue"),
        ("Concluidos", f"{len(suc_m):,}", "c/ sucesso", "kpi-blue"),
        ("INST", f"{(suc_m['Macro Atividade'] == 'INST-FTTH').sum():,}", "", "kpi-blue"),
        ("REP", f"{(suc_m['Macro Atividade'] == 'REP-FTTH').sum():,}", "", "kpi-purple"),
        ("Eficacia", f"{efic}%", "suc/total", "kpi-green" if efic >= 85 else "kpi-yellow"),
    ]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")

    st.markdown("""
    <div style="display:flex;gap:10px;margin-bottom:10px;font-size:11px;align-items:center;">
        <span style="background:#1e3a5f;color:white;padding:2px 8px;border-radius:4px;">≥5</span>
        <span style="background:#d4edda;color:#155724;padding:2px 8px;border-radius:4px;">=4</span>
        <span style="background:#fff3cd;color:#856404;padding:2px 8px;border-radius:4px;">=3</span>
        <span style="background:#ffcccc;color:#721c24;padding:2px 8px;border-radius:4px;">1-2</span>
        <span style="background:#f0f0f0;color:#6c757d;padding:2px 8px;border-radius:4px;">0</span>
        <span style="color:#64748b;margin-left:4px;">= atividades no dia</span>
    </div>
    """, unsafe_allow_html=True)

    _sec(f"Producao por Tecnico — {lbl_mes}")

    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    suc_range = suc_m[suc_m["DIA"].isin(dias_range)]
    pivot = suc_range.groupby(["CODIGO_TECNICO_EXTRAIDO", "DIA"]).size().unstack(fill_value=0)
    for d in dias_range:
        if d not in pivot.columns:
            pivot[d] = 0
    pivot = pivot[dias_range]

    nomes = suc_m.groupby("CODIGO_TECNICO_EXTRAIDO")["Técnico Atribuído"].first().apply(_n)
    ss_tec = semsuc_m.groupby("CODIGO_TECNICO_EXTRAIDO").size()
    dias_trab = suc_range.groupby("CODIGO_TECNICO_EXTRAIDO")["DIA"].nunique()

    pivot.insert(0, "Nome", nomes)
    pivot["Total"] = pivot[dias_range].sum(axis=1)
    pivot["Sem Suc."] = ss_tec.reindex(pivot.index).fillna(0).astype(int)
    pivot["Dias"] = dias_trab.reindex(pivot.index).fillna(0).astype(int)
    pivot["Media"] = (pivot["Total"] / pivot["Dias"].replace(0, 1)).round(1)
    pivot["Eficacia%"] = (pivot["Total"] / (pivot["Total"] + pivot["Sem Suc."]).replace(0, 1) * 100).round(1)
    pivot = pivot.sort_values("Total", ascending=False).reset_index()
    pivot = pivot.rename(columns={"CODIGO_TECNICO_EXTRAIDO": "TR"})

    cols_dia = [str(d) for d in dias_range]
    cols_order = ["Nome", "TR"] + dias_range + ["Dias", "Total", "Sem Suc.", "Media", "Eficacia%"]
    pivot = pivot[cols_order]
    pivot.columns = ["Nome", "TR"] + cols_dia + ["Dias", "Total", "Sem Suc.", "Media", "Eficacia%"]

    def _cor_cel(v):
        try:
            v = int(v)
        except Exception:
            return ""
        if v >= 5:
            return "background-color:#1e3a5f;color:white;font-weight:700;text-align:center"
        if v == 4:
            return "background-color:#d4edda;color:#155724;font-weight:600;text-align:center"
        if v == 3:
            return "background-color:#fff3cd;color:#856404;font-weight:600;text-align:center"
        if v in (1, 2):
            return "background-color:#ffcccc;color:#721c24;text-align:center"
        return "background-color:#f0f0f0;color:#adb5bd;text-align:center"

    try:
        styled = pivot.style.map(_cor_cel, subset=cols_dia)
    except AttributeError:
        styled = pivot.style.applymap(_cor_cel, subset=cols_dia)

    max_p = int(pivot["Total"].max()) if not pivot.empty else 1
    altura_total = 38 + (len(pivot) * 35)

    st.dataframe(styled, use_container_width=True, hide_index=True,
                 column_config={
                     "Nome": st.column_config.TextColumn("Nome", width="medium"),
                     "TR": st.column_config.TextColumn("TR", width="small"),
                     "Total": st.column_config.ProgressColumn("Total", format="%d", min_value=0, max_value=max_p),
                     "Eficacia%": st.column_config.ProgressColumn("Eficacia%", format="%.1f%%", min_value=0, max_value=100),
                     "Media": st.column_config.NumberColumn("Media", format="%.1f"),
                 }, height=altura_total)

    _sec("Eficacia Diaria do Mes")
    ef_list = []
    for d in dias_range:
        rows = df_m[df_m["DIA"] == d]
        s = (rows["FLAG_CONCLUIDO_SUCESSO"] == "SIM").sum()
        ss = (rows["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM").sum()
        ef_list.append({
            "DIA": d,
            "Concluidos": s,
            "Eficacia%": round(s / max(s + ss, 1) * 100, 1),
        })
    ef_dia = pd.DataFrame(ef_list)

    fig = go.Figure()
    fig.add_bar(x=ef_dia["DIA"].astype(str), y=ef_dia["Concluidos"],
                name="Concluidos", marker_color=C["navy"], yaxis="y")
    fig.add_scatter(x=ef_dia["DIA"].astype(str), y=ef_dia["Eficacia%"],
                    name="Eficacia%", mode="lines+markers",
                    line=dict(color=C["green"], width=2), marker_size=6, yaxis="y2")
    fig.add_hline(y=85, line_dash="dash", line_color=C["yellow"],
                  annotation_text="Meta 85%", yref="y2")
    fig.update_layout(
        **_lyt(f"Producao e Eficacia — {lbl_mes}", 320),
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    tickfont_color=C["green"], range=[0, 110]),
        showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 13. TELA — QUALIDADE
# =============================================================================

def tela_qualidade(dm, ds, f):
    _header("🏆", "Qualidade", f)

    def _n(v):
        return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    mes_ref = f.get("mes", "")
    tecs = sorted(dm["CODIGO_TECNICO_EXTRAIDO"].dropna().unique())
    if not tecs:
        st.warning("Nenhum tecnico encontrado para os filtros selecionados.")
        return

    def _cls_prod(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ("S/D", "⬜", "#94a3b8", 0)
        v = float(v)
        if v >= 6:   return ("EXCELENTE", "🏆", "#1e3a5f", 4)
        if v >= 4:   return ("PARABENS", "🟢", "#16a34a", 3)
        if v >= 3:   return ("ATENCAO", "🟡", "#d97706", 2)
        if v >= 1:   return ("PRECISA MELHORAR", "🔴", "#dc2626", 1)
        return ("PRECISA MELHORAR", "🔴", "#dc2626", 1)

    def _cls_efic(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ("S/D", "⬜", "#94a3b8", 0)
        v = float(v)
        if v >= 85:  return ("EXCELENTE", "🏆", "#1e3a5f", 4)
        if v >= 82:  return ("PARABENS", "🟢", "#16a34a", 3)
        if v >= 75:  return ("ATENCAO", "🟡", "#d97706", 2)
        return ("PRECISA MELHORAR", "🔴", "#dc2626", 1)

    def _cls_rep(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ("S/D", "⬜", "#94a3b8", 0)
        v = float(v)
        if v < 2:    return ("EXCELENTE", "🏆", "#1e3a5f", 4)
        if v <= 5:   return ("OTIMO", "🟢", "#16a34a", 3)
        if v <= 9:   return ("PARABENS", "🟢", "#16a34a", 2)
        return ("PRECISA MELHORAR", "🔴", "#dc2626", 0)

    def _cls_inf(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ("S/D", "⬜", "#94a3b8", 0)
        v = float(v)
        if v < 3:    return ("OTIMO", "🟢", "#16a34a", 3)
        return ("PRECISA MELHORAR", "🔴", "#dc2626", 0)

    def _nota_total(pc, ec, rc, ic):
        return pc[3] + ec[3] + rc[3] + ic[3]

    def _cor_nota(n):
        if n >= 13: return "#1e3a5f"
        if n >= 9:  return "#16a34a"
        if n >= 5:  return "#d97706"
        return "#dc2626"

    rows = []
    for cod in tecs:
        df_t = dm[dm["CODIGO_TECNICO_EXTRAIDO"] == cod].copy()
        if df_t.empty:
            continue

        nome = _n(df_t["Técnico Atribuído"].dropna().iloc[0]) if not df_t["Técnico Atribuído"].dropna().empty else cod

        suc = df_t[df_t["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
        dias_unicos = suc["DIA_FIM"].dropna().nunique()
        prod_media = round(len(suc) / dias_unicos, 1) if dias_unicos > 0 else None

        n_suc = (df_t["FLAG_CONCLUIDO_SUCESSO"] == "SIM").sum()
        n_ss = (df_t["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM").sum()
        efic = round(n_suc / (n_suc + n_ss) * 100, 1) if (n_suc + n_ss) > 0 else None

        dados_rep = contar_reparos_repetidos_por_tecnico(ds, cod, mes_ref)
        rep_den = dados_rep["total_reparos"]
        rep_num = dados_rep["reparos_repetidos"]
        rep_pct = dados_rep["taxa"]

        inst_den = (df_t["FLAG_INSTALACAO_VALIDA"] == "SIM").sum() if "FLAG_INSTALACAO_VALIDA" in df_t.columns else 0
        inst_num = ((df_t.get("FLAG_INSTALACAO_VALIDA", "NAO") == "SIM") &
                    (df_t["vip_flag_infancia"] == "SIM")).sum() if inst_den > 0 else 0
        inf_pct = round(inst_num / inst_den * 100, 1) if inst_den > 0 else None

        pc = _cls_prod(prod_media)
        ec = _cls_efic(efic)
        rc = _cls_rep(rep_pct)
        ic = _cls_inf(inf_pct)
        nota = _nota_total(pc, ec, rc, ic)

        rows.append({
            "cod": cod,
            "nome": nome,
            "prod_media": prod_media,
            "efic_pct": efic,
            "rep_pct": rep_pct,
            "inf_pct": inf_pct,
            "prod_cls": pc,
            "efic_cls": ec,
            "rep_cls": rc,
            "inf_cls": ic,
            "nota": nota,
            "n_suc": n_suc,
            "dias": dias_unicos,
        })

    if not rows:
        st.warning("Sem dados suficientes para calcular indicadores.")
        return

    df_q = pd.DataFrame(rows).sort_values("nota", ascending=False).reset_index(drop=True)

    n_exc = (df_q["nota"] >= 13).sum()
    n_bom = ((df_q["nota"] >= 9) & (df_q["nota"] < 13)).sum()
    n_atc = ((df_q["nota"] >= 5) & (df_q["nota"] < 9)).sum()
    n_mel = (df_q["nota"] < 5).sum()

    cols_kpi = st.columns(5)
    for col, lbl, val, cls in zip(
        cols_kpi,
        ["Tecnicos", "🏆 Excelente", "✅ Bom", "⚠️ Atencao", "🔴 Melhoria"],
        [len(df_q), n_exc, n_bom, n_atc, n_mel],
        ["kpi-blue", "kpi-blue", "kpi-green", "kpi-yellow", "kpi-red"],
    ):
        col.markdown(_kpi(lbl, val, "", cls), unsafe_allow_html=True)

    st.write("")

    with st.expander("📋 Regras de classificacao", expanded=False):
        st.markdown("""
| Indicador | 🏆 Excelente | 🟢 Parabens / Otimo | 🟡 Atencao | 🔴 Precisa Melhorar |
|---|---|---|---|---|
| **Produtividade** (ativ/dia) | ≥ 6 | 4 ou 5 = Parabens | 3 | ≤ 2 |
| **Eficacia** (%) | ≥ 85% | 82–85% | 75–82% | < 75% |
| **Repetida** (%) | < 2% | 2–5% = Otimo · 5–9% = Parabens | — | > 9% |
| **Infancia** (%) | — | < 3% = Otimo | — | ≥ 3% |

**Pontuacao:** cada indicador vale 0–4 pontos. Total 0–16.
≥13 Excelente | 9–12 Bom | 5–8 Atencao | <5 Precisa Melhorar
        """)

    _sec("Ranking de Qualidade por Tecnico")

    disp = []
    for _, r in df_q.iterrows():
        pv = f"{r['prod_media']:.1f}" if r['prod_media'] is not None else "S/D"
        ev = f"{r['efic_pct']:.1f}%" if r['efic_pct'] is not None else "S/D"
        rv = f"{r['rep_pct']:.1f}%" if r['rep_pct'] is not None else "S/D"
        iv = f"{r['inf_pct']:.1f}%" if r['inf_pct'] is not None else "S/D"
        disp.append({
            "Nome": r["nome"],
            "TR": r["cod"],
            "Prod.": pv,
            "Prod_S": r["prod_cls"][0],
            "Efic.": ev,
            "Efic_S": r["efic_cls"][0],
            "Repet.": rv,
            "Rep_S": r["rep_cls"][0],
            "Infan.": iv,
            "Inf_S": r["inf_cls"][0],
            "Nota": f"{r['nota']}/16",
        })

    df_disp = pd.DataFrame(disp)

    _cor_map = {
        "EXCELENTE": "background-color:#1e3a5f;color:white;font-weight:700",
        "PARABENS": "background-color:#16a34a;color:white;font-weight:700",
        "OTIMO": "background-color:#15803d;color:white;font-weight:700",
        "ATENCAO": "background-color:#d97706;color:white;font-weight:700",
        "PRECISA MELHORAR": "background-color:#dc2626;color:white;font-weight:700",
        "S/D": "background-color:#e2e8f0;color:#64748b",
    }
    
    def _cor(v):
        return _cor_map.get(v, "")

    _scols = ["Prod_S", "Efic_S", "Rep_S", "Inf_S"]
    try:
        styled = df_disp.style.applymap(_cor, subset=_scols)
    except AttributeError:
        styled = df_disp.style.map(_cor, subset=_scols)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=min(60 + len(df_disp) * 36, 700),
        column_config={
            "Nome": st.column_config.TextColumn("Nome", width="medium"),
            "TR": st.column_config.TextColumn("TR", width="small"),
            "Nota": st.column_config.TextColumn("Nota", width="small"),
            "Prod.": st.column_config.TextColumn("Prod.ativ/dia", width="small"),
            "Efic.": st.column_config.TextColumn("Eficacia", width="small"),
            "Repet.": st.column_config.TextColumn("Repetida", width="small"),
            "Infan.": st.column_config.TextColumn("Infancia", width="small"),
            "Prod_S": st.column_config.TextColumn("Status Prod.", width="medium"),
            "Efic_S": st.column_config.TextColumn("Status Efic.", width="medium"),
            "Rep_S": st.column_config.TextColumn("Status Rep.", width="medium"),
            "Inf_S": st.column_config.TextColumn("Status Inf.", width="medium"),
        }
    )

    st.write("")
    _sec("Distribuicao de Classificacoes por Indicador")

    _cats = ["EXCELENTE", "OTIMO", "PARABENS", "ATENCAO", "PRECISA MELHORAR", "S/D"]
    _cores = ["#1e3a5f", "#15803d", "#16a34a", "#d97706", "#dc2626", "#94a3b8"]
    _inds = ["prod_cls", "efic_cls", "rep_cls", "inf_cls"]
    _lbls = ["Produtividade", "Eficacia", "Repetida", "Infancia"]

    fig_dist = go.Figure()
    for cat, cor in zip(_cats, _cores):
        vals = [
            (df_q[ind].apply(lambda x: x[0]) == cat).sum()
            for ind in _inds
        ]
        if sum(vals) == 0:
            continue
        fig_dist.add_trace(go.Bar(
            name=cat, x=_lbls, y=vals,
            marker_color=cor,
            text=[v if v > 0 else "" for v in vals],
            textposition="auto", textfont_size=11,
        ))

    fig_dist.update_layout(
        **_lyt("Distribuicao por Indicador e Classificacao", 340),
        barmode="stack",
        yaxis=dict(title="Qtd. Tecnicos", gridcolor=C["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_dist, use_container_width=True)

    _sec("Gerar Atas de Qualidade — Assinatura Digital")
    st.caption(
        "Clique em 📄 ATA para baixar o formulario HTML. "
        "Abra no navegador, assine digitalmente e clique em Salvar Ata e Gerar PDF."
    )

    sup_nome = f.get("supervisor", "N/I") or "N/I"

    for _, r in df_q.iterrows():
        pv = f"{r['prod_media']:.1f} /dia" if r['prod_media'] is not None else "S/D"
        ev = f"{r['efic_pct']:.1f}%" if r['efic_pct'] is not None else "S/D"
        rv = f"{r['rep_pct']:.1f}%" if r['rep_pct'] is not None else "S/D"
        iv = f"{r['inf_pct']:.1f}%" if r['inf_pct'] is not None else "S/D"

        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 1, 1, 1, 1, 1, 1])

        with c1:
            st.write(f"**{r['nome']}** `{r['cod']}`")
        with c2:
            pc = r["prod_cls"]
            st.markdown(f'<span style="color:{pc[2]};font-weight:700">{pc[1]} {pv}</span>',
                        unsafe_allow_html=True)
        with c3:
            ec = r["efic_cls"]
            st.markdown(f'<span style="color:{ec[2]};font-weight:700">{ec[1]} {ev}</span>',
                        unsafe_allow_html=True)
        with c4:
            rc = r["rep_cls"]
            st.markdown(f'<span style="color:{rc[2]};font-weight:700">{rc[1]} {rv}</span>',
                        unsafe_allow_html=True)
        with c5:
            ic = r["inf_cls"]
            st.markdown(f'<span style="color:{ic[2]};font-weight:700">{ic[1]} {iv}</span>',
                        unsafe_allow_html=True)
        with c6:
            cor_n = _cor_nota(r["nota"])
            st.markdown(
                f'<span style="color:{cor_n};font-weight:800;font-size:15px">{r["nota"]}/16</span>',
                unsafe_allow_html=True)
        with c7:
            if st.button("📄 ATA", key=f"ata_q_{r['cod']}"):
                html_content = _html_ata_qualidade(
                    nome=r["nome"],
                    codigo=r["cod"],
                    supervisor=sup_nome,
                    mes_ref=mes_ref,
                    prod_val=pv,
                    efic_val=ev,
                    rep_val=rv,
                    inf_val=iv,
                    prod_cls=r["prod_cls"],
                    efic_cls=r["efic_cls"],
                    rep_cls=r["rep_cls"],
                    inf_cls=r["inf_cls"],
                    nota=r["nota"],
                )
                fname = f"ata_qualidade_{r['cod']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                b64 = base64.b64encode(html_content.encode()).decode()
                href = (
                    f'<a href="data:text/html;base64,{b64}" download="{fname}" target="_blank" '
                    f'style="display:inline-block;background:#1e3a5f;color:white;padding:5px 12px;'
                    f'border-radius:5px;text-decoration:none;font-size:11px;font-weight:700">'
                    f'📥 Baixar</a>'
                )
                st.markdown(href, unsafe_allow_html=True)


def _html_ata_qualidade(nome, codigo, supervisor, mes_ref,
                        prod_val, efic_val, rep_val, inf_val,
                        prod_cls, efic_cls, rep_cls, inf_cls, nota):
    nota_max = 16
    if nota >= 13:
        cor_h = "135deg,#1a6c5c 0%,#2ca08c 100%"
        titulo = "🏆 ATA DE RECONHECIMENTO — DESEMPENHO EXCELENTE"
        msg = (f"Prezado(a) <strong>{nome}</strong>, seu desempenho no periodo foi "
               f"excepcional. Todos os indicadores estao dentro ou acima das metas. Continue assim!")
    elif nota >= 9:
        cor_h = "135deg,#1a3a8f 0%,#2563eb 100%"
        titulo = "✅ ATA DE QUALIDADE — BOM DESEMPENHO"
        msg = (f"Prezado(a) <strong>{nome}</strong>, seu desempenho esta dentro das metas "
               f"esperadas. Identifique os pontos de atencao para atingir a excelencia.")
    elif nota >= 5:
        cor_h = "135deg,#b45309 0%,#d97706 100%"
        titulo = "⚠️ ATA DE ATENCAO — PONTOS DE MELHORIA"
        msg = (f"Prezado(a) <strong>{nome}</strong>, ha indicadores que precisam de atencao. "
               f"Vamos alinhar um plano de acao para a melhoria do desempenho.")
    else:
        cor_h = "135deg,#a8433d 0%,#c0392b 100%"
        titulo = "🔴 ATA DE ACOMPANHAMENTO — NECESSITA MELHORIA"
        msg = (f"Prezado(a) <strong>{nome}</strong>, seus indicadores estao abaixo das metas "
               f"estabelecidas. E necessario um plano de acao imediato.")

    def _badge(label, cor):
        return (f'<span style="background:{cor};color:white;padding:2px 10px;'
                f'border-radius:12px;font-size:11px;font-weight:700">{label}</span>')

    def _ind(lbl, val, cls):
        return (f'<div style="flex:1;min-width:140px;border:1px solid #e2e8f0;border-radius:8px;'
                f'padding:14px;text-align:center">'
                f'<div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">{lbl}</div>'
                f'<div style="font-size:20px;font-weight:700;color:#1a3a8f;margin-bottom:8px">{val}</div>'
                f'{_badge(cls[0], cls[2])}'
                f'</div>')

    inds_html = (
        _ind("Produtividade", prod_val, prod_cls) +
        _ind("Eficacia", efic_val, efic_cls) +
        _ind("Repetida", rep_val, rep_cls) +
        _ind("Infancia", inf_val, inf_cls)
    )

    cod_safe = codigo.replace("'", "\\'")
    nome_safe = nome.replace("'", "\\'")
    sup_safe = supervisor.replace("'", "\\'")
    ts_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    dt_now = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Ata — {nome}</title>
<script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}}
body{{background:#f5f7fa;padding:20px;color:#333;line-height:1.6}}
.box{{max-width:860px;margin:0 auto;background:white;border-radius:12px;
      box-shadow:0 5px 25px rgba(0,0,0,.08);overflow:hidden}}
.hdr{{background:linear-gradient({cor_h});color:white;padding:24px 30px}}
.hdr h1{{font-size:20px;margin-bottom:4px;font-weight:700}}
.hdr p{{font-size:12px;opacity:.9}}
.body{{padding:26px}}
.info{{background:#f0f4ff;border-radius:8px;padding:14px;margin-bottom:18px;
       border-left:4px solid #1a3a8f;font-size:13px}}
.info p{{margin:2px 0}}
.msg{{background:#f8fafc;padding:13px;border-radius:8px;font-style:italic;
      margin:16px 0;border-left:4px solid #1a3a8f;font-size:13px}}
.inds{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}}
.nota{{text-align:center;margin:16px 0}}
.nota span{{font-size:28px;font-weight:800;color:#1a3a8f}}
.sig-box{{background:#f9fafc;border-radius:8px;padding:14px;
          border:1px solid #eaeaea;margin-top:14px}}
.sig-title{{font-size:13px;color:#1a3a8f;margin-bottom:8px;font-weight:600}}
.sig-area{{position:relative;width:100%;height:120px;border:2px dashed #bdc3c7;
           border-radius:8px;background:white;margin-bottom:10px}}
.sig-canvas{{width:100%;height:100%;display:block;cursor:crosshair}}
.sig-ph{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
         color:#95a5a6;font-size:13px;text-align:center;pointer-events:none}}
.btns{{display:flex;gap:8px;margin-bottom:8px}}
.btn{{padding:8px 14px;border:none;border-radius:6px;font-weight:600;
      cursor:pointer;font-size:13px;flex:1}}
.bp{{background:#1a3a8f;color:white}}
.bs{{background:#ecf0f1;color:#333}}
.sig-info{{background:#e8f4fc;border-radius:8px;padding:10px;margin-top:6px;
           border-left:4px solid #1a3a8f;display:none;font-size:12px}}
.sig-info.on{{display:block}}
.btn-pdf{{background:#16a34a;color:white;border:none;border-radius:6px;
          padding:12px;font-size:15px;font-weight:700;cursor:pointer;
          width:100%;margin-top:18px}}
.rodape{{margin-top:16px;padding-top:12px;border-top:1px solid #eaeaea;
         font-size:11px;color:#94a3b8;text-align:center}}
@media(max-width:560px){{.inds{{flex-direction:column}}}}
</style>
</head>
<body>
<div class="box">
  <div class="hdr">
    <h1>{titulo}</h1>
    <p>Periodo: {mes_ref} &nbsp;·&nbsp; Gerado em: {dt_now}</p>
  </div>
  <div class="body">
    <div class="info">
      <p><strong>Nome:</strong> {nome}</p>
      <p><strong>Codigo:</strong> {codigo}</p>
      <p><strong>Supervisor:</strong> {supervisor}</p>
    </div>
    <div class="msg">{msg}</div>

    <h3 style="color:#1a3a8f;font-size:14px;margin-bottom:10px">📊 Indicadores do Periodo</h3>
    <div class="inds">{inds_html}</div>
    <div class="nota">Pontuacao: <span>{nota}/{nota_max}</span></div>

    <div class="sig-box">
      <div class="sig-title">✍️ Assinatura do Tecnico <span style="color:#ef4444">*</span></div>
      <div class="sig-area">
        <canvas id="cvT" class="sig-canvas"></canvas>
        <div id="phT" class="sig-ph">Assine aqui (obrigatorio)</div>
      </div>
      <div class="btns">
        <button class="btn bs" id="clrT">🧹 Limpar</button>
        <button class="btn bp" id="valT">✔ Validar</button>
      </div>
      <div id="infoT" class="sig-info">
        <strong>Tecnico:</strong> {nome} &nbsp;|&nbsp;
        <strong>Data/Hora:</strong> <span id="dtT">--</span>
      </div>
    </div>

    <div class="sig-box" style="margin-top:14px">
      <div class="sig-title">✍️ Assinatura do Supervisor <span style="color:#94a3b8">(opcional)</span></div>
      <div class="sig-area">
        <canvas id="cvS" class="sig-canvas"></canvas>
        <div id="phS" class="sig-ph">Assine aqui (opcional)</div>
      </div>
      <div class="btns">
        <button class="btn bs" id="clrS">🧹 Limpar</button>
        <button class="btn bp" id="valS">✔ Validar</button>
      </div>
      <div id="infoS" class="sig-info">
        <strong>Supervisor:</strong> {supervisor} &nbsp;|&nbsp;
        <strong>Data/Hora:</strong> <span id="dtS">--</span>
      </div>
    </div>

    <button class="btn-pdf" id="btnPDF" disabled>📄 Salvar Ata e Gerar PDF</button>
    <div class="rodape">BERTA — Painel Operacional FTTH/GPON — Santa Catarina</div>
  </div>
</div>
<script>
let padT, padS, tecOk=false;
function resize(cv){{const r=cv.getBoundingClientRect();cv.width=r.width;cv.height=r.height;}}
window.onload=()=>{{
  const cvT=document.getElementById('cvT'), cvS=document.getElementById('cvS');
  resize(cvT); resize(cvS);
  padT=new SignaturePad(cvT); padS=new SignaturePad(cvS);
  padT.addEventListener('beginStroke',()=>document.getElementById('phT').style.display='none');
  padS.addEventListener('beginStroke',()=>document.getElementById('phS').style.display='none');
}};
document.getElementById('clrT').onclick=()=>{{padT.clear();document.getElementById('phT').style.display='';tecOk=false;document.getElementById('btnPDF').disabled=true;document.getElementById('infoT').classList.remove('on');}};
document.getElementById('clrS').onclick=()=>{{padS.clear();document.getElementById('phS').style.display='';document.getElementById('infoS').classList.remove('on');}};
document.getElementById('valT').onclick=()=>{{
  if(padT.isEmpty()){{alert('Assine antes de validar.');return;}}
  document.getElementById('dtT').textContent=new Date().toLocaleString('pt-BR');
  document.getElementById('infoT').classList.add('on');
  tecOk=true; document.getElementById('btnPDF').disabled=false;
}};
document.getElementById('valS').onclick=()=>{{
  if(padS.isEmpty()){{alert('Assine antes de validar.');return;}}
  document.getElementById('dtS').textContent=new Date().toLocaleString('pt-BR');
  document.getElementById('infoS').classList.add('on');
}};
document.getElementById('btnPDF').onclick=async()=>{{
  if(!tecOk){{alert('Assinatura do tecnico e obrigatoria.');return;}}
  const {{jsPDF}}=window.jspdf;
  const doc=new jsPDF({{unit:'mm',format:'a4'}});
  const W=doc.internal.pageSize.getWidth();
  doc.setFillColor(26,58,143); doc.rect(0,0,W,38,'F');
  doc.setTextColor(255,255,255); doc.setFontSize(13); doc.setFont(undefined,'bold');
  doc.text('{titulo}',W/2,16,{{align:'center'}});
  doc.setFontSize(9); doc.setFont(undefined,'normal');
  doc.text('Periodo: {mes_ref}  |  Gerado: {dt_now}',W/2,26,{{align:'center'}});
  let y=46; doc.setTextColor(51,51,51); doc.setFontSize(11);
  doc.setFont(undefined,'bold'); doc.text('DADOS DO TECNICO',14,y); y+=7;
  doc.setFont(undefined,'normal');
  ['Nome: {nome_safe}','Codigo: {cod_safe}','Supervisor: {sup_safe}'].forEach(t=>{{doc.text(t,14,y);y+=6;}});
  y+=4; doc.setFont(undefined,'bold'); doc.text('INDICADORES',14,y); y+=7;
  doc.setFont(undefined,'normal');
  ['Produtividade: {prod_val} — {prod_cls[0]}','Eficacia: {efic_val} — {efic_cls[0]}',
   'Repetida: {rep_val} — {rep_cls[0]}','Infancia: {inf_val} — {inf_cls[0]}',
   'Pontuacao Geral: {nota}/{nota_max}'].forEach(t=>{{doc.text(t,14,y);y+=6;}});
  y+=6;
  if(!padT.isEmpty()){{
    doc.setFont(undefined,'bold'); doc.text('ASSINATURA DO TECNICO',14,y); y+=6;
    doc.addImage(padT.toDataURL('image/png'),'PNG',14,y,80,28); y+=32;
    doc.setFont(undefined,'normal'); doc.setFontSize(9);
    doc.text('Validada em: '+new Date().toLocaleString('pt-BR'),14,y); y+=8;
  }}
  if(!padS.isEmpty()){{
    doc.setFontSize(11); doc.setFont(undefined,'bold'); doc.text('ASSINATURA DO SUPERVISOR',14,y); y+=6;
    doc.addImage(padS.toDataURL('image/png'),'PNG',14,y,80,28); y+=32;
  }}
  doc.setFontSize(8); doc.setTextColor(150,150,150);
  doc.text('BERTA — Sistema Operacional FTTH/GPON — SC',W/2,285,{{align:'center'}});
  doc.save('ata_qualidade_{cod_safe}_{ts_now}.pdf');
  alert('PDF gerado com sucesso!');
}};
window.addEventListener('resize',()=>{{
  setTimeout(()=>{{
    [padT,padS].forEach(p=>{{if(p&&p.canvas){{const r=p.canvas.getBoundingClientRect();const d=p.toData();p.canvas.width=r.width;p.canvas.height=r.height;if(d&&d.length)p.fromData(d);}}}});
  }},200);
}});
</script>
</body>
</html>"""

# =============================================================================
# 14. MAIN
# =============================================================================

def main():
    try:
        df = carregar_base()
        if df is None:
            st.error("Nao foi possivel carregar a base. Verifique o Supabase Storage.")
            return
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        return

    f = sidebar(df)
    tela = f["tela"]
    dm = _filtrar(df, f)
    ds = _escopo(df, f)

    if f["supervisor"]:
        ult_att = ultima_atualizacao_base()
        att_str = f" | 🕐 Base atualizada: {ult_att}" if ult_att else ""
        st.markdown(
            f'<div class="banner-sup">👑 Equipe de <strong>{f["supervisor"]}</strong>'
            f' — {len(f["tecs_sup"])} tecnico(s) | {f["mes"]}{att_str}</div>',
            unsafe_allow_html=True)
    else:
        ult_att = ultima_atualizacao_base()
        if ult_att:
            st.markdown(
                f'<div class="banner-sup" style="background:#f0f4f8">'
                f'🕐 Base atualizada: <strong>{ult_att}</strong></div>',
                unsafe_allow_html=True)

    if dm.empty and tela not in ("📅 Diario", "📆 Calendario"):
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    if tela == "📅 Diario":
        tela_diario(df, ds, f)
    elif tela == "📊 Producao Diaria":
        tela_producao(dm, ds, f)
    elif tela == "🔁 Repetidos":
        tela_repetidos(dm, ds, f)
    elif tela == "👶 Infancia":
        tela_infancia(dm, ds, f)
    elif tela == "📆 Calendario":
        tela_calendario(df, ds, f)
    elif tela == "🏆 Qualidade":
        tela_qualidade(dm, ds, f)


if __name__ == "__main__":
    main()
