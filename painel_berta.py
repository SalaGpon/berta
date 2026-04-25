#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERTA — Painel Operacional do Supervisor v3.5
Telas: Producao Diaria | Repetidos | Infancia | Calendario | Qualidade | Diario | Justificativas
Fonte de dados: Repositório (API)
"""

import os
import re
import base64
import io
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import streamlit as st

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
# 2. CSS GLOBAL
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body { margin: 0; padding: 0; }
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

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

[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #dde3ed !important;
}
[data-testid="stSidebar"] * { color: #1a2332 !important; }
[data-testid="stSidebar"] hr { border-color: #dde3ed !important; }

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
[data-baseweb="tab-panel"] { background-color: transparent !important; }
[data-baseweb="tab-border"] { background-color: #dde3ed !important; }

.stDataFrame,
[data-testid="stDataFrameResizable"],
[data-testid="stDataFrameContainer"] {
    background-color: #ffffff !important;
    border: 1px solid #dde3ed !important;
    border-radius: 8px !important;
}

.stButton > button {
    background-color: #1e3a5f !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}
.stButton > button:hover { background-color: #163050 !important; }

[data-baseweb="tag"] {
    background-color: #e8f0fa !important;
    color: #1e3a5f !important;
}

.stRadio label { color: #1a2332 !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f5f7fa; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

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

_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE_LOCAL = next(
    (p for p in [
        os.path.join(_DIR, "BASEBOT.csv"),
        os.path.join(_DIR, "bases", "BASEBOT.csv"),
    ] if os.path.exists(p)),
    None,
)

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
ROYAL = "#1e3a5f"
ROYAL_LIGHT = "#4a7db5"

_LYT = dict(
    paper_bgcolor=C["paper"],
    plot_bgcolor=C["bg"],
    font=dict(family="Inter, sans-serif", color=C["txt"], size=12),
    margin=dict(l=40, r=20, t=44, b=36),
    xaxis=dict(gridcolor=C["grid"], linecolor=C["grid"], zeroline=False, tickfont_color=C["txt"]),
    yaxis=dict(gridcolor=C["grid"], linecolor=C["grid"], zeroline=False, tickfont_color=C["txt"]),
    legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor=C["grid"], borderwidth=1, font_color=C["txt"]),
)

URL_JUSTIFICATIVA = "https://script.google.com/macros/s/AKfycbzBQjCcxSMrKBlUH3H6PY4I1AvF_XKTvJcHKXsHFT6HI7J-MONPeLXTEvZZOo5da4-y/exec"
URL_ATAS_DRIVE    = "https://script.google.com/macros/s/AKfycbyEw2E759E79Tpy3wbgZt8tip6F82aYtQiZ33-CoIpcExiUX5dUXynoBqYzJaa-fPk7DA/exec"

# =============================================================================
# 4. CARREGAMENTO DO DATAFRAME
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def carregar_base_repositorio():
    try:
        token = st.secrets.get("GITHUB_TOKEN", "")
        if not token:
            st.warning("🔑 Token de acesso não configurado. Contate o administrador.")
            return None

        headers = {"Authorization": f"token {token}"}
        meta_url = "https://api.github.com/repos/SalaGpon/Berta-bot/contents/BASEBOT.csv"
        meta = requests.get(meta_url, headers=headers, timeout=30)
        if meta.status_code != 200:
            st.warning(f"Erro ao acessar repositório: HTTP {meta.status_code}")
            return None

        sha = meta.json().get("sha")
        blob_url = f"https://api.github.com/repos/SalaGpon/Berta-bot/git/blobs/{sha}"
        blob_resp = requests.get(blob_url, headers=headers, timeout=60)
        if blob_resp.status_code != 200:
            st.warning(f"Erro ao baixar arquivo: HTTP {blob_resp.status_code}")
            return None

        b64_content = blob_resp.json().get("content")
        if not b64_content:
            st.warning("Arquivo vazio no repositório.")
            return None

        texto = base64.b64decode(b64_content).decode("utf-8-sig", errors="replace")

        for sep in ["\t", ";", ","]:
            try:
                df = pd.read_csv(
                    io.StringIO(texto),
                    sep=sep,
                    dtype=str,
                    engine="python",
                    on_bad_lines="warn",
                    encoding="utf-8-sig"
                )
                if df.shape[1] > 5:
                    st.success(f"✅ Base carregada do Repositório (API) – separador detectado: '{sep}'")
                    return df
            except Exception:
                continue

        try:
            df = pd.read_csv(
                io.StringIO(texto),
                sep=None,
                dtype=str,
                engine="python",
                on_bad_lines="warn"
            )
            if df.shape[1] > 5:
                st.success("✅ Base carregada do Repositório (API) – separador automático")
                return df
        except Exception as e:
            st.warning(f"Não foi possível ler o arquivo do repositório: {e}")

        return None

    except Exception as e:
        st.warning(f"Erro ao carregar do repositório: {e}")
        return None


@st.cache_data(ttl=300)
def carregar_base_local():
    if not CAMINHO_BASE_LOCAL:
        return None
    try:
        for sep in ["\t", ";", ","]:
            try:
                df = pd.read_csv(CAMINHO_BASE_LOCAL, sep=sep, dtype=str, engine="python", on_bad_lines="warn")
                if df.shape[1] > 5:
                    st.success(f"✅ Base carregada do arquivo local – separador '{sep}'")
                    return df
            except Exception:
                continue
        df = pd.read_csv(CAMINHO_BASE_LOCAL, sep=None, dtype=str, engine="python", on_bad_lines="warn")
        if df.shape[1] > 5:
            st.success("✅ Base carregada do arquivo local – separador automático")
            return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo local: {e}")
    return None


def carregar_base():
    df = carregar_base_repositorio()
    if df is None:
        df = carregar_base_local()
    if df is not None:
        return _processar_df(df)
    return None


def _processar_df(df):
    df.columns = df.columns.str.strip()

    col_fim = "DH_FIM_EXEC_REAL"
    col_ab  = "AB_BA"
    col_estado = "ESTADO"
    col_macro  = "MACRO"
    col_tecnico = "TECNICO_EXECUTOR"
    col_territorio = "TERRITORIO"
    col_sa = "SA"
    col_gpon = "GPON"
    col_descricao = "DESCRICAO"
    col_obs = "OBSERVACAO"
    col_cod_fechamento = "COD_FECHAMENTO"
    col_flag_sucesso = "FLAG_FECHADO_SUCESSO"
    col_flag_sem_sucesso = "FLAG_FECHADO_SEM_SUCESSO"

    for c in [col_fim, col_ab, col_estado, col_macro, col_tecnico, col_territorio, col_sa, col_gpon]:
        if c not in df.columns:
            raise KeyError(f"Coluna '{c}' não encontrada. Colunas disponíveis: {list(df.columns)}")

    df["FIM_DT"] = pd.to_datetime(df[col_fim], dayfirst=True, errors="coerce")
    df["AB_DT"]  = pd.to_datetime(df[col_ab],  dayfirst=True, errors="coerce")

    df["Estado"]  = df[col_estado].str.strip().str.upper()
    df["Macro Atividade"] = df[col_macro].str.strip().str.upper()

    df["NOME_TEC"] = df[col_tecnico].apply(
        lambda v: str(v).split(" - ")[0].strip().title() if pd.notna(v) and " - " in str(v) else str(v).strip().title()
    )

    def _extrair_cod(nome):
        if pd.isna(nome) or not nome:
            return ""
        m = re.search(r"(TR|TT|TC)\d+", str(nome), re.I)
        return m.group(0).upper() if m else ""
    df["CODIGO_TECNICO_EXTRAIDO"] = df[col_tecnico].apply(_extrair_cod)

    df["DIA_FIM"] = df["FIM_DT"].dt.date
    df["MES_FIM"] = df["FIM_DT"].dt.to_period("M")
    df["SEM_FIM"] = df["FIM_DT"].dt.isocalendar().week.astype("Int64")
    df["ANO_FIM"] = df["FIM_DT"].dt.year.astype("Int64")
    df["DIA_AB"]  = df["AB_DT"].dt.date
    df["MES_AB"]  = df["AB_DT"].dt.to_period("M")
    df["SEM_AB"]  = df["AB_DT"].dt.isocalendar().week.astype("Int64")

    df["FLAG_CONCLUIDO_SUCESSO"] = df.get(col_flag_sucesso, "NAO")
    df["FLAG_CONCLUIDO_SEM_SUCESSO"] = df.get(col_flag_sem_sucesso, "NAO")

    df["FLAG_REPARO_VALIDO"] = (
        (df["Macro Atividade"] == "REP-FTTH") &
        (df["FLAG_CONCLUIDO_SUCESSO"] == "SIM")
    ).map({True: "SIM", False: "NAO"})
    df["FLAG_INSTALACAO_VALIDA"] = (
        (df["Macro Atividade"] == "INST-FTTH") &
        (df["FLAG_CONCLUIDO_SUCESSO"] == "SIM")
    ).map({True: "SIM", False: "NAO"})

    for _f in ("FLAG_REPETIDO_ABERTO", "FLAG_P0_10_DIA", "FLAG_P0_15_DIA",
               "FLAG_REPETIDO", "FLAG_INFANCIA", "FLAG_INF",
               "TEC_ANTERIOR", "IF_DIAS"):
        if _f not in df.columns:
            df[_f] = "NAO"
        else:
            df[_f] = df[_f].fillna("NAO")

    df["FLAG_REPETIDO_30D"] = df["FLAG_REPETIDO"]
    df["FLAG_INFANCIA_30D"]  = df["FLAG_INFANCIA"]

    if "ALARMADO" not in df.columns:
        df["ALARMADO"] = "NAO"
    else:
        df["ALARMADO"] = df["ALARMADO"].fillna("NAO")

    if "CDOE" not in df.columns:
        df["CDOE"] = ""
    else:
        df["CDOE"] = df["CDOE"].fillna("")

    if "LOGRADOURO" in df.columns:
        df["Logradouro"] = df["LOGRADOURO"].fillna("")
    if "NUMERO" in df.columns:
        df["Número"] = df["NUMERO"].fillna("")
    if "BAIRRO" in df.columns:
        df["Bairro"] = df["BAIRRO"].fillna("")

    df["Território de serviço: Nome"] = df[col_territorio]
    df["Número SA"] = df[col_sa]
    df["FSLOI_GPONAccess"] = df[col_gpon]
    df["Técnico Atribuído"] = df[col_tecnico]

    if "Descrição" not in df.columns:
        df["Descrição"] = df.get(col_descricao, "")
    if "Observação" not in df.columns:
        df["Observação"] = df.get(col_obs, "")
    if "Código de encerramento" not in df.columns:
        df["Código de encerramento"] = df.get(col_cod_fechamento, "")

    return df


def extrair_codigo_tecnico(tecnico_str) -> str:
    try:
        m = re.search(r'(TR\d+|TT\d+|TC\d+)', str(tecnico_str).strip())
        return m.group(1).upper() if m else ""
    except:
        return ""


@st.cache_data(ttl=600)
def carregar_equipes(df=None):
    if df is None:
        df = carregar_base()
    equipes = {}
    if df is not None:
        for _, row in df.iterrows():
            sup = str(row.get("SUPERVISOR", "")).strip()
            if not sup or sup.upper() in ("", "NAN", "NONE"):
                continue
            sup = sup.title()
            cod = str(row.get("TR", "")).strip().upper()
            if not cod:
                cod = extrair_codigo_tecnico(row.get("TECNICO_EXECUTOR", ""))
            if not cod:
                continue
            equipes.setdefault(sup, [])
            if cod not in equipes[sup]:
                equipes[sup].append(cod)

    if not equipes:
        st.info("Equipes não encontradas no BASEBOT.csv, tentando planilha de presença...")
        try:
            import openpyxl
            url_presenca = "https://raw.githubusercontent.com/SalaGpon/Berta-bot/main/Presen%C3%A7a.xlsx"
            r = requests.get(url_presenca, timeout=30)
            if r.status_code == 200:
                wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(min_row=2, values_only=True))
                if rows:
                    headers = [cell.value for cell in ws[1]]
                    tr_col = next((i for i, h in enumerate(headers) if h and "TR" in str(h).upper()), None)
                    sup_col = next((i for i, h in enumerate(headers) if h and "SUPERVISOR" in str(h).upper()), None)
                    if tr_col is not None and sup_col is not None:
                        for row in rows:
                            tr = str(row[tr_col]).strip().upper() if row[tr_col] else None
                            sup = str(row[sup_col]).strip().title() if row[sup_col] else None
                            if tr and sup:
                                equipes.setdefault(sup, [])
                                if tr not in equipes[sup]:
                                    equipes[sup].append(tr)
                wb.close()
                if equipes:
                    st.success("✅ Equipes carregadas da planilha de presença")
        except Exception as e:
            st.warning(f"Não foi possível carregar a planilha de presença: {e}")

    return equipes


# =============================================================================
# 4B. CARREGAR MAPEAMENTO DE CAUSAS MACRO
# =============================================================================

@st.cache_data(ttl=3600)
def carregar_causas_macro():
    try:
        url = "https://raw.githubusercontent.com/SalaGpon/Berta-bot/main/Causas.xlsx"
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            raise FileNotFoundError("Arquivo de causas não encontrado.")
        df = pd.read_excel(io.BytesIO(r.content), sheet_name="Causas", dtype=str)
        df.columns = df.columns.str.strip()
        mapa = {}
        for _, row in df.iterrows():
            cod = str(row.get("cod_fechamento", "")).strip()
            causa = str(row.get("Causa Macro", "")).strip()
            if cod and causa:
                mapa[cod] = causa
        return mapa
    except Exception as e:
        st.warning("Não foi possível carregar a planilha de causas macro. Usando descrições originais.")
        return {}


# =============================================================================
# 5. HELPERS
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
                    line=dict(color=ROYAL_LIGHT, width=2), marker_size=6, secondary_y=True)
    if meta is not None:
        fig.add_hline(y=meta, line_dash="dash", line_color=C["yellow"],
                      annotation_text=f"Meta {meta}%", secondary_y=True)
    fig.update_layout(**_lyt(titulo, h))
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return fig


# =============================================================================
# 6. SIDEBAR
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
            ["📅 Diario", "📊 Producao Diaria", "🔁 Repetidos", "👶 Infancia",
             "📆 Calendario", "🏆 Qualidade", "📝 Justificativas"],
            label_visibility="collapsed", key="nav")
        st.divider()

        st.markdown("**Filtros**")
        df_atual = df

        meses = sorted(df_atual["MES_FIM"].dropna().astype(str).unique(), reverse=True)
        mes_padrao = datetime.now().strftime("%Y-%m")
        mes_idx = meses.index(mes_padrao) if mes_padrao in meses else 0
        mes = st.selectbox("📅 Mes", meses, index=mes_idx, key="f_mes")

        eq = carregar_equipes(df_atual)
        sups = sorted(eq.keys())
        if sups:
            sup = st.selectbox("👑 Supervisor", ["— Todos —"] + sups, key="f_sup")
            tecs_sup = eq.get(sup, []) if sup != "— Todos —" else []
            if tecs_sup:
                st.caption(f"Equipe: {len(tecs_sup)} tecnico(s)")
        else:
            sup, tecs_sup = "— Todos —", []

        terrs = sorted(df_atual["Território de serviço: Nome"].dropna().unique())
        terr  = st.multiselect("📍 Territorio", terrs, key="f_terr")

        pool = ([t for t in tecs_sup if t in df_atual["CODIGO_TECNICO_EXTRAIDO"].values]
                if tecs_sup else sorted(df_atual["CODIGO_TECNICO_EXTRAIDO"].dropna().unique()))
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
# 7. TELAS (Producao, Repetidos, Infancia, Calendario, Diario)
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
    fig.add_bar(x=prod["Dia"], y=prod["Inst"], name="INST", marker_color=ROYAL)
    fig.add_bar(x=prod["Dia"], y=prod["Rep"],  name="REP",  marker_color=ROYAL_LIGHT)
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
            _bar_h(t5["NOME_TEC"], t5["Prod"], ROYAL,
                   labels=t5["CODIGO_TECNICO_EXTRAIDO"], h=260),
            use_container_width=True)
    with c2:
        st.markdown("**Top 5 — Menor Producao**")
        b5 = pt.tail(5).sort_values("Prod")
        st.plotly_chart(
            _bar_h(b5["NOME_TEC"], b5["Prod"], ROYAL_LIGHT,
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
                                    line=dict(color=ROYAL,width=2),marker_size=7, marker_color=ROYAL))
        fig2.update_layout(**_lyt("Producao Semanal - ultimas 12 semanas",300))
        st.plotly_chart(fig2, use_container_width=True)
    with tab2:
        ev2 = suc_sc.groupby("MES_FIM").size().reset_index(name="T")
        ev2["MES_FIM"] = ev2["MES_FIM"].astype(str)
        ev2 = ev2.sort_values("MES_FIM").tail(12)
        fig3 = go.Figure(go.Bar(x=ev2["MES_FIM"],y=ev2["T"],marker_color=ROYAL))
        fig3.update_layout(**_lyt("Producao Mensal",300))
        st.plotly_chart(fig3, use_container_width=True)


def tela_repetidos(dm, ds, f):
    _header("🔁", "Repetidos", f)

    tem_vip = ("TEC_ANTERIOR" in dm.columns) and ("FLAG_REPETIDO" in dm.columns)

    den_df = dm[
        (dm["Macro Atividade"] == "REP-FTTH") &
        (dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM")
    ]

    if tem_vip:
        num_df = dm[
            (dm["FLAG_REPETIDO"] == "SIM") &
            (dm["TEC_ANTERIOR"].notna()) &
            (dm["TEC_ANTERIOR"].str.strip() != "")
        ]
        fonte_label = "🏛️ Fonte: VIP Oficial (TEC_ANTERIOR + FLAG_REPETIDO)"
    else:
        gpons_rep, _, _ = _calcular_repetidos_gpon(ds, f["mes"])
        num_df = pd.DataFrame()
        fonte_label = "⚙️ Fonte: Cálculo Interno (GPON)"

    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    if tem_vip:
        den_tec = den_df.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
            Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0]) if len(x) else ""),
            Total=("Número SA", "count")).reset_index()
        num_tec = num_df.groupby("TEC_ANTERIOR").size().reset_index(name="Repetidos")
        num_tec.rename(columns={"TEC_ANTERIOR": "CODIGO_TECNICO_EXTRAIDO"}, inplace=True)
        tb = den_tec.merge(num_tec, on="CODIGO_TECNICO_EXTRAIDO", how="left")
        tb["Repetidos"] = tb["Repetidos"].fillna(0).astype(int)
        tb["Taxa%"] = (tb["Repetidos"] / tb["Total"].replace(0, 1) * 100).round(2)
        tb = tb.sort_values("Taxa%", ascending=False).reset_index(drop=True)
        tb = tb.rename(columns={"CODIGO_TECNICO_EXTRAIDO": "TR"})
    else:
        den_tec = den_df.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
            Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0]) if len(x) else ""),
            Total=("Número SA", "count")).reset_index()
        rep_por_tec = {}
        for gpon, info in gpons_rep.items():
            tr = info.get("pai_tr", "")
            if tr:
                rep_por_tec[tr] = rep_por_tec.get(tr, 0) + 1
        num_tec_df = pd.DataFrame(rep_por_tec.items(), columns=["CODIGO_TECNICO_EXTRAIDO", "Repetidos"]) if rep_por_tec else pd.DataFrame(columns=["CODIGO_TECNICO_EXTRAIDO", "Repetidos"])
        tb = den_tec.merge(num_tec_df, on="CODIGO_TECNICO_EXTRAIDO", how="left")
        tb["Repetidos"] = tb["Repetidos"].fillna(0).astype(int)
        tb["Taxa%"] = (tb["Repetidos"] / tb["Total"].replace(0,1) * 100).round(2)
        tb = tb.sort_values("Taxa%", ascending=False).reset_index(drop=True)
        tb = tb.rename(columns={"CODIGO_TECNICO_EXTRAIDO": "TR"})

    total_rep_tabela = int(tb["Total"].sum())
    repetidos_tabela = int(tb["Repetidos"].sum())
    taxa_tabela = round(repetidos_tabela / total_rep_tabela * 100, 2) if total_rep_tabela > 0 else 0

    rep_ab = ds[ds["FLAG_REPETIDO_ABERTO"] == "SIM"] if "FLAG_REPETIDO_ABERTO" in ds.columns else pd.DataFrame()
    if tem_vip:
        rep_alrm = dm[(dm["FLAG_REPETIDO"] == "SIM") & (dm["ALARMADO"] == "SIM")]
        rep_alrm_count = len(rep_alrm)
    else:
        rep_alrm_count = 0

    cols = st.columns(5)
    for col, (lb,vl,sb,cl) in zip(cols,[
        ("Total Reparos", f"{total_rep_tabela:,}",   "abertos no mes",  "kpi-blue"),
        ("Repetidos",     f"{repetidos_tabela:,}",   "reparos filhos",  "kpi-red" if taxa_tabela>9 else "kpi-yellow"),
        ("Taxa %",        f"{taxa_tabela}%",          "meta: <= 9%",     "kpi-red" if taxa_tabela>9 else "kpi-green"),
        ("Em Garantia",   f"{len(rep_ab):,}",         "abertos 30d",     "kpi-yellow"),
        ("Alarmados",     f"{rep_alrm_count}",        "GPON alarmado",   "kpi-red" if rep_alrm_count>0 else "kpi-green"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:#64748b;margin:6px 0 14px 2px;">{fonte_label}</div>',
        unsafe_allow_html=True)

    _sec("Indicador por Tecnico")
    tb["Status"] = tb["Taxa%"].apply(lambda t: "🔴" if t>12 else "🟡" if t>9 else "🟢" if t>0 else "⚪")
    st.dataframe(tb[["Status","Nome","TR","Repetidos","Total","Taxa%"]], use_container_width=True, hide_index=True,
                 column_config={"Taxa%": st.column_config.ProgressColumn(
                     "Taxa%", format="%.1f%%", min_value=0,
                     max_value=max(float(tb["Taxa%"].max()) if not tb.empty else 1, 1))})

    if tem_vip and not num_df.empty:
        _sec("Histórico Resumo dos GPONs Repetidos")
        for gpon, grupo_filho in num_df.groupby("FSLOI_GPONAccess"):
            hist = ds[ds["FSLOI_GPONAccess"] == gpon].sort_values("FIM_DT")
            if hist.empty:
                continue

            filho = grupo_filho.iloc[0]
            filho_tr = filho.get("CODIGO_TECNICO_EXTRAIDO", "")
            pai_tr = filho.get("TEC_ANTERIOR", "")

            linhas = []
            for _, row in hist.iterrows():
                sa = row.get("Número SA", "")
                data = row.get("FIM_DT", "")
                if pd.isna(data):
                    data_str = "S/D"
                else:
                    data_str = pd.to_datetime(data).strftime("%d/%m/%Y") if not isinstance(data, str) else data
                tecnico = row.get("NOME_TEC", "")
                tr = row.get("CODIGO_TECNICO_EXTRAIDO", "")
                desc = row.get("Descrição", "")

                if tr == filho_tr and row.get("FLAG_REPETIDO", "NAO") == "SIM":
                    icone = "🔸 REPETIDO"
                elif tr == pai_tr and pd.notna(data) and pd.notna(filho.get("FIM_DT")):
                    if pd.to_datetime(data) < pd.to_datetime(filho["FIM_DT"]):
                        icone = "🔹 PAI (contabiliza)"
                    else:
                        icone = "📌"
                else:
                    datas = hist["FIM_DT"].dropna().sort_values()
                    if len(datas) >= 2 and pd.notna(data):
                        if pd.to_datetime(data) == datas.iloc[-2]:
                            icone = "🔹 PAI (contabiliza)"
                        else:
                            icone = "📌"
                    else:
                        icone = "📌"

                linha = f"   {icone}: SA {sa} - {data_str} - {tecnico} - {tr}"
                if desc and str(desc).strip():
                    linha += f"\n      📝 {str(desc).strip()}"
                linhas.append(linha)

            endereco = ""
            if "Logradouro" in filho.index:
                endereco = f"{filho.get('Logradouro','')}, {filho.get('Número','')} - {filho.get('Bairro','')}"
            if endereco:
                linhas.append(f"   🏠 {endereco}")

            with st.expander(f"📜 GPON {gpon} ({len(hist)} reparos)"):
                st.markdown("\n".join(linhas), unsafe_allow_html=True)

        st.divider()
        _sec("Repetidos por Dia do Mês")
        if "DIA_FIM" in num_df.columns:
            diario = num_df.groupby("DIA_FIM").size().reset_index(name="Repetidos")
            diario["Dia"] = pd.to_datetime(diario["DIA_FIM"]).dt.strftime("%d/%m")
            fig_dia = make_subplots(specs=[[{"secondary_y": False}]])
            fig_dia.add_bar(x=diario["Dia"], y=diario["Repetidos"], name="Repetidos", marker_color=ROYAL)
            fig_dia.add_scatter(x=diario["Dia"], y=diario["Repetidos"], mode="lines+markers",
                                line=dict(color=ROYAL_LIGHT, width=2), marker=dict(size=6, color=ROYAL_LIGHT),
                                name="Tendência")
            fig_dia.update_layout(**_lyt("", 300))
            fig_dia.update_yaxes(title_text="Quantidade")
            st.plotly_chart(fig_dia, use_container_width=True)
        else:
            st.info("Dados insuficientes para gráfico diário.")

        _sec("Pareto de Causas dos Repetidos")
        mapa_causas = carregar_causas_macro()
        if mapa_causas:
            num_df["CAUSA_MACRO"] = num_df["Código de encerramento"].astype(str).str.strip().map(mapa_causas)
            num_df["CAUSA_MACRO"] = num_df["CAUSA_MACRO"].fillna("OUTROS")
        else:
            num_df["CAUSA_MACRO"] = num_df["Descrição"].str[:50]

        causas = num_df.groupby("CAUSA_MACRO").size().reset_index(name="Qtd")
        causas = causas.sort_values("Qtd", ascending=False).head(15)
        causas["Perc"] = (causas["Qtd"] / causas["Qtd"].sum() * 100).round(1)
        causas["Acum"] = causas["Perc"].cumsum()
        fig_causas = make_subplots(specs=[[{"secondary_y": True}]])
        fig_causas.add_bar(x=causas["CAUSA_MACRO"], y=causas["Qtd"],
                           name="Ocorrências", marker_color=ROYAL)
        fig_causas.add_scatter(x=causas["CAUSA_MACRO"], y=causas["Acum"],
                               name="% Acumulado", mode="lines+markers",
                               line=dict(color=ROYAL_LIGHT, width=2), secondary_y=True)
        fig_causas.update_layout(**_lyt("Pareto de Causas", 350))
        fig_causas.update_yaxes(showgrid=False, secondary_y=True)
        st.plotly_chart(fig_causas, use_container_width=True)

        _sec("Pareto de Técnicos — Repetidos")
        pareto_tec = tb[["Nome","TR","Repetidos"]].sort_values("Repetidos", ascending=False)
        pareto_tec["Perc"] = (pareto_tec["Repetidos"] / pareto_tec["Repetidos"].sum() * 100).round(1)
        pareto_tec["Acum"] = pareto_tec["Perc"].cumsum()
        fig_tec = make_subplots(specs=[[{"secondary_y": True}]])
        fig_tec.add_bar(x=pareto_tec["Nome"], y=pareto_tec["Repetidos"],
                        name="Repetidos", marker_color=ROYAL)
        fig_tec.add_scatter(x=pareto_tec["Nome"], y=pareto_tec["Acum"],
                            name="% Acumulado", mode="lines+markers",
                            line=dict(color=ROYAL_LIGHT, width=2), secondary_y=True)
        fig_tec.update_layout(**_lyt("Pareto de Técnicos", 400))
        fig_tec.update_yaxes(showgrid=False, secondary_y=True)
        st.plotly_chart(fig_tec, use_container_width=True)


def _calcular_repetidos_gpon(ds, mes_str):
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        return {}, 0, pd.DataFrame()

    primeiro_dia = pd.Timestamp(ano, mes, 1)
    if mes == 12:
        ultimo_dia = pd.Timestamp(ano+1, 1, 1) - pd.Timedelta(days=1)
    else:
        ultimo_dia = pd.Timestamp(ano, mes+1, 1) - pd.Timedelta(days=1)

    df = ds.copy()
    if "FIM_DT" not in df.columns:
        df["FIM_DT"] = pd.to_datetime(df["DH_FIM_EXEC_REAL"], dayfirst=True, errors="coerce")
    if "AB_DT" not in df.columns:
        df["AB_DT"] = pd.to_datetime(df["AB_BA"], dayfirst=True, errors="coerce")

    df["_GPON"] = df["FSLOI_GPONAccess"].astype(str).str.strip().str.upper()

    df_rep = df[
        (df["Macro Atividade"] == "REP-FTTH") &
        (df["FLAG_CONCLUIDO_SUCESSO"] == "SIM") &
        (df["FIM_DT"].notna()) &
        (df["_GPON"].notna()) &
        (~df["_GPON"].isin(["", "NAN"]))
    ].copy()

    gpons_repetidos = {}
    for gpon, grupo in df_rep.groupby("_GPON"):
        grupo = grupo.sort_values("FIM_DT").reset_index(drop=True)
        if len(grupo) < 2:
            continue
        for i in range(len(grupo) - 1):
            pai  = grupo.iloc[i]
            filho = grupo.iloc[i+1]
            delta = (filho["FIM_DT"] - pai["FIM_DT"]).days
            ab_filho = filho.get("AB_DT")
            if pd.notna(ab_filho) and (ab_filho < primeiro_dia or ab_filho > ultimo_dia):
                continue
            if delta <= 30:
                if gpon not in gpons_repetidos:
                    gpons_repetidos[gpon] = {
                        "pai_tr"   : pai.get("CODIGO_TECNICO_EXTRAIDO", ""),
                        "pai_nome" : pai.get("NOME_TEC", ""),
                        "pai_sa"   : pai.get("Número SA", ""),
                        "pai_fim"  : pai["FIM_DT"],
                        "filho_tr" : filho.get("CODIGO_TECNICO_EXTRAIDO", ""),
                        "filho_sa" : filho.get("Número SA", ""),
                        "delta"    : delta,
                    }
                break

    den_df = df[
        (df["Macro Atividade"] == "REP-FTTH") &
        (df["FLAG_CONCLUIDO_SUCESSO"] == "SIM") &
        (df["AB_DT"].notna()) &
        (df["AB_DT"] >= primeiro_dia) &
        (df["AB_DT"] <= ultimo_dia)
    ]
    return gpons_repetidos, len(den_df), den_df


def tela_infancia(dm, ds, f):
    _header("👶", "Infancia", f)

    inst = dm[
        (dm["Macro Atividade"] == "INST-FTTH") &
        (dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM")
    ]

    tem_vip_inf = "FLAG_INFANCIA" in inst.columns

    if tem_vip_inf:
        inf = inst[inst["FLAG_INFANCIA"] == "SIM"]
        fonte_label = "🏛️ Fonte: VIP Oficial"
    else:
        rep = ds[(ds["Macro Atividade"]=="REP-FTTH") & (ds["FLAG_CONCLUIDO_SUCESSO"]=="SIM")]
        inf_list = []
        for _, irow in inst.iterrows():
            gpon = irow["FSLOI_GPONAccess"]
            if pd.isna(gpon): continue
            fim_inst = irow["FIM_DT"]
            if pd.isna(fim_inst): continue
            limite = fim_inst + pd.Timedelta(days=30)
            filhos = rep[(rep["FSLOI_GPONAccess"]==gpon) & (rep["FIM_DT"]>fim_inst) & (rep["FIM_DT"]<=limite)]
            if not filhos.empty:
                inf_list.append(irow)
        inf = pd.DataFrame(inf_list) if inf_list else pd.DataFrame()
        fonte_label = "⚙️ Fonte: Cálculo Interno"

    taxa = round(len(inf)/len(inst)*100,2) if len(inst)>0 else 0
    estados_ab = ["ATRIBUÍDO","NÃO ATRIBUÍDO","RECEBIDO","EM EXECUÇÃO","EM DESLOCAMENTO"]
    gpons = set(inf["FSLOI_GPONAccess"].dropna().str.upper())
    rep_ab = ds[(ds["Macro Atividade"]=="REP-FTTH") &
                (ds["Estado"].isin(estados_ab)) &
                (ds["FSLOI_GPONAccess"].str.upper().isin(gpons))] if gpons else pd.DataFrame()
    inf_alrm = inf[inf["ALARMADO"]=="SIM"] if "ALARMADO" in inf.columns else pd.DataFrame()

    cols = st.columns(5)
    for col,(lb,vl,sb,cl) in zip(cols,[
        ("Total Inst.",  f"{len(inst):,}", "INST concluidas",  "kpi-blue"),
        ("Infancia",     f"{len(inf):,}",  "reparo em 30d",    "kpi-red" if taxa>5 else "kpi-yellow"),
        ("Taxa %",       f"{taxa}%",       "meta: <= 5%",      "kpi-red" if taxa>5 else "kpi-green"),
        ("Inf. Aberta",  f"{len(rep_ab):,}","reparo aberto",   "kpi-yellow"),
        ("Alarmados",    f"{len(inf_alrm):,}","GPON alarmado", "kpi-red" if len(inf_alrm)>0 else "kpi-green"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:#64748b;margin:6px 0 14px 2px;">{fonte_label}</div>',
        unsafe_allow_html=True)

    _sec("Indicador por Tecnico")
    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    di = inst.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
        Total=("Número SA","count"),
        Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0]) if len(x) else "")
    ).reset_index()
    if tem_vip_inf:
        ni = inf.groupby("CODIGO_TECNICO_EXTRAIDO").size().reset_index(name="Infancia")
    else:
        ni = inf.groupby("CODIGO_TECNICO_EXTRAIDO").size().reset_index(name="Infancia") if not inf.empty else pd.DataFrame(columns=["CODIGO_TECNICO_EXTRAIDO","Infancia"])

    tb = di.merge(ni, on="CODIGO_TECNICO_EXTRAIDO", how="left")
    tb["Infancia"] = tb["Infancia"].fillna(0).astype(int)
    tb["Taxa%"] = (tb["Infancia"] / tb["Total"].replace(0,1) * 100).round(2)
    tb = tb.sort_values("Taxa%", ascending=False).reset_index(drop=True)
    tb = tb.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"})
    tb["Status"] = tb["Taxa%"].apply(lambda t: "🔴" if t>8 else "🟡" if t>5 else "🟢" if t>0 else "⚪")
    st.dataframe(tb[["Status","Nome","TR","Infancia","Total","Taxa%"]], use_container_width=True, hide_index=True,
                 column_config={"Taxa%": st.column_config.ProgressColumn(
                     "Taxa%", format="%.1f%%", min_value=0, max_value=max(float(tb["Taxa%"].max()) if not tb.empty else 1, 1))})

    if tem_vip_inf and not inf.empty:
        _sec("Detalhamento — Infância (VIP)")
        cols_det = [c for c in ["Número SA","FSLOI_GPONAccess","CODIGO_TECNICO_EXTRAIDO","NOME_TEC",
                                "inf_dias_anterior","inf_tecnico_filho","inf_dat_fech_anterior","Cidade"] if c in inf.columns]
        det = inf[cols_det].drop_duplicates(subset=["FSLOI_GPONAccess"])
        det.rename(columns={
            "FSLOI_GPONAccess":"GPON","Número SA":"SA Inst.",
            "CODIGO_TECNICO_EXTRAIDO":"TR (Instalador)",
            "inf_dias_anterior":"Dias p/ reparo",
            "inf_tecnico_filho":"Tec. que Reparou"}, inplace=True)
        st.dataframe(det, use_container_width=True, hide_index=True)

        st.divider()

        _sec("Infância por Dia do Mês")
        if "DIA_FIM" in inf.columns:
            diario = inf.groupby("DIA_FIM").size().reset_index(name="Infancia")
            diario["Dia"] = pd.to_datetime(diario["DIA_FIM"]).dt.strftime("%d/%m")
            fig_dia = make_subplots(specs=[[{"secondary_y": False}]])
            fig_dia.add_bar(x=diario["Dia"], y=diario["Infancia"], name="Infância", marker_color=ROYAL)
            fig_dia.add_scatter(x=diario["Dia"], y=diario["Infancia"], mode="lines+markers",
                                line=dict(color=ROYAL_LIGHT, width=2), marker=dict(size=6, color=ROYAL_LIGHT),
                                name="Tendência")
            fig_dia.update_layout(**_lyt("", 300))
            fig_dia.update_yaxes(title_text="Quantidade")
            st.plotly_chart(fig_dia, use_container_width=True)
        else:
            st.info("Dados insuficientes para gráfico diário.")

        _sec("Pareto de Causas da Infância")
        sas = inf["SA_REPARO_INFANCIA"].dropna().unique() if "SA_REPARO_INFANCIA" in inf.columns else []
        rows = ds[ds["Número SA"].isin(sas)] if len(sas) else pd.DataFrame()
        if not rows.empty:
            mapa_causas = carregar_causas_macro()
            if mapa_causas:
                rows["CAUSA_MACRO"] = rows["Código de encerramento"].astype(str).str.strip().map(mapa_causas)
                rows["CAUSA_MACRO"] = rows["CAUSA_MACRO"].fillna("OUTROS")
            else:
                rows["CAUSA_MACRO"] = rows["Descrição"].str[:50]
            causas = rows.groupby("CAUSA_MACRO").size().reset_index(name="Qtd")
            causas = causas.sort_values("Qtd", ascending=False).head(15)
            causas["Perc"] = (causas["Qtd"] / causas["Qtd"].sum() * 100).round(1)
            causas["Acum"] = causas["Perc"].cumsum()
            fig_causas = make_subplots(specs=[[{"secondary_y": True}]])
            fig_causas.add_bar(x=causas["CAUSA_MACRO"], y=causas["Qtd"],
                               name="Ocorrências", marker_color=ROYAL)
            fig_causas.add_scatter(x=causas["CAUSA_MACRO"], y=causas["Acum"],
                                   name="% Acumulado", mode="lines+markers",
                                   line=dict(color=ROYAL_LIGHT, width=2), secondary_y=True)
            fig_causas.update_layout(**_lyt("Pareto de Causas", 350))
            fig_causas.update_yaxes(showgrid=False, secondary_y=True)
            st.plotly_chart(fig_causas, use_container_width=True)
        else:
            st.info("Sem dados de causa dos reparos de infância.")

        _sec("Pareto de Técnicos — Infância")
        pareto_tec = tb[["Nome","TR","Infancia"]].sort_values("Infancia", ascending=False)
        pareto_tec["Perc"] = (pareto_tec["Infancia"] / pareto_tec["Infancia"].sum() * 100).round(1)
        pareto_tec["Acum"] = pareto_tec["Perc"].cumsum()
        fig_tec = make_subplots(specs=[[{"secondary_y": True}]])
        fig_tec.add_bar(x=pareto_tec["Nome"], y=pareto_tec["Infancia"],
                        name="Infância", marker_color=ROYAL)
        fig_tec.add_scatter(x=pareto_tec["Nome"], y=pareto_tec["Acum"],
                            name="% Acumulado", mode="lines+markers",
                            line=dict(color=ROYAL_LIGHT, width=2), secondary_y=True)
        fig_tec.update_layout(**_lyt("Pareto de Técnicos", 400))
        fig_tec.update_yaxes(showgrid=False, secondary_y=True)
        st.plotly_chart(fig_tec, use_container_width=True)


def tela_calendario(df, ds, f):
    import calendar as _cal
    _header("📆", "Calendario Mensal", f)

    mes_str = f["mes"]
    try:
        per = pd.Period(mes_str, freq="M")
        ano, mes = per.year, per.month
    except Exception:
        st.error("Mes invalido."); return

    hoje      = datetime.now()
    dias_mes  = _cal.monthrange(ano, mes)[1]
    dia_max   = hoje.day if (ano == hoje.year and mes == hoje.month) else dias_mes
    dias_range = list(range(1, dia_max + 1))
    meses_pt  = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    lbl_mes   = f"{meses_pt[mes-1]}/{ano}"

    df_m = ds[(ds["FIM_DT"].dt.year==ano) & (ds["FIM_DT"].dt.month==mes)].copy()
    df_m["DIA"] = df_m["FIM_DT"].dt.day.astype(int)
    suc_m    = df_m[df_m["FLAG_CONCLUIDO_SUCESSO"]    == "SIM"]
    semsuc_m = df_m[df_m["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM"]

    if suc_m.empty:
        st.warning("Sem dados de producao para o mes selecionado.")
        return

    tecs = suc_m["CODIGO_TECNICO_EXTRAIDO"].nunique()
    efic = round(len(suc_m)/(len(suc_m)+len(semsuc_m))*100,1) if (len(suc_m)+len(semsuc_m))>0 else 0
    cols = st.columns(5)
    for col,(lb,vl,sb,cl) in zip(cols,[
        ("Tecnicos Ativos", f"{tecs}",           lbl_mes,       "kpi-blue"),
        ("Concluidos",      f"{len(suc_m):,}",   "c/ sucesso",  "kpi-blue"),
        ("INST",            f"{(suc_m['Macro Atividade']=='INST-FTTH').sum():,}", "", "kpi-blue"),
        ("REP",             f"{(suc_m['Macro Atividade']=='REP-FTTH').sum():,}",  "", "kpi-purple"),
        ("Eficacia",        f"{efic}%",           "suc/total",   "kpi-green" if efic>=85 else "kpi-yellow"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)
    st.write("")

    st.markdown("""
    <div style="display:flex;gap:10px;margin-bottom:10px;font-size:11px;align-items:center;">
        <span style="background:#7c3aed;color:white;padding:2px 8px;border-radius:4px;">≥8</span>
        <span style="background:#000000;color:white;padding:2px 8px;border-radius:4px;">6-7</span>
        <span style="background:#1e40af;color:white;padding:2px 8px;border-radius:4px;">5</span>
        <span style="background:#d4edda;color:#155724;padding:2px 8px;border-radius:4px;">4</span>
        <span style="background:#fff3cd;color:#856404;padding:2px 8px;border-radius:4px;">3</span>
        <span style="background:#ffcccc;color:#721c24;padding:2px 8px;border-radius:4px;">1-2</span>
        <span style="background:#f0f0f0;color:#6c757d;padding:2px 8px;border-radius:4px;">0</span>
        <span style="color:#64748b;margin-left:4px;">= atividades no dia</span>
    </div>
    """, unsafe_allow_html=True)

    _sec(f"Producao por Tecnico — {lbl_mes}")

    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    suc_range = suc_m[suc_m["DIA"].isin(dias_range)]
    pivot = suc_range.groupby(["CODIGO_TECNICO_EXTRAIDO","DIA"]).size().unstack(fill_value=0)
    for d in dias_range:
        if d not in pivot.columns:
            pivot[d] = 0
    pivot = pivot[dias_range]

    nomes     = suc_m.groupby("CODIGO_TECNICO_EXTRAIDO")["Técnico Atribuído"].first().apply(_n)
    ss_tec    = semsuc_m.groupby("CODIGO_TECNICO_EXTRAIDO").size()
    dias_trab = suc_range.groupby("CODIGO_TECNICO_EXTRAIDO")["DIA"].nunique()

    pivot.insert(0, "Nome", nomes)
    pivot["Total"]     = pivot[dias_range].sum(axis=1)
    pivot["Sem Suc."]  = ss_tec.reindex(pivot.index).fillna(0).astype(int)
    pivot["Dias"]      = dias_trab.reindex(pivot.index).fillna(0).astype(int)
    pivot["Media"]     = (pivot["Total"] / pivot["Dias"].replace(0,1)).round(1)
    pivot["Eficacia%"] = (pivot["Total"]/(pivot["Total"]+pivot["Sem Suc."]).replace(0,1)*100).round(1)
    pivot = pivot.sort_values("Total", ascending=False).reset_index()
    pivot = pivot.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"})

    cols_dia  = [str(d) for d in dias_range]
    cols_order = ["Nome","TR"] + dias_range + ["Dias","Total","Sem Suc.","Media","Eficacia%"]
    pivot = pivot[cols_order]
    pivot.columns = ["Nome","TR"] + cols_dia + ["Dias","Total","Sem Suc.","Media","Eficacia%"]

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

    try:
        styled = pivot.style.map(_cor_cel, subset=cols_dia)
    except AttributeError:
        styled = pivot.style.applymap(_cor_cel, subset=cols_dia)

    max_p = int(pivot["Total"].max()) if not pivot.empty else 1
    altura_total = 38 + (len(pivot) * 35)

    st.dataframe(styled, use_container_width=True, hide_index=True,
        column_config={
            "Nome"     : st.column_config.TextColumn("Nome", width="medium"),
            "TR"       : st.column_config.TextColumn("TR", width="small"),
            "Total"    : st.column_config.ProgressColumn("Total", format="%d", min_value=0, max_value=max_p),
            "Eficacia%": st.column_config.ProgressColumn("Eficacia%", format="%.1f%%", min_value=0, max_value=100),
            "Media"    : st.column_config.NumberColumn("Media", format="%.1f"),
        }, height=altura_total)

    ef_list = []
    for d in dias_range:
        rows = df_m[df_m["DIA"] == d]
        s = (rows["FLAG_CONCLUIDO_SUCESSO"]=="SIM").sum()
        ss = (rows["FLAG_CONCLUIDO_SEM_SUCESSO"]=="SIM").sum()
        ef_list.append({"DIA": d, "Concluidos": s, "Eficacia%": round(s / max(s+ss, 1) * 100, 1)})
    ef_dia = pd.DataFrame(ef_list)

    fig = go.Figure()
    fig.add_bar(x=ef_dia["DIA"].astype(str), y=ef_dia["Concluidos"], name="Concluidos", marker_color=ROYAL, yaxis="y")
    fig.add_scatter(x=ef_dia["DIA"].astype(str), y=ef_dia["Eficacia%"], name="Eficacia%", mode="lines+markers",
                    line=dict(color=ROYAL_LIGHT,width=2), marker_size=6, yaxis="y2")
    fig.add_hline(y=85, line_dash="dash", line_color=C["yellow"], annotation_text="Meta 85%", yref="y2")
    fig.update_layout(
        **_lyt(f"Producao e Eficacia — {lbl_mes}", 320),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, tickfont_color=C["green"], range=[0,110]),
        showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


def tela_diario(df, ds, f):
    _header("📅", "Controle do Dia", f)

    datas_disp = sorted(ds["FIM_DT"].dropna().dt.date.unique(), reverse=True)
    if not datas_disp:
        st.warning("Nenhuma data disponivel.")
        return

    hoje = datetime.today().date()
    if hoje in datas_disp:
        valor_padrao = hoje
    else:
        valor_padrao = datas_disp[0]

    c_pick, c_info = st.columns([2, 5])
    with c_pick:
        dia_sel = st.date_input("Data de referencia",
            value=valor_padrao,
            min_value=datas_disp[-1],
            max_value=datas_disp[0],
            key="dia_ref")

    dm  = ds[ds["FIM_DT"].dt.date == dia_sel].copy()
    dm_ab = ds[ds["AB_DT"].dt.date == dia_sel].copy()

    suc     = dm[dm["FLAG_CONCLUIDO_SUCESSO"]    == "SIM"]
    sem_suc = dm[dm["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM"]
    inst_d  = suc[suc["Macro Atividade"] == "INST-FTTH"]
    rep_d   = suc[suc["Macro Atividade"] == "REP-FTTH"]
    tecs_atv = suc["CODIGO_TECNICO_EXTRAIDO"].nunique()
    efic    = round(len(suc)/(len(suc)+len(sem_suc))*100,1) if (len(suc)+len(sem_suc))>0 else 0

    with c_info:
        st.markdown(
            f"<div style='margin-top:28px;font-size:12px;color:#64748b;'>"
            f"<b>{dia_sel.strftime('%d/%m/%Y')}</b> — "
            f"{tecs_atv} tecnicos ativos | {len(suc)+len(sem_suc)} atividades concluidas</div>",
            unsafe_allow_html=True)

    rep_dia_ab = dm_ab[dm_ab["FLAG_REPETIDO_30D"]  == "SIM"]
    rep_ab_tot = ds[ds["FLAG_REPETIDO_ABERTO"]      == "SIM"]
    inf_dia    = suc[suc["FLAG_INFANCIA_30D"]        == "SIM"]
    p0_10 = ds[(ds["FIM_DT"].dt.date == dia_sel) & (ds["FLAG_P0_10_DIA"] == "SIM")]
    p0_15 = ds[(ds["FIM_DT"].dt.date == dia_sel) & (ds["FLAG_P0_15_DIA"] == "SIM")]

    cols = st.columns(7)
    for col, (lb,vl,sb,cl) in zip(cols, [
        ("Concluidos",    f"{len(suc):,}",  f"INST:{len(inst_d)} REP:{len(rep_d)}", "kpi-blue"),
        ("Eficacia",      f"{efic}%",        "suc/total",   "kpi-green" if efic>=85 else "kpi-yellow" if efic>=70 else "kpi-red"),
        ("Sem Sucesso",   f"{len(sem_suc):,}","pendencias",  "kpi-red" if len(sem_suc)>0 else "kpi-green"),
        ("Rep. Dia",      f"{len(rep_dia_ab):,}","abertos hoje","kpi-red" if len(rep_dia_ab)>0 else "kpi-green"),
        ("Rep. Abertos",  f"{len(rep_ab_tot):,}","em garantia","kpi-yellow" if len(rep_ab_tot)>0 else "kpi-green"),
        ("P0 10h",        f"{p0_10['CODIGO_TECNICO_EXTRAIDO'].nunique()}","tecnicos","kpi-red" if not p0_10.empty else "kpi-green"),
        ("P0 15h",        f"{p0_15['CODIGO_TECNICO_EXTRAIDO'].nunique()}","tecnicos","kpi-red" if not p0_15.empty else "kpi-green"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)
    st.write("")

    def _extrair_tr(nome):
        if pd.isna(nome) or not nome: return ""
        m = re.search(r"(TR|TT|TC)\d+", str(nome), re.I)
        return m.group(0).upper() if m else ""

    _sec("Produtividade por Tecnico")
    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""
    if suc.empty:
        st.info("Nenhuma atividade concluida neste dia.")
    else:
        pt = suc.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
            Nome  =("Técnico Atribuído", lambda x: _n(x.iloc[0])),
            Total =("Número SA","count"),
            INST  =("Macro Atividade", lambda x: (x=="INST-FTTH").sum()),
            REP   =("Macro Atividade", lambda x: (x=="REP-FTTH").sum()),
        ).reset_index()
        ss_tec = sem_suc.groupby("CODIGO_TECNICO_EXTRAIDO").size().reset_index(name="SemSuc")
        pt = pt.merge(ss_tec, on="CODIGO_TECNICO_EXTRAIDO", how="left")
        pt["SemSuc"] = pt["SemSuc"].fillna(0).astype(int)
        pt["Efic%"]  = (pt["Total"]/(pt["Total"]+pt["SemSuc"]).replace(0,1)*100).round(1)
        pt = pt.sort_values("Total", ascending=False).reset_index(drop=True)
        pt.columns = ["TR","Nome","Total","INST","REP","Sem Suc.","Eficacia%"]
        st.dataframe(pt, use_container_width=True, hide_index=True,
            column_config={
                "Total":    st.column_config.ProgressColumn("Total", format="%d", min_value=0,
                            max_value=int(pt["Total"].max()) if not pt.empty else 1),
                "Eficacia%":st.column_config.ProgressColumn("Eficacia%", format="%.1f%%", min_value=0, max_value=100),
            })

    _sec("Sem Sucesso — Pendencias do Dia")
    if sem_suc.empty:
        st.success("Nenhuma pendencia no dia.")
    else:
        ok = [c for c in ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC",
                           "Macro Atividade","Descrição","Observação",
                           "Código de encerramento"] if c in sem_suc.columns]
        st.dataframe(sem_suc[ok].rename(columns={
            "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
            "Macro Atividade":"Tipo","Código de encerramento":"Cod. Enc."}),
            use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        _sec("Repetidos Abertos no Dia")
        if rep_dia_ab.empty:
            st.success("Nenhum repetido aberto hoje.")
        else:
            cols_rep = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess"]
            if "rep_tecnico_pai" in rep_dia_ab.columns:
                rep_dia_ab["TR_PAI"] = rep_dia_ab["rep_tecnico_pai"].apply(_extrair_tr)
                cols_rep.extend(["rep_tecnico_pai","TR_PAI"])
            if "ALARMADO" in rep_dia_ab.columns:
                cols_rep.append("ALARMADO")
            df_show = rep_dia_ab[cols_rep].copy()
            rename_map = {
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON",
                "rep_tecnico_pai":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            }
            st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

    with c2:
        _sec("Repetidos em Garantia (Abertos)")
        if rep_ab_tot.empty:
            st.success("Nenhum reparo em garantia.")
        else:
            cols_rep = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","DIA_AB"]
            if "rep_tecnico_pai" in rep_ab_tot.columns:
                rep_ab_tot["TR_PAI"] = rep_ab_tot["rep_tecnico_pai"].apply(_extrair_tr)
                cols_rep.extend(["rep_tecnico_pai","TR_PAI"])
            if "ALARMADO" in rep_ab_tot.columns:
                cols_rep.append("ALARMADO")
            df_show = rep_ab_tot[cols_rep].copy()
            rename_map = {
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON","DIA_AB":"Abertura",
                "rep_tecnico_pai":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            }
            st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

    c3, c4 = st.columns(2)
    with c3:
        _sec("Infancia — Instalacoes do Dia")
        if inf_dia.empty:
            st.success("Nenhuma infancia hoje.")
        else:
            cols_inf = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess"]
            if "SA_REPARO_INFANCIA" in inf_dia.columns:
                cols_inf.append("SA_REPARO_INFANCIA")
            if "inf_tecnico_pai" in inf_dia.columns:
                inf_dia["TR_PAI"] = inf_dia["inf_tecnico_pai"].apply(_extrair_tr)
                cols_inf.extend(["inf_tecnico_pai","TR_PAI"])
            df_show = inf_dia[cols_inf].copy()
            rename_map = {
                "Número SA":"SA Inst.","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON",
                "SA_REPARO_INFANCIA":"SA Reparo",
                "inf_tecnico_pai":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            }
            st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

    with c4:
        _sec("Infancia Aberta (Reparo em Andamento)")
        estados_ab = ["ATRIBUÍDO","NÃO ATRIBUÍDO","RECEBIDO","EM EXECUÇÃO","EM DESLOCAMENTO"]
        gpons_suc = set(suc["FSLOI_GPONAccess"].dropna().str.upper())
        inf_ab_dia = ds[
            (ds["Macro Atividade"] == "REP-FTTH") &
            (ds["Estado"].isin(estados_ab)) &
            (ds["FLAG_INFANCIA_30D"] == "SIM") &
            (ds["FSLOI_GPONAccess"].str.upper().isin(gpons_suc))
        ].copy()
        if inf_ab_dia.empty:
            st.success("Nenhuma infancia aberta.")
        else:
            cols_ab = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","Estado"]
            if "inf_tecnico_pai" in inf_ab_dia.columns:
                inf_ab_dia["TR_PAI"] = inf_ab_dia["inf_tecnico_pai"].apply(_extrair_tr)
                cols_ab.extend(["inf_tecnico_pai","TR_PAI"])
            df_show = inf_ab_dia[cols_ab].copy()
            rename_map = {
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON",
                "inf_tecnico_pai":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            }
            st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

    _sec("P0 — Controle de Encerramento")
    cp1, cp2 = st.columns(2)
    with cp1:
        st.markdown("**P0 10h — Nao encerraram ate as 10h**")
        if p0_10.empty:
            st.success("Todos encerraram ate 10h.")
        else:
            t10 = p0_10.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
                Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])),
                Qtd =("Número SA","count")).reset_index()
            t10.columns = ["TR","Nome","Qtd"]
            st.dataframe(t10, use_container_width=True, hide_index=True)
    with cp2:
        st.markdown("**P0 15h — Nao encerraram ate as 15h**")
        if p0_15.empty:
            st.success("Todos encerraram ate 15h.")
        else:
            t15 = p0_15.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
                Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])),
                Qtd =("Número SA","count")).reset_index()
            t15.columns = ["TR","Nome","Qtd"]
            st.dataframe(t15, use_container_width=True, hide_index=True)


# =============================================================================
# 8. TELA QUALIDADE (COMPLETA + ATA INLINE + UPLOAD DRIVE)
# =============================================================================

def _cls_prod(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ("S/D", "⬜", "#94a3b8", 0)
    v = float(v)
    if v >= 6:   return ("EXCELENTE",        "🏆", "#1e3a5f", 4)
    if v >= 5:   return ("PARABENS",         "🟢", "#16a34a", 3)
    if v >= 4:   return ("PARABENS",         "🟢", "#16a34a", 3)
    if v >= 3:   return ("ATENCAO",          "🟡", "#d97706", 2)
    if v >= 1:   return ("PRECISA MELHORAR", "🔴", "#dc2626", 1)
    return            ("PRECISA MELHORAR",   "🔴", "#dc2626", 1)

def _cls_efic(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ("S/D", "⬜", "#94a3b8", 0)
    v = float(v)
    if v >= 85:  return ("EXCELENTE",        "🏆", "#1e3a5f", 4)
    if v >= 82:  return ("PARABENS",         "🟢", "#16a34a", 3)
    if v >= 75:  return ("ATENCAO",          "🟡", "#d97706", 2)
    return            ("PRECISA MELHORAR",   "🔴", "#dc2626", 1)

def _cls_rep(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ("S/D", "⬜", "#94a3b8", 0)
    v = float(v)
    if v < 2:    return ("EXCELENTE",        "🏆", "#1e3a5f", 4)
    if v <= 5:   return ("OTIMO",            "🟢", "#16a34a", 3)
    if v <= 9:   return ("PARABENS",         "🟢", "#16a34a", 2)
    return            ("PRECISA MELHORAR",   "🔴", "#dc2626", 0)

def _cls_inf(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ("S/D", "⬜", "#94a3b8", 0)
    v = float(v)
    if v < 3:    return ("OTIMO",            "🟢", "#16a34a", 3)
    return            ("PRECISA MELHORAR",   "🔴", "#dc2626", 0)

def _nota_total(pc, ec, rc, ic):
    return pc[3] + ec[3] + rc[3] + ic[3]

def _cor_nota(n):
    if n >= 13: return "#1e3a5f"
    if n >= 9:  return "#16a34a"
    if n >= 5:  return "#d97706"
    return "#dc2626"

def _badge(label, cor):
    return (f'<span style="background:{cor};color:white;padding:2px 10px;'
            f'border-radius:12px;font-size:11px;font-weight:700">{label}</span>')

def _html_ata_qualidade(nome, codigo, supervisor, mes_ref,
                        prod_val, efic_val, rep_val, inf_val,
                        prod_cls, efic_cls, rep_cls, inf_cls, nota):
    nota_max = 16
    titulo = "ATA DE DESEMPENHO OPERACIONAL"
    cor_h = "135deg,#1e3a5f 0%,#2563eb 100%"
    
    if nota >= 13:
        msg = (f"Prezado(a) <strong>{nome}</strong>, seu desempenho no periodo foi "
               f"excepcional. Todos os indicadores estao dentro ou acima das metas. Continue assim!")
    elif nota >= 9:
        msg = (f"Prezado(a) <strong>{nome}</strong>, seu desempenho esta dentro das metas "
               f"esperadas. Identifique os pontos de atencao para atingir a excelencia.")
    elif nota >= 5:
        msg = (f"Prezado(a) <strong>{nome}</strong>, ha indicadores que precisam de atencao. "
               f"Vamos alinhar um plano de acao para a melhoria do desempenho.")
    else:
        msg = (f"Prezado(a) <strong>{nome}</strong>, seus indicadores estao abaixo das metas "
               f"estabelecidas. E necessario um plano de acao imediato.")

    def _ind(lbl, val, cls):
        return (f'<div style="flex:1;min-width:140px;border:1px solid #e2e8f0;border-radius:8px;'
                f'padding:14px;text-align:center">'
                f'<div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">{lbl}</div>'
                f'<div style="font-size:20px;font-weight:700;color:#1a3a8f;margin-bottom:8px">{val}</div>'
                f'{_badge(cls[0], cls[2])}'
                f'</div>')

    inds_html = (
        _ind("Produtividade", prod_val, prod_cls) +
        _ind("Eficacia",      efic_val, efic_cls) +
        _ind("Repetida",      rep_val,  rep_cls)  +
        _ind("Infancia",      inf_val,  inf_cls)
    )

    cod_safe = codigo.replace("'","\\'")
    nome_safe = nome.replace("'","\\'")
    sup_safe  = supervisor.replace("'","\\'")
    ts_now    = datetime.now().strftime("%Y%m%d_%H%M%S")
    dt_now    = datetime.now().strftime("%d/%m/%Y %H:%M")

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
.hdr{{background:linear-gradient({cor_h});color:white;padding:24px 30px;text-align:center}}
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

    <!-- Assinatura Tecnico -->
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

    <!-- Assinatura Supervisor -->
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
  const pdfBase64 = doc.output('datauristring').split(',')[1];
  const urlAtas = '{URL_ATAS_DRIVE}';
  const payload = {{
    supervisor: '{sup_safe}',
    tecnico: '{cod_safe}',
    pdf_base64: pdfBase64
  }};
  fetch(urlAtas, {{ method: 'POST', mode: 'no-cors', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(payload) }})
    .then(() => alert('ATA salva no Google Drive com sucesso!'))
    .catch(err => alert('Erro ao salvar no Drive: ' + err));
  doc.save('ata_qualidade_{cod_safe}_{ts_now}.pdf');
}};
window.addEventListener('resize',()=>{{
  setTimeout(()=>{{
    [padT,padS].forEach(p=>{{if(p&&p.canvas){{const r=p.canvas.getBoundingClientRect();const d=p.toData();p.canvas.width=r.width;p.canvas.height=r.height;if(d&&d.length)p.fromData(d);}}}});
  }},200);
}});
</script>
</body>
</html>"""


