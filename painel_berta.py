#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERTA — Painel Operacional do Supervisor v3.2 (W)
Telas: Producao Diaria | Repetidos | Infancia | Calendario | Qualidade | Diario
Fonte de dados: Repositório (API)
"""

import os
import re
import base64
import io
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
# 4. CARREGAMENTO DO DATAFRAME
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def carregar_base_repositorio():
    """Tenta carregar o BASEBOT.csv via API do repositório, com detecção automática do separador."""
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
    """Fallback para arquivo local (apenas desenvolvimento)."""
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
    """Orquestra o carregamento do BASEBOT.csv."""
    df = carregar_base_repositorio()
    if df is None:
        df = carregar_base_local()
    if df is not None:
        return _processar_df(df)
    return None


def _processar_df(df):
    """Normaliza e cria colunas derivadas (adaptado ao novo layout do BASEBOT.csv)."""
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

    if "Logradouro" not in df.columns:
        df["Logradouro"] = df.get("LOGRADOURO", "")

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
                    line=dict(color=C["yellow"], width=2), marker_size=6, secondary_y=True)
    if meta is not None:
        fig.add_hline(y=meta, line_dash="dash", line_color=C["red"],
                      annotation_text=f"Meta {meta}%", secondary_y=True)
    fig.update_layout(**_lyt(titulo, h))
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return fig


# =============================================================================
# 6. SIDEBAR – sem upload manual
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
        df_atual = df

        # Mês padrão: mês atual, se existir
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
# 7. TELAS
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


def tela_repetidos(dm, ds, f):
    _header("🔁", "Repetidos", f)

    tem_vip = ("TEC_ANTERIOR" in dm.columns) and ("FLAG_REPETIDO" in dm.columns)

    den_df = dm[
        (dm["Macro Atividade"] == "REP-FTTH") &
        (dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM")
    ]
    den_total = len(den_df)

    if tem_vip:
        num_df = dm[
            (dm["FLAG_REPETIDO"] == "SIM") &
            (dm["TEC_ANTERIOR"].notna()) &
            (dm["TEC_ANTERIOR"].str.strip() != "")
        ]
        repetidos_total = len(num_df)
        fonte_label = "🏛️ Fonte: VIP Oficial (TEC_ANTERIOR + FLAG_REPETIDO)"
    else:
        gpons_rep, den_total, _ = _calcular_repetidos_gpon(ds, f["mes"])
        repetidos_total = len(gpons_rep)
        num_df = pd.DataFrame()
        fonte_label = "⚙️ Fonte: Cálculo Interno (GPON)"

    taxa = round(repetidos_total / den_total * 100, 2) if den_total > 0 else 0

    rep_ab = ds[ds["FLAG_REPETIDO_ABERTO"] == "SIM"] if "FLAG_REPETIDO_ABERTO" in ds.columns else pd.DataFrame()

    if tem_vip:
        rep_alrm = dm[(dm["FLAG_REPETIDO"] == "SIM") & (dm["ALARMADO"] == "SIM")]
        rep_alrm_count = len(rep_alrm)
    else:
        rep_alrm_count = 0

    cols = st.columns(5)
    for col, (lb,vl,sb,cl) in zip(cols,[
        ("Total Reparos", f"{den_total:,}",   "abertos no mes",  "kpi-blue"),
        ("Repetidos",     f"{repetidos_total:,}",  "reparos filhos",  "kpi-red" if taxa>9 else "kpi-yellow"),
        ("Taxa %",        f"{taxa}%",          "meta: <= 9%",     "kpi-red" if taxa>9 else "kpi-green"),
        ("Em Garantia",   f"{len(rep_ab):,}",  "abertos 30d",     "kpi-yellow"),
        ("Alarmados",     f"{rep_alrm_count}", "GPON alarmado",   "kpi-red" if rep_alrm_count>0 else "kpi-green"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:11px;color:#64748b;margin:6px 0 14px 2px;">{fonte_label}</div>',
        unsafe_allow_html=True)

    _sec("Indicador por Tecnico")
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

    tb["Status"] = tb["Taxa%"].apply(lambda t: "🔴" if t>12 else "🟡" if t>9 else "🟢" if t>0 else "⚪")
    st.dataframe(tb[["Status","Nome","TR","Repetidos","Total","Taxa%"]], use_container_width=True, hide_index=True,
                 column_config={"Taxa%": st.column_config.ProgressColumn(
                     "Taxa%", format="%.1f%%", min_value=0,
                     max_value=max(float(tb["Taxa%"].max()) if not tb.empty else 1, 1))})

    if tem_vip and not num_df.empty:
        _sec("Detalhamento — Repetidos (VIP)")
        cols_det = [c for c in ["Número SA","FSLOI_GPONAccess","CODIGO_TECNICO_EXTRAIDO","NOME_TEC",
                                "rep_dias_anterior","rep_tecnico_filho","rep_cod_fech_anterior",
                                "rep_agrupador_anterior","Cidade","TEC_ANTERIOR","Logradouro"] if c in num_df.columns]
        det = num_df[cols_det].copy()
        det.rename(columns={
            "FSLOI_GPONAccess":"GPON","Número SA":"SA Filho",
            "CODIGO_TECNICO_EXTRAIDO":"TR (executor)",
            "TEC_ANTERIOR":"TR (PAI)",
            "Logradouro":"Endereço"}, inplace=True)
        st.dataframe(det, use_container_width=True, hide_index=True)


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
    fig.add_bar(x=ef_dia["DIA"].astype(str), y=ef_dia["Concluidos"], name="Concluidos", marker_color=C["navy"], yaxis="y")
    fig.add_scatter(x=ef_dia["DIA"].astype(str), y=ef_dia["Eficacia%"], name="Eficacia%", mode="lines+markers",
                    line=dict(color=C["green"],width=2), marker_size=6, yaxis="y2")
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

    # Data padrão: o dia mais recente disponível (normalmente o dia atual ou último dia útil)
    c_pick, c_info = st.columns([2, 5])
    with c_pick:
        dia_sel = st.date_input("Data de referencia",
            value=datas_disp[0],
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
# 8. TELA QUALIDADE (COMPLETA)
# =============================================================================

def _cls_prod(v):
    if pd.isna(v): return ("S/D", "⬜", "#94a3b8", 0)
    if v >= 6: return ("EXCELENTE", "🏆", "#1e3a5f", 4)
    if v >= 5: return ("PARABÉNS", "🟢", "#16a34a", 3)
    if v >= 4: return ("BOM", "🟡", "#d97706", 2)
    if v >= 1: return ("ATENÇÃO", "🟠", "#f59e0b", 1)
    return ("CRÍTICO", "🔴", "#dc2626", 0)

def _cls_efic(v):
    if pd.isna(v): return ("S/D", "⬜", "#94a3b8", 0)
    if v >= 90: return ("EXCELENTE", "🏆", "#1e3a5f", 4)
    if v >= 85: return ("PARABÉNS", "🟢", "#16a34a", 3)
    if v >= 75: return ("ATENÇÃO", "🟡", "#d97706", 2)
    return ("CRÍTICO", "🔴", "#dc2626", 0)

def _cls_rep(v):
    if pd.isna(v): return ("S/D", "⬜", "#94a3b8", 0)
    if v <= 3: return ("EXCELENTE", "🏆", "#1e3a5f", 4)
    if v <= 6: return ("PARABÉNS", "🟢", "#16a34a", 3)
    if v <= 9: return ("ATENÇÃO", "🟡", "#d97706", 2)
    return ("CRÍTICO", "🔴", "#dc2626", 0)

def _cls_inf(v):
    if pd.isna(v): return ("S/D", "⬜", "#94a3b8", 0)
    if v <= 3: return ("EXCELENTE", "🏆", "#1e3a5f", 4)
    if v <= 5: return ("PARABÉNS", "🟢", "#16a34a", 3)
    if v <= 7: return ("ATENÇÃO", "🟡", "#d97706", 2)
    return ("CRÍTICO", "🔴", "#dc2626", 0)

def _nota_total(prod_info, efic_info, rep_info, inf_info):
    return prod_info[3] + efic_info[3] + rep_info[3] + inf_info[3]

def _cor_nota(nota):
    if nota >= 13: return "#1e3a5f"
    if nota >= 9:  return "#16a34a"
    if nota >= 5:  return "#d97706"
    return "#dc2626"


def tela_qualidade(dm, ds, f):
    _header("🏆", "Qualidade", f)

    tecs = dm["CODIGO_TECNICO_EXTRAIDO"].dropna().unique()
    if len(tecs) == 0:
        st.warning("Nenhum técnico encontrado para o período.")
        return

    dados_tec = []
    for tr in tecs:
        atv = dm[dm["CODIGO_TECNICO_EXTRAIDO"] == tr]
        suc = atv[atv["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
        tot = atv[atv["Estado"].isin(["CONCLUÍDO COM SUCESSO", "CONCLUÍDO SEM SUCESSO"])]
        
        dias = atv["DIA_FIM"].nunique()
        media_diaria = round(len(suc) / dias, 1) if dias > 0 else 0.0
        
        efi = round(len(suc) / len(tot) * 100, 1) if len(tot) > 0 else 0.0
        
        # Repetidos
        if "FLAG_REPETIDO" in dm.columns and "TEC_ANTERIOR" in dm.columns:
            filhos = dm[(dm["FLAG_REPETIDO"] == "SIM") & (dm["TEC_ANTERIOR"].str.strip().str.upper() == tr)]
            num_rep = len(filhos)
            den_rep = len(dm[(dm["Macro Atividade"] == "REP-FTTH") & 
                             (dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM") & 
                             (dm["CODIGO_TECNICO_EXTRAIDO"] == tr)])
        else:
            num_rep = 0
            den_rep = 0
            df_rep_tec = ds[(ds["Macro Atividade"] == "REP-FTTH") &
                            (ds["FLAG_CONCLUIDO_SUCESSO"] == "SIM") &
                            (ds["CODIGO_TECNICO_EXTRAIDO"] == tr)]
            if not df_rep_tec.empty:
                for gpon, grupo in df_rep_tec.groupby("FSLOI_GPONAccess"):
                    grupo = grupo.sort_values("FIM_DT")
                    for i in range(len(grupo)-1):
                        if (grupo.iloc[i+1]["FIM_DT"] - grupo.iloc[i]["FIM_DT"]).days <= 30:
                            num_rep += 1
                            break
                den_rep = len(df_rep_tec)
        taxa_rep = round(num_rep / den_rep * 100, 1) if den_rep > 0 else 0.0
        
        # Infância
        if "FLAG_INFANCIA" in dm.columns:
            num_inf = len(dm[(dm["CODIGO_TECNICO_EXTRAIDO"] == tr) & (dm["FLAG_INFANCIA"] == "SIM")])
            den_inf = len(dm[(dm["Macro Atividade"] == "INST-FTTH") &
                             (dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM") &
                             (dm["CODIGO_TECNICO_EXTRAIDO"] == tr)])
        else:
            inst_tec = ds[(ds["Macro Atividade"] == "INST-FTTH") &
                          (ds["FLAG_CONCLUIDO_SUCESSO"] == "SIM") &
                          (ds["CODIGO_TECNICO_EXTRAIDO"] == tr)]
            num_inf = 0
            if not inst_tec.empty:
                rep_ds = ds[(ds["Macro Atividade"] == "REP-FTTH") &
                            (ds["FLAG_CONCLUIDO_SUCESSO"] == "SIM")]
                for _, inst_row in inst_tec.iterrows():
                    gpon = inst_row["FSLOI_GPONAccess"]
                    fim_inst = inst_row["FIM_DT"]
                    if pd.isna(gpon) or pd.isna(fim_inst):
                        continue
                    limite = fim_inst + pd.Timedelta(days=30)
                    if any((rep_ds["FSLOI_GPONAccess"] == gpon) & (rep_ds["FIM_DT"] > fim_inst) & (rep_ds["FIM_DT"] <= limite)):
                        num_inf += 1
            den_inf = len(inst_tec)
        taxa_inf = round(num_inf / den_inf * 100, 1) if den_inf > 0 else 0.0
        
        nome = atv["NOME_TEC"].iloc[0] if len(atv) > 0 else ""
        
        c_prod = _cls_prod(media_diaria)
        c_efic = _cls_efic(efi)
        c_rep  = _cls_rep(taxa_rep)
        c_inf  = _cls_inf(taxa_inf)
        nota   = _nota_total(c_prod, c_efic, c_rep, c_inf)
        
        dados_tec.append({
            "TR": tr,
            "Nome": nome,
            "Prod. Média": media_diaria,
            "Eficácia (%)": efi,
            "Repetidos (%)": taxa_rep,
            "Infância (%)": taxa_inf,
            "Nota": nota,
            "Status": f"{c_prod[1]}{c_efic[1]}{c_rep[1]}{c_inf[1]}",
            "Status_Texto": f"{c_prod[0]} | {c_efic[0]} | {c_rep[0]} | {c_inf[0]}",
        })

    df_qual = pd.DataFrame(dados_tec).sort_values("Nota", ascending=False)
    
    media_equipe = {
        "Produtividade": round(df_qual["Prod. Média"].mean(), 1) if not df_qual.empty else 0,
        "Eficácia": round(df_qual["Eficácia (%)"].mean(), 1) if not df_qual.empty else 0,
        "Repetidos (%)": round(df_qual["Repetidos (%)"].mean(), 1) if not df_qual.empty else 0,
        "Infância (%)": round(df_qual["Infância (%)"].mean(), 1) if not df_qual.empty else 0,
    }
    
    cols = st.columns(4)
    for col, (metrica, valor, sub, cls) in zip(cols, [
        ("Prod. Média", f"{media_equipe['Produtividade']}", "atividades/dia", "kpi-blue"),
        ("Eficácia", f"{media_equipe['Eficácia']}%", "suc/total", "kpi-green" if media_equipe['Eficácia'] >= 85 else "kpi-yellow"),
        ("Repetidos", f"{media_equipe['Repetidos (%)']}%", "meta ≤ 9%", "kpi-green" if media_equipe['Repetidos (%)'] <= 9 else "kpi-red"),
        ("Infância", f"{media_equipe['Infância (%)']}%", "meta ≤ 5%", "kpi-green" if media_equipe['Infância (%)'] <= 5 else "kpi-red"),
    ]):
        col.markdown(_kpi(metrica, valor, sub, cls), unsafe_allow_html=True)
    st.write("")
    
    _sec("Ranking de Qualidade por Técnico")
    st.markdown("""
    <div style="font-size:11px;color:#64748b;margin-bottom:10px">
        <b>Critérios:</b> 🏆 Excelente (4pts) • 🟢 Bom (3pts) • 🟡 Atenção (2pts) • 🟠 Ruim (1pt) • 🔴 Crítico (0pts)<br>
        <b>Nota final:</b> soma dos pontos nos quatro pilares (máx. 16).<br>
        <b>Legenda cores:</b> <span style="color:#1e3a5f;font-weight:700">≥13</span> • <span style="color:#16a34a;font-weight:700">9-12</span> • <span style="color:#d97706;font-weight:700">5-8</span> • <span style="color:#dc2626;font-weight:700">&lt;5</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.dataframe(
        df_qual[["TR", "Nome", "Prod. Média", "Eficácia (%)", "Repetidos (%)", "Infância (%)", "Nota", "Status", "Status_Texto"]],
        column_config={
            "TR": st.column_config.TextColumn("TR", width="small"),
            "Nome": st.column_config.TextColumn("Nome", width="medium"),
            "Prod. Média": st.column_config.NumberColumn("Média/Dia", format="%.1f"),
            "Eficácia (%)": st.column_config.ProgressColumn("Eficácia", format="%.1f%%", min_value=0, max_value=100),
            "Repetidos (%)": st.column_config.ProgressColumn("Repetidos", format="%.1f%%", min_value=0, max_value=100),
            "Infância (%)": st.column_config.ProgressColumn("Infância", format="%.1f%%", min_value=0, max_value=100),
            "Nota": st.column_config.NumberColumn("Nota (0-16)", format="%d"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Status_Texto": st.column_config.TextColumn("Detalhe", width="medium"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    _sec("Distribuição da Nota de Qualidade")
    df_graf = df_qual.sort_values("Nota")
    cores = [_cor_nota(n) for n in df_graf["Nota"]]
    fig = go.Figure(go.Bar(
        x=df_graf["Nota"],
        y=df_graf["Nome"],
        orientation="h",
        marker_color=cores,
        text=df_graf["Nota"].astype(str),
        textposition="inside",
        textfont=dict(color="white", size=12)
    ))
    fig.update_layout(**_lyt("", 400))
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# 9. MAIN
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
