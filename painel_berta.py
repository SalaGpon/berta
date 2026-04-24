#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERTA — Painel Operacional do Supervisor v3.2 (W)
Telas: Producao Diaria | Repetidos | Infancia | Calendario | Qualidade | Diario
Fonte de dados: GitHub API → upload manual → arquivo local
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
# 2. CSS GLOBAL (mantido igual)
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
# 4. CARREGAMENTO DO DATAFRAME (SEM WIDGETS INTERNOS)
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def carregar_base_github():
    """
    Tenta carregar o BASEBOT.csv usando a API do GitHub.
    Retorna um DataFrame ou None.
    """
    try:
        token = st.secrets.get("GITHUB_TOKEN", "")
        if not token:
            st.warning("🔑 Token GITHUB_TOKEN não configurado nas secrets. Pulando GitHub...")
            return None

        headers = {"Authorization": f"token {token}"}
        meta_url = "https://api.github.com/repos/SalaGpon/Berta-bot/contents/BASEBOT.csv"
        meta = requests.get(meta_url, headers=headers, timeout=30)
        if meta.status_code != 200:
            st.warning(f"GitHub Meta: HTTP {meta.status_code}")
            return None

        sha = meta.json().get("sha")
        blob_url = f"https://api.github.com/repos/SalaGpon/Berta-bot/git/blobs/{sha}"
        blob_resp = requests.get(blob_url, headers=headers, timeout=60)
        if blob_resp.status_code != 200:
            st.warning(f"GitHub Blob: HTTP {blob_resp.status_code}")
            return None

        b64_content = blob_resp.json().get("content")
        if not b64_content:
            st.warning("GitHub: conteúdo vazio.")
            return None

        texto = base64.b64decode(b64_content).decode("utf-8-sig", errors="replace")
        df = pd.read_csv(io.StringIO(texto), sep=";", dtype=str, low_memory=False)
        if len(df) == 0:
            st.warning("GitHub: arquivo vazio.")
            return None

        st.success("✅ Base carregada do GitHub (API)")
        return df
    except Exception as e:
        st.warning(f"Erro ao carregar do GitHub: {e}")
        return None


@st.cache_data(ttl=300)
def carregar_base_local():
    """Tenta carregar via arquivo local (apenas para desenvolvimento)."""
    if not CAMINHO_BASE_LOCAL:
        return None
    try:
        df = pd.read_csv(CAMINHO_BASE_LOCAL, sep=";", encoding="utf-8-sig", dtype=str, low_memory=False)
        st.success("✅ Base carregada do arquivo local")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo local: {e}")
        return None


def carregar_base():
    """
    Orquestra o carregamento do BASEBOT.csv:
    1. GitHub API
    2. Arquivo local (fallback)
    Retorna um DataFrame processado ou None.
    """
    df = carregar_base_github()
    if df is None:
        df = carregar_base_local()
    if df is not None:
        return _processar_df(df)
    return None


def _processar_df(df):
    """Normaliza e cria colunas derivadas."""
    # Remove espaços extras dos nomes das colunas
    df.columns = df.columns.str.strip()

    # Mapeamento flexível para a coluna de data de fim
    colunas_fim = ["Fim Execução", "FIM_EXECUCAO", "Fim Execucao", "FIM EXECUÇÃO", "FIM EXECUCAO"]
    col_fim = None
    for c in colunas_fim:
        if c in df.columns:
            col_fim = c
            break
    if col_fim is None:
        raise KeyError(
            f"Coluna de fim de execução não encontrada. "
            f"Colunas disponíveis: {list(df.columns)}. "
            f"Verifique se o arquivo BASEBOT.csv está atualizado."
        )

    # Mapeamento para data de criação
    colunas_ab = ["Data de criação", "DATA_DE_CRIACAO", "Data de Criacao"]
    col_ab = None
    for c in colunas_ab:
        if c in df.columns:
            col_ab = c
            break
    if col_ab is None:
        raise KeyError(
            f"Coluna de data de criação não encontrada. "
            f"Colunas disponíveis: {list(df.columns)}."
        )

    df["FIM_DT"] = pd.to_datetime(df[col_fim], dayfirst=True, errors="coerce")
    df["AB_DT"]  = pd.to_datetime(df[col_ab],  dayfirst=True, errors="coerce")
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

    # (resto das colunas VIP, flags etc. – mantido igual ao código anterior)
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
    }
    for col, default in _vip_defaults.items():
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)

    if "FLAG_CONCLUIDO_SUCESSO" not in df.columns:
        df["FLAG_CONCLUIDO_SUCESSO"] = (
            df["Estado"].str.upper() == "CONCLUÍDO COM SUCESSO"
        ).map({True: "SIM", False: "NAO"})
    if "FLAG_CONCLUIDO_SEM_SUCESSO" not in df.columns:
        df["FLAG_CONCLUIDO_SEM_SUCESSO"] = (
            df["Estado"].str.upper() == "CONCLUÍDO SEM SUCESSO"
        ).map({True: "SIM", False: "NAO"})
    if "CODIGO_TECNICO_EXTRAIDO" not in df.columns:
        df["CODIGO_TECNICO_EXTRAIDO"] = df["Técnico Atribuído"].apply(
            lambda v: (lambda m: m.group(0).upper() if m else "")(
                re.search(r"(TR|TT|TC)\d+", str(v), re.I)))
    if "FLAG_REPARO_VALIDO" not in df.columns:
        df["FLAG_REPARO_VALIDO"] = (
            (df["Macro Atividade"].str.upper() == "REP-FTTH") &
            (df["Estado"].str.upper() == "CONCLUÍDO COM SUCESSO")
        ).map({True: "SIM", False: "NAO"})
    if "FLAG_INSTALACAO_VALIDA" not in df.columns:
        df["FLAG_INSTALACAO_VALIDA"] = (
            (df["Macro Atividade"].str.upper() == "INST-FTTH") &
            (df["Estado"].str.upper() == "CONCLUÍDO COM SUCESSO")
        ).map({True: "SIM", False: "NAO"})
    for _f in ("FLAG_REPETIDO_ABERTO", "FLAG_P0_10_DIA", "FLAG_P0_15_DIA"):
        if _f not in df.columns:
            df[_f] = "NAO"
    if "FLAG_REPETIDO_30D" not in df.columns:
        df["FLAG_REPETIDO_30D"] = df["vip_flag_repetido"]
    if "FLAG_INFANCIA_30D" not in df.columns:
        df["FLAG_INFANCIA_30D"] = df["vip_flag_infancia"]
    if "ALARMADO" not in df.columns:
        df["ALARMADO"] = "NAO"
    else:
        df["ALARMADO"] = df["ALARMADO"].fillna("NAO")
    if "CDOE" not in df.columns:
        df["CDOE"] = ""
    else:
        df["CDOE"] = df["CDOE"].fillna("")

    if "Logradouro" in df.columns and "Logradouro_cli" in df.columns:
        mask = df["Logradouro"].astype(str).str.strip().isin(["", "nan"])
        df.loc[mask, "Logradouro"] = df.loc[mask, "Logradouro_cli"]
    elif "Logradouro_cli" in df.columns:
        df["Logradouro"] = df["Logradouro_cli"]

    for col in ("TEC_ANTERIOR", "IF_DIAS", "FLAG_REPETIDO", "FLAG_INFANCIA"):
        if col not in df.columns:
            df[col] = ""

    return df