def tela_qualidade(dm, ds, f):
    _header("🏆", "Qualidade", f)

    def _n(v):
        return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    mes_ref = f.get("mes", "")

    tecs = sorted(dm["CODIGO_TECNICO_EXTRAIDO"].dropna().unique())
    if not tecs:
        st.warning("Nenhum tecnico encontrado para os filtros selecionados.")
        return

    rows = []
    for cod in tecs:
        df_t = dm[dm["CODIGO_TECNICO_EXTRAIDO"] == cod].copy()
        if df_t.empty:
            continue

        nome = _n(df_t["Técnico Atribuído"].dropna().iloc[0]) if not df_t["Técnico Atribuído"].dropna().empty else cod

        suc = df_t[df_t["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
        dias_unicos = suc["DIA_FIM"].dropna().nunique()
        prod_media  = round(len(suc) / dias_unicos, 1) if dias_unicos > 0 else None

        n_suc  = (df_t["FLAG_CONCLUIDO_SUCESSO"]     == "SIM").sum()
        n_ss   = (df_t["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM").sum()
        efic   = round(n_suc / (n_suc + n_ss) * 100, 1) if (n_suc + n_ss) > 0 else None

        rep_den = (df_t["Macro Atividade"] == "REP-FTTH").sum()
        rep_num = ((df_t["Macro Atividade"] == "REP-FTTH") &
                   (df_t["FLAG_REPETIDO"] == "SIM")).sum()
        rep_pct = round(rep_num / rep_den * 100, 1) if rep_den > 0 else None

        inst_den = (df_t["FLAG_INSTALACAO_VALIDA"] == "SIM").sum()
        inst_num = ((df_t["FLAG_INSTALACAO_VALIDA"] == "SIM") &
                    (df_t["FLAG_INFANCIA"] == "SIM")).sum()
        inf_pct  = round(inst_num / inst_den * 100, 1) if inst_den > 0 else None

        pc = _cls_prod(prod_media)
        ec = _cls_efic(efic)
        rc = _cls_rep(rep_pct)
        ic = _cls_inf(inf_pct)
        nota = _nota_total(pc, ec, rc, ic)

        rows.append({
            "cod":        cod,
            "nome":       nome,
            "prod_media": prod_media,
            "efic_pct":   efic,
            "rep_pct":    rep_pct,
            "inf_pct":    inf_pct,
            "prod_cls":   pc,
            "efic_cls":   ec,
            "rep_cls":    rc,
            "inf_cls":    ic,
            "nota":       nota,
            "n_suc":      n_suc,
            "dias":       dias_unicos,
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
        ["Tecnicos",      "🏆 Excelente",  "✅ Bom",      "⚠️ Atencao",  "🔴 Melhoria"],
        [len(df_q),       n_exc,            n_bom,          n_atc,          n_mel],
        ["kpi-blue",      "kpi-blue",       "kpi-green",    "kpi-yellow",   "kpi-red"],
    ):
        col.markdown(_kpi(lbl, val, "", cls), unsafe_allow_html=True)

    st.write("")
    st.write("")
    with st.expander("📋 Regras de classificacao", expanded=False):
        st.markdown("""| Indicador | 🏆 Excelente | 🟢 Parabens / Otimo | 🟡 Atencao | 🔴 Precisa Melhorar |
|---|---|---|---|---|
| **Produtividade** (ativ/dia) | ≥ 6 | 4 ou 5 = Parabens | 3 | ≤ 2 |
| **Eficacia** (%) | ≥ 85% | 82–85% | 75–82% | < 75% |
| **Repetida** (%) | < 2% | 2–5% = Otimo · 5–9% = Parabens | — | > 9% |
| **Infancia** (%) | — | < 3% = Otimo | — | ≥ 3% |

**Pontuacao:** cada indicador vale 0–4 pontos. Total 0–16.
≥13 Excelente | 9–12 Bom | 5–8 Atencao | <5 Precisa Melhorar""")

    _sec("Ranking de Qualidade por Tecnico")

    disp = []
    for _, r in df_q.iterrows():
        pv = f"{r['prod_media']:.1f}" if r['prod_media'] is not None else "S/D"
        ev = f"{r['efic_pct']:.1f}%"  if r['efic_pct']   is not None else "S/D"
        rv = f"{r['rep_pct']:.1f}%"   if r['rep_pct']    is not None else "S/D"
        iv = f"{r['inf_pct']:.1f}%"   if r['inf_pct']    is not None else "S/D"
        disp.append({
            "Nome":       r["nome"],
            "TR":         r["cod"],
            "Prod.":      pv,
            "Prod_S":     r["prod_cls"][0],
            "Efic.":      ev,
            "Efic_S":     r["efic_cls"][0],
            "Repet.":     rv,
            "Rep_S":      r["rep_cls"][0],
            "Infan.":     iv,
            "Inf_S":      r["inf_cls"][0],
            "Nota":       f"{r['nota']}/16",
        })

    df_disp = pd.DataFrame(disp)

    _cor_map = {
        "EXCELENTE":        "background-color:#1e3a5f;color:white;font-weight:700",
        "PARABENS":         "background-color:#16a34a;color:white;font-weight:700",
        "OTIMO":            "background-color:#15803d;color:white;font-weight:700",
        "ATENCAO":          "background-color:#d97706;color:white;font-weight:700",
        "PRECISA MELHORAR": "background-color:#dc2626;color:white;font-weight:700",
        "S/D":              "background-color:#e2e8f0;color:#64748b",
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
            "Nome":   st.column_config.TextColumn("Nome",   width="medium"),
            "TR":     st.column_config.TextColumn("TR",     width="small"),
            "Nota":   st.column_config.TextColumn("Nota",   width="small"),
            "Prod.":  st.column_config.TextColumn("Prod.ativ/dia", width="small"),
            "Efic.":  st.column_config.TextColumn("Eficacia",      width="small"),
            "Repet.": st.column_config.TextColumn("Repetida",      width="small"),
            "Infan.": st.column_config.TextColumn("Infancia",      width="small"),
            "Prod_S": st.column_config.TextColumn("Status Prod.",  width="medium"),
            "Efic_S": st.column_config.TextColumn("Status Efic.",  width="medium"),
            "Rep_S":  st.column_config.TextColumn("Status Rep.",   width="medium"),
            "Inf_S":  st.column_config.TextColumn("Status Inf.",   width="medium"),
        }
    )

    st.write("")
    _sec("Distribuicao de Classificacoes por Indicador")

    _cats  = ["EXCELENTE", "OTIMO", "PARABENS", "ATENCAO", "PRECISA MELHORAR", "S/D"]
    _cores = ["#1e3a5f",   "#2d5a8e", "#4a7db5", "#6b9bd2", "#a0c4ff",           "#94a3b8"]
    _inds  = ["prod_cls",  "efic_cls","rep_cls", "inf_cls"]
    _lbls  = ["Produtividade","Eficacia","Repetida","Infancia"]

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

    layout_dist = _lyt("Distribuicao por Indicador e Classificacao", 340)
    layout_dist["barmode"] = "stack"
    layout_dist["yaxis"] = dict(title="Qtd. Tecnicos", gridcolor=C["grid"])
    layout_dist["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    fig_dist.update_layout(layout_dist)
    st.plotly_chart(fig_dist, use_container_width=True)

    _sec("Gerar Atas de Qualidade — Assinatura Digital")
    st.caption("Clique em 📄 ATA para abrir o formulário de assinatura logo abaixo. Ao salvar, o PDF será enviado automaticamente para o Google Drive.")

    _h1, _h2, _h3, _h4, _h5, _h6, _h7 = st.columns([3, 1, 1, 1, 1, 1, 1])
    for col, txt in zip(
        [_h1, _h2, _h3, _h4, _h5, _h6, _h7],
        ["**Tecnico**", "**Prod.**", "**Efic.**", "**Repet.**", "**Inf.**", "**Nota**", ""],
    ):
        col.markdown(txt)

    sup_nome = f.get("supervisor", "N/I") or "N/I"

    if "ata_html" not in st.session_state:
        st.session_state.ata_html = None
        st.session_state.ata_nome = ""

    for _, r in df_q.iterrows():
        pv = f"{r['prod_media']:.1f} /dia" if r['prod_media'] is not None else "S/D"
        ev = f"{r['efic_pct']:.1f}%"       if r['efic_pct']   is not None else "S/D"
        rv = f"{r['rep_pct']:.1f}%"        if r['rep_pct']    is not None else "S/D"
        iv = f"{r['inf_pct']:.1f}%"        if r['inf_pct']    is not None else "S/D"

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
                st.session_state.ata_html = _html_ata_qualidade(
                    nome      = r["nome"],
                    codigo    = r["cod"],
                    supervisor= sup_nome,
                    mes_ref   = mes_ref,
                    prod_val  = pv,
                    efic_val  = ev,
                    rep_val   = rv,
                    inf_val   = iv,
                    prod_cls  = r["prod_cls"],
                    efic_cls  = r["efic_cls"],
                    rep_cls   = r["rep_cls"],
                    inf_cls   = r["inf_cls"],
                    nota      = r["nota"],
                )
                st.session_state.ata_nome = r["nome"]
                st.rerun()

    if st.session_state.ata_html:
        st.markdown(f"**📝 Assinatura de {st.session_state.ata_nome}**")
        st.components.v1.html(st.session_state.ata_html, height=900, scrolling=True)
        if st.button("❌ Fechar ATA"):
            st.session_state.ata_html = None
            st.session_state.ata_nome = ""
            st.rerun()


# =============================================================================
# 9. TELA JUSTIFICATIVAS (DIÁRIA – COM ENDEREÇO, DESCRIÇÃO E HISTÓRICO)
# =============================================================================

def tela_justificativas(df, f):
    _header("📝", "Justificativas Diárias", f)
    ds = _escopo(df, f)

    datas_disp = sorted(ds["FIM_DT"].dropna().dt.date.unique(), reverse=True)
    if not datas_disp:
        st.warning("Nenhuma data disponível.")
        return

    hoje = datetime.today().date()
    valor_padrao = hoje if hoje in datas_disp else datas_disp[0]
    dia_sel = st.date_input("Data de referência", value=valor_padrao,
                            min_value=datas_disp[-1], max_value=datas_disp[0],
                            key="dia_just")

    dm = ds[ds["FIM_DT"].dt.date == dia_sel].copy()

    # Função auxiliar para montar endereço
    def _endereco(row):
        parts = []
        if "Logradouro" in row and pd.notna(row["Logradouro"]) and str(row["Logradouro"]).strip():
            parts.append(str(row["Logradouro"]).strip())
        if "Número" in row and pd.notna(row["Número"]) and str(row["Número"]).strip():
            parts.append(str(row["Número"]).strip())
        if "Bairro" in row and pd.notna(row["Bairro"]) and str(row["Bairro"]).strip():
            parts.append(str(row["Bairro"]).strip())
        cidade = ""
        if "Cidade" in row and pd.notna(row["Cidade"]) and str(row["Cidade"]).strip():
            cidade = str(row["Cidade"]).strip()
        elif "Território de serviço: Nome" in row:
            terr = str(row["Território de serviço: Nome"]).strip()
            if "." in terr:
                partes_terr = terr.split(".")
                if len(partes_terr) >= 2:
                    cidade = partes_terr[1].strip()
            else:
                cidade = terr
        if cidade:
            parts.append(cidade)
        return ", ".join(parts) if parts else "Endereço não disponível"

    # Função interna para histórico do GPON (simplificada)
    def _hist_gpon_md(gpon, filho_tr, pai_tr, filho_fim):
        hist = df[df["FSLOI_GPONAccess"] == gpon].sort_values("FIM_DT")
        if hist.empty:
            return "Sem histórico disponível."
        linhas = []
        for _, row in hist.iterrows():
            sa = row.get("Número SA", "")
            data = row.get("FIM_DT", "")
            if pd.isna(data):
                data_str = "S/D"
            else:
                data_str = pd.to_datetime(data).strftime("%d/%m/%Y") if not isinstance(data, str) else data
            tecnico = row.get("NOME_TEC", "")
            tr = row.get("CODIGO_TECNICO_EXTRAIDO", "")
            desc = row.get("Descrição", "")

            if tr == filho_tr and row.get("FLAG_REPETIDO", "NAO") == "SIM":
                icone = "🔸 REPETIDO"
            elif tr == pai_tr and pd.notna(data) and pd.notna(filho_fim):
                if pd.to_datetime(data) < pd.to_datetime(filho_fim):
                    icone = "🔹 PAI (contabiliza)"
                else:
                    icone = "📌"
            else:
                datas = hist["FIM_DT"].dropna().sort_values()
                if len(datas) >= 2 and pd.notna(data):
                    if pd.to_datetime(data) == datas.iloc[-2]:
                        icone = "🔹 PAI (contabiliza)"
                    else:
                        icone = "📌"
                else:
                    icone = "📌"

            linha = f"   {icone}: SA {sa} - {data_str} - {tecnico} - {tr}"
            if desc and str(desc).strip():
                linha += f"\n      📝 {str(desc).strip()}"
            linhas.append(linha)
        return "\n".join(linhas) if linhas else "Sem histórico."

    tab1, tab2, tab3, tab4 = st.tabs(["⚠️ PZERO", "🔁 REPETIDOS", "👶 INFÂNCIA", "🚨 ALARMES 24H"])

    supervisor_atual = f.get("supervisor", "N/I")

    # ---------- PZERO ----------
    with tab1:
        st.markdown("### PZero do dia")
        pzero = dm[((dm["FLAG_P0_10_DIA"] == "SIM") | (dm["FLAG_P0_15_DIA"] == "SIM"))]
        if pzero.empty:
            st.success("Nenhum PZero registrado.")
        else:
            for idx, row in pzero.iterrows():
                with st.form(key=f"pzero_form_{idx}"):
                    c1, c2, c3 = st.columns([2,2,2])
                    c1.write(f"**SA:** {row['Número SA']}")
                    c2.write(f"**TR:** {row['CODIGO_TECNICO_EXTRAIDO']} - {row['NOME_TEC']}")
                    c3.write(f"**GPON:** {row['FSLOI_GPONAccess']}")
                    st.caption(f"🏠 Endereço: {_endereco(row)}")
                    desc = row.get("Descrição", "")
                    if pd.notna(desc) and str(desc).strip():
                        st.caption(f"📋 Descrição: {str(desc).strip()}")
                    # Histórico GPON
                    with st.expander("📜 Histórico do GPON"):
                        gpon = row.get("FSLOI_GPONAccess", "")
                        if gpon:
                            st.markdown(_hist_gpon_md(gpon, "", "", None), unsafe_allow_html=True)
                    just = st.text_area("Justificativa", key=f"just_pzero_{idx}")
                    if st.form_submit_button("Enviar"):
                        if not just:
                            st.error("Justificativa é obrigatória.")
                        else:
                            payload = {
                                "supervisor": supervisor_atual,
                                "tecnico": row["CODIGO_TECNICO_EXTRAIDO"],
                                "tipo": "PZERO",
                                "referencia": str(row["Número SA"]),
                                "justificativa": f"[{dia_sel.strftime('%d/%m/%Y')}] {just}"
                            }
                            with st.spinner("Enviando..."):
                                try:
                                    resp = requests.post(URL_JUSTIFICATIVA, json=payload, timeout=15)
                                    if resp.status_code == 200 and resp.json().get("status") == "ok":
                                        st.success("✅ PZERO justificado!")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Erro: {resp.json().get('mensagem', 'Falha desconhecida')}")
                                except Exception as e:
                                    st.error(f"❌ Falha na comunicação: {e}")

    # ---------- REPETIDOS ----------
    with tab2:
        st.markdown("### Repetidos do dia")
        repetidos = dm[(dm["Macro Atividade"] == "REP-FTTH") &
                        (dm["FLAG_REPETIDO"] == "SIM") &
                        (dm["TEC_ANTERIOR"].notna())]
        if repetidos.empty:
            st.success("Nenhum repetido registrado.")
        else:
            for idx, row in repetidos.iterrows():
                with st.form(key=f"rep_form_{idx}"):
                    c1, c2, c3 = st.columns([2,2,2])
                    c1.write(f"**SA:** {row['Número SA']}")
                    c2.write(f"**TR:** {row['CODIGO_TECNICO_EXTRAIDO']} - {row['NOME_TEC']}")
                    c3.write(f"**GPON:** {row['FSLOI_GPONAccess']}")
                    st.caption(f"🏠 Endereço: {_endereco(row)}")
                    desc = row.get("Descrição", "")
                    if pd.notna(desc) and str(desc).strip():
                        st.caption(f"📋 Descrição: {str(desc).strip()}")
                    # Histórico GPON
                    with st.expander("📜 Histórico do GPON"):
                        gpon = row["FSLOI_GPONAccess"]
                        filho_tr = row["CODIGO_TECNICO_EXTRAIDO"]
                        pai_tr = row.get("TEC_ANTERIOR", "")
                        filho_fim = row["FIM_DT"]
                        st.markdown(_hist_gpon_md(gpon, filho_tr, pai_tr, filho_fim), unsafe_allow_html=True)
                    just = st.text_area("Justificativa", key=f"just_rep_{idx}")
                    if st.form_submit_button("Enviar"):
                        if not just:
                            st.error("Justificativa é obrigatória.")
                        else:
                            payload = {
                                "supervisor": supervisor_atual,
                                "tecnico": row["CODIGO_TECNICO_EXTRAIDO"],
                                "tipo": "REPETIDO",
                                "referencia": str(row["Número SA"]),
                                "justificativa": f"[{dia_sel.strftime('%d/%m/%Y')}] {just}"
                            }
                            with st.spinner("Enviando..."):
                                try:
                                    resp = requests.post(URL_JUSTIFICATIVA, json=payload, timeout=15)
                                    if resp.status_code == 200 and resp.json().get("status") == "ok":
                                        st.success("✅ Repetido justificado!")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Erro: {resp.json().get('mensagem', 'Falha desconhecida')}")
                                except Exception as e:
                                    st.error(f"❌ Falha na comunicação: {e}")

    # ---------- INFÂNCIA ----------
    with tab3:
        st.markdown("### Infâncias do dia")
        infancias = dm[(dm["Macro Atividade"] == "INST-FTTH") &
                        (dm["FLAG_INFANCIA"] == "SIM")]
        if infancias.empty:
            st.success("Nenhuma infância registrada.")
        else:
            for idx, row in infancias.iterrows():
                with st.form(key=f"inf_form_{idx}"):
                    c1, c2, c3 = st.columns([2,2,2])
                    c1.write(f"**SA:** {row['Número SA']}")
                    c2.write(f"**TR:** {row['CODIGO_TECNICO_EXTRAIDO']} - {row['NOME_TEC']}")
                    c3.write(f"**GPON:** {row['FSLOI_GPONAccess']}")
                    st.caption(f"🏠 Endereço: {_endereco(row)}")
                    desc = row.get("Descrição", "")
                    if pd.notna(desc) and str(desc).strip():
                        st.caption(f"📋 Descrição: {str(desc).strip()}")
                    # Histórico GPON
                    with st.expander("📜 Histórico do GPON"):
                        gpon = row["FSLOI_GPONAccess"]
                        st.markdown(_hist_gpon_md(gpon, "", "", None), unsafe_allow_html=True)
                    just = st.text_area("Justificativa", key=f"just_inf_{idx}")
                    if st.form_submit_button("Enviar"):
                        if not just:
                            st.error("Justificativa é obrigatória.")
                        else:
                            payload = {
                                "supervisor": supervisor_atual,
                                "tecnico": row["CODIGO_TECNICO_EXTRAIDO"],
                                "tipo": "INFANCIA",
                                "referencia": str(row["Número SA"]),
                                "justificativa": f"[{dia_sel.strftime('%d/%m/%Y')}] {just}"
                            }
                            with st.spinner("Enviando..."):
                                try:
                                    resp = requests.post(URL_JUSTIFICATIVA, json=payload, timeout=15)
                                    if resp.status_code == 200 and resp.json().get("status") == "ok":
                                        st.success("✅ Infância justificada!")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Erro: {resp.json().get('mensagem', 'Falha desconhecida')}")
                                except Exception as e:
                                    st.error(f"❌ Falha na comunicação: {e}")

    # ---------- ALARMES 24H ----------
    with tab4:
        st.markdown("### Alarmes 24h do dia")
        alarmes = dm[(dm["ALARMADO"] == "SIM")]
        if alarmes.empty:
            st.success("Nenhum alarme registrado.")
        else:
            for idx, row in alarmes.iterrows():
                with st.form(key=f"alrm_form_{idx}"):
                    c1, c2, c3 = st.columns([2,2,2])
                    c1.write(f"**SA:** {row['Número SA']}")
                    c2.write(f"**TR:** {row['CODIGO_TECNICO_EXTRAIDO']} - {row['NOME_TEC']}")
                    c3.write(f"**GPON:** {row['FSLOI_GPONAccess']}")
                    st.caption(f"🏠 Endereço: {_endereco(row)}")
                    desc = row.get("Descrição", "")
                    if pd.notna(desc) and str(desc).strip():
                        st.caption(f"📋 Descrição: {str(desc).strip()}")
                    with st.expander("📜 Histórico do GPON"):
                        gpon = row.get("FSLOI_GPONAccess", "")
                        if gpon:
                            st.markdown(_hist_gpon_md(gpon, "", "", None), unsafe_allow_html=True)
                    just = st.text_area("Justificativa", key=f"just_alrm_{idx}")
                    if st.form_submit_button("Enviar"):
                        if not just:
                            st.error("Justificativa é obrigatória.")
                        else:
                            payload = {
                                "supervisor": supervisor_atual,
                                "tecnico": row["CODIGO_TECNICO_EXTRAIDO"],
                                "tipo": "ALARME_24H",
                                "referencia": str(row["Número SA"]),
                                "justificativa": f"[{dia_sel.strftime('%d/%m/%Y')}] {just}"
                            }
                            with st.spinner("Enviando..."):
                                try:
                                    resp = requests.post(URL_JUSTIFICATIVA, json=payload, timeout=15)
                                    if resp.status_code == 200 and resp.json().get("status") == "ok":
                                        st.success("✅ Alarme justificado!")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Erro: {resp.json().get('mensagem', 'Falha desconhecida')}")
                                except Exception as e:
                                    st.error(f"❌ Falha na comunicação: {e}")


# =============================================================================
# 10. MAIN
# =============================================================================

def main():
    df = carregar_base()
    if df is None:
        st.error("❌ Não foi possível carregar a base de dados. Verifique o token de acesso.")
        return

    f    = sidebar(df)
    tela = f["tela"]
    dm   = _filtrar(df, f)
    ds   = _escopo(df, f)

    if f["supervisor"]:
        st.markdown(
            f'<div class="banner-sup">👑 Equipe de <strong>{f["supervisor"]}</strong>'
            f' — {len(f["tecs_sup"])} tecnico(s) | {f["mes"]}</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="banner-sup" style="background:#f0f4f8">'
            '🕐 Dados carregados com sucesso.</div>',
            unsafe_allow_html=True)

    if tela == "📝 Justificativas":
        tela_justificativas(df, f)
        return

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