# (funções extrair_codigo_tecnico, carregar_equipes, helpers, etc. mantidas)

def extrair_codigo_tecnico(tecnico_str) -> str:
    try:
        m = re.search(r'(TR\d+|TT\d+|TC\d+)', str(tecnico_str).strip())
        return m.group(1).upper() if m else ""
    except:
        return ""


@st.cache_data(ttl=600)
def carregar_equipes(df=None):
    """Obtém as equipes (Supervisor -> [TRs]) do BASEBOT.csv ou da planilha de presença."""
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


# (todas as funções de tela permanecem inalteradas, exceto que agora usam o df carregado corretamente)

# =============================================================================
# 5. SIDEBAR – inclui upload manual e filtros
# =============================================================================

def sidebar(df):
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:18px 0 10px">'
            '<div style="font-size:22px;font-weight:800;color:#1e3a5f;letter-spacing:2px">📡 BERTA</div>'
            '<div style="font-size:10px;color:#64748b;font-weight:600;letter-spacing:1px;margin-top:3px">PAINEL OPERACIONAL</div>'
            '</div>', unsafe_allow_html=True)
        st.divider()

        # Upload manual (fora de qualquer cache)
        uploaded_file = st.file_uploader(
            "📂 Enviar BASEBOT.csv manualmente",
            type=["csv"],
            key="upload_manual",
            help="Carregue o arquivo se o GitHub não estiver disponível."
        )
        if uploaded_file is not None:
            try:
                _df = pd.read_csv(uploaded_file, sep=";", dtype=str, low_memory=False)
                if len(_df) > 0:
                    st.session_state["df_manual"] = _df
                    st.success("📂 Arquivo carregado manualmente")
                else:
                    st.warning("Arquivo enviado está vazio.")
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")

        st.divider()

        tela = st.radio("Tela",
            ["📅 Diario", "📊 Producao Diaria", "🔁 Repetidos", "👶 Infancia", "📆 Calendario", "🏆 Qualidade"],
            label_visibility="collapsed", key="nav")
        st.divider()

        st.markdown("**Filtros**")
        # O restante da filtragem usa o df (ou o df_manual, se definido)
        df_atual = df  # será o df principal, mas podemos utilizar o manual se disponível
        if "df_manual" in st.session_state:
            df_atual = st.session_state["df_manual"]

        meses = sorted(df_atual["MES_FIM"].dropna().astype(str).unique(), reverse=True)
        mes   = st.selectbox("📅 Mes", meses, key="f_mes")

        eq = carregar_equipes(df_atual)  # passa o df atual
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
            # Limpa também o manual para forçar novo download
            if "df_manual" in st.session_state:
                del st.session_state["df_manual"]
            st.rerun()

    return {
        "tela": tela, "mes": mes,
        "supervisor": "" if sup == "— Todos —" else sup,
        "tecs_sup": tecs_sup,
        "territorios": terr,
        "tecnicos": tec,
    }


# =============================================================================
# 6. MAIN – unifica a lógica de carregamento
# =============================================================================

def main():
    # Verifica se há upload manual na sessão
    if "df_manual" in st.session_state:
        df = _processar_df(st.session_state["df_manual"])
        st.success("Usando arquivo carregado manualmente.")
    else:
        df = carregar_base()

    if df is None:
        st.error("❌ Nenhuma fonte de dados disponível.")
        st.info(
            "Configure a secret `GITHUB_TOKEN` ou faça upload manual do arquivo BASEBOT.csv."
        )
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

    # (chamada das telas – igual ao código original)
    if tela == "📅 Diario":
        tela_diario(df, ds, f)
    # ... restante igual ...


if __name__ == "__main__":
    main()
