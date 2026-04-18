#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERTA — Painel Operacional do Supervisor v3.4
Telas: Diario | Producao Diaria | Repetidos | Infancia | Calendario | Qualidade
Tema: Branco / Azul Marinho
"""

import os
import re
import base64
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import calendar as _cal
import streamlit as st

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    layout="wide",
    page_title="BERTA - Painel Operacional",
    page_icon="📡",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CSS GLOBAL
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body { margin: 0; padding: 0; }
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="block-container"], .main, .block-container,
section.main > div, div[data-testid="stVerticalBlock"] {
    background-color: #f5f7fa !important;
    color: #1a2332 !important;
}

[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #dde3ed !important;
}
[data-testid="stSidebar"] * { color: #1a2332 !important; }

[data-baseweb="select"] > div, [data-baseweb="input"] > div {
    background-color: #ffffff !important;
    border-color: #dde3ed !important;
    color: #1a2332 !important;
}

[data-baseweb="tab-list"] {
    background-color: #ffffff !important;
    border-bottom: 2px solid #dde3ed !important;
}
[data-baseweb="tab"] {
    color: #64748b !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
}
[aria-selected="true"] {
    color: #1e3a5f !important;
    border-bottom: 2px solid #1e3a5f !important;
}

.stDataFrame, [data-testid="stDataFrameContainer"] {
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

.kpi-card {
    background: #ffffff;
    border: 1px solid #dde3ed;
    border-radius: 10px;
    padding: 16px 14px;
    text-align: center;
    position: relative;
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
    font-size: 10px; font-weight: 700; letter-spacing: 1.1px;
    text-transform: uppercase; color: #64748b; margin-bottom: 6px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 26px; font-weight: 700; color: #1a2332;
}
.kpi-blue { --accent: #1e3a5f; }
.kpi-green { --accent: #16a34a; }
.kpi-yellow { --accent: #d97706; }
.kpi-red { --accent: #dc2626; }
.kpi-purple { --accent: #7c3aed; }

.sec {
    font-size: 11px; font-weight: 700; letter-spacing: 1.4px;
    text-transform: uppercase; color: #1e3a5f;
    border-left: 3px solid #1e3a5f; padding-left: 10px;
    margin: 22px 0 10px 0;
}

.ph {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 0 18px 0; border-bottom: 1px solid #dde3ed;
    margin-bottom: 18px;
}
.ph h1 { font-size: 20px; font-weight: 700; color: #1a2332; margin: 0; }
.badge {
    background: #e8f0fa; border: 1px solid #bdd0ea; color: #1e3a5f;
    font-size: 10px; font-weight: 700; padding: 3px 10px;
    border-radius: 20px; text-transform: uppercase;
}

.banner-sup {
    background: #e8f0fa; border: 1px solid #bdd0ea; border-radius: 6px;
    padding: 8px 14px; margin-bottom: 16px; font-size: 12px; color: #1e3a5f;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTES E CONEXÃO SUPABASE
# =============================================================================
try:
    from chave import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bfamfgjjitrfcdyzuibd.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    if not SUPABASE_KEY:
        try:
            SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        except Exception:
            st.warning("SUPABASE_KEY não configurada.")
            SUPABASE_KEY = ""

SUPABASE_HDR = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
SUPABASE_STORAGE_URL = f"{SUPABASE_URL}/storage/v1/object/public/berta/BASEBOT.csv"

_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE_LOCAL = next((p for p in [
    os.path.join(_DIR, "BASEBOT.csv"),
    os.path.join(_DIR, "bases", "BASEBOT.csv"),
] if os.path.exists(p)), None)

C = {
    "bg": "#ffffff", "paper": "#ffffff", "grid": "#e8edf3", "txt": "#475569",
    "navy": "#1e3a5f", "navy2": "#2d5a8e", "navy3": "#4a7db5",
    "green": "#16a34a", "yellow": "#d97706", "red": "#dc2626", "purple": "#7c3aed",
}
_LYT = dict(
    paper_bgcolor=C["paper"], plot_bgcolor=C["bg"],
    font=dict(family="Inter, sans-serif", color=C["txt"], size=12),
    margin=dict(l=40, r=20, t=44, b=36),
    xaxis=dict(gridcolor=C["grid"], linecolor=C["grid"], zeroline=False),
    yaxis=dict(gridcolor=C["grid"], linecolor=C["grid"], zeroline=False),
)

# =============================================================================
# FUNÇÕES DE DADOS
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

def _extrair_tr_do_texto(texto):
    if pd.isna(texto) or not texto:
        return ""
    m = re.search(r"(TR|TT|TC)\d+", str(texto), re.I)
    return m.group(0).upper() if m else ""

def _processar_df(df):
    df.columns = df.columns.str.strip()
    df["FIM_DT"] = pd.to_datetime(df["Fim Execução"], dayfirst=True, errors="coerce")
    df["AB_DT"]  = pd.to_datetime(df["Data de criação"], dayfirst=True, errors="coerce")
    df["Estado"] = df["Estado"].str.strip().str.upper()
    df["Macro Atividade"] = df["Macro Atividade"].str.strip().str.upper()
    df["NOME_TEC"] = df["Técnico Atribuído"].apply(
        lambda v: str(v).split(" - ")[0].strip().title() if pd.notna(v) else "")
    df["DIA_FIM"] = df["FIM_DT"].dt.date
    df["MES_FIM"] = df["FIM_DT"].dt.to_period("M")
    df["SEM_FIM"] = df["FIM_DT"].dt.isocalendar().week.astype("Int64")
    df["ANO_FIM"] = df["FIM_DT"].dt.year.astype("Int64")
    df["DIA_AB"] = df["AB_DT"].dt.date
    df["MES_AB"] = df["AB_DT"].dt.to_period("M")
    df["SEM_AB"] = df["AB_DT"].dt.isocalendar().week.astype("Int64")

    vip_defaults = {
        "vip_flag_repetido": "NAO", "vip_flag_infancia": "NAO",
        "rep_tecnico_pai": "", "rep_agrupador_anterior": "", "rep_cod_fech_anterior": "",
        "inf_tecnico_pai": "", "rep_sa_anterior": ""
    }
    for col, val in vip_defaults.items():
        if col not in df.columns:
            df[col] = val
        else:
            df[col] = df[col].fillna(val)

    if "FLAG_CONCLUIDO_SUCESSO" not in df.columns:
        df["FLAG_CONCLUIDO_SUCESSO"] = (df["Estado"] == "CONCLUÍDO COM SUCESSO").map({True: "SIM", False: "NAO"})
    if "FLAG_CONCLUIDO_SEM_SUCESSO" not in df.columns:
        df["FLAG_CONCLUIDO_SEM_SUCESSO"] = (df["Estado"] == "CONCLUÍDO SEM SUCESSO").map({True: "SIM", False: "NAO"})
    if "CODIGO_TECNICO_EXTRAIDO" not in df.columns:
        df["CODIGO_TECNICO_EXTRAIDO"] = df["Técnico Atribuído"].apply(lambda v: _extrair_tr_do_texto(v))
    if "FLAG_REPARO_VALIDO" not in df.columns:
        df["FLAG_REPARO_VALIDO"] = ((df["Macro Atividade"] == "REP-FTTH") & (df["Estado"] == "CONCLUÍDO COM SUCESSO")).map({True: "SIM", False: "NAO"})
    if "FLAG_INSTALACAO_VALIDA" not in df.columns:
        df["FLAG_INSTALACAO_VALIDA"] = ((df["Macro Atividade"] == "INST-FTTH") & (df["Estado"] == "CONCLUÍDO COM SUCESSO")).map({True: "SIM", False: "NAO"})
    for f in ("FLAG_REPETIDO_ABERTO", "FLAG_P0_10_DIA", "FLAG_P0_15_DIA"):
        if f not in df.columns:
            df[f] = "NAO"
    if "FLAG_REPETIDO_30D" not in df.columns:
        df["FLAG_REPETIDO_30D"] = df["vip_flag_repetido"]
    if "FLAG_INFANCIA_30D" not in df.columns:
        df["FLAG_INFANCIA_30D"] = df["vip_flag_infancia"]
    if "ALARMADO" not in df.columns:
        df["ALARMADO"] = "NAO"
    else:
        df["ALARMADO"] = df["ALARMADO"].fillna("NAO")

    return df

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
    except Exception:
        pass
    if CAMINHO_BASE_LOCAL:
        try:
            df = pd.read_csv(CAMINHO_BASE_LOCAL, sep=";", encoding="utf-8-sig", dtype=str, low_memory=False)
            return _processar_df(df)
        except Exception as e:
            st.error(f"Erro local: {e}")
    return None

@st.cache_data(ttl=300)
def carregar_equipes():
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/tecnicos?select=tr,tt,tc,supervisor,funcionario", headers=SUPABASE_HDR, timeout=10)
        if r.status_code != 200:
            return {}
        eq = {}
        for row in r.json():
            sup = str(row.get("supervisor", "")).strip().title()
            if not sup or sup.upper() in ("", "NAN", "NONE"):
                continue
            cod = None
            for campo in ("tc", "tr", "tt"):
                v = str(row.get(campo, "")).strip().upper()
                if v and re.match(r"^(TR|TT|TC)\d+$", v, re.I):
                    cod = v
                    break
            if cod:
                eq.setdefault(sup, []).append(cod)
        return eq
    except Exception:
        return {}

# =============================================================================
# HELPERS DE UI
# =============================================================================
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

def _ev_dual(x, bars, line, bcolor, titulo, h=300, meta=None):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=x, y=bars, name="Qtd", marker_color=bcolor)
    fig.add_scatter(x=x, y=line, name="Taxa%", mode="lines+markers", line=dict(color=C["yellow"], width=2), secondary_y=True)
    if meta is not None:
        fig.add_hline(y=meta, line_dash="dash", line_color=C["red"], annotation_text=f"Meta {meta}%", secondary_y=True)
    fig.update_layout(**_lyt(titulo, h))
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return fig

# =============================================================================
# SIDEBAR
# =============================================================================
def sidebar(df):
    with st.sidebar:
        st.markdown('<div style="text-align:center;padding:18px 0 10px"><div style="font-size:22px;font-weight:800;color:#1e3a5f">📡 BERTA</div><div style="font-size:10px;color:#64748b">PAINEL OPERACIONAL</div></div>', unsafe_allow_html=True)
        st.divider()
        tela = st.radio("Tela", ["📅 Diario", "📊 Producao Diaria", "🔁 Repetidos", "👶 Infancia", "📆 Calendario", "🏆 Qualidade"], label_visibility="collapsed", key="nav")
        st.divider()
        st.markdown("**Filtros**")
        meses = sorted(df["MES_FIM"].dropna().astype(str).unique(), reverse=True)
        mes = st.selectbox("📅 Mes", meses, key="f_mes")
        eq = carregar_equipes()
        sups = sorted(eq.keys())
        if sups:
            sup = st.selectbox("👑 Supervisor", ["— Todos —"] + sups, key="f_sup")
            tecs_sup = eq.get(sup, []) if sup != "— Todos —" else []
        else:
            sup, tecs_sup = "— Todos —", []
        terrs = sorted(df["Território de serviço: Nome"].dropna().unique())
        terr = st.multiselect("📍 Territorio", terrs, key="f_terr")
        pool = [t for t in tecs_sup if t in df["CODIGO_TECNICO_EXTRAIDO"].values] if tecs_sup else sorted(df["CODIGO_TECNICO_EXTRAIDO"].dropna().unique())
        tec = st.multiselect("👤 Tecnico", pool, key="f_tec")
        st.divider()
        if st.button("🔄 Recarregar base", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    return {"tela": tela, "mes": mes, "supervisor": "" if sup == "— Todos —" else sup, "tecs_sup": tecs_sup, "territorios": terr, "tecnicos": tec}

def _filtrar(df, f):
    r = df[df["MES_FIM"].astype(str) == f["mes"]].copy()
    if f["tecs_sup"]: r = r[r["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecs_sup"])]
    if f["territorios"]: r = r[r["Território de serviço: Nome"].isin(f["territorios"])]
    if f["tecnicos"]: r = r[r["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecnicos"])]
    return r

def _escopo(df, f):
    if f["tecs_sup"]: return df[df["CODIGO_TECNICO_EXTRAIDO"].isin(f["tecs_sup"])].copy()
    return df

# =============================================================================
# TELA - PRODUÇÃO DIÁRIA (original mantida)
# =============================================================================
def tela_producao(dm, ds, f):
    _header("📊", "Producao Diaria", f)
    suc = dm[dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
    conc = dm[dm["Estado"].isin(["CONCLUÍDO COM SUCESSO", "CONCLUÍDO SEM SUCESSO"])]
    inst = suc[suc["Macro Atividade"] == "INST-FTTH"]
    rep = suc[suc["Macro Atividade"] == "REP-FTTH"]
    dias = suc["DIA_FIM"].nunique()
    efic = round(len(suc) / len(conc) * 100, 1) if len(conc) > 0 else 0
    med = round(len(suc) / dias, 1) if dias > 0 else 0

    cols = st.columns(6)
    for col, (lb, vl, sb, cl) in zip(cols, [
        ("Concluidos", f"{len(suc):,}", "c/ sucesso", "kpi-blue"),
        ("Eficacia", f"{efic}%", "suc / total", "kpi-green" if efic>=85 else "kpi-yellow"),
        ("Instalacoes", f"{len(inst):,}", "INST-FTTH", "kpi-blue"),
        ("Reparos", f"{len(rep):,}", "REP-FTTH", "kpi-purple"),
        ("Dias Trab.", f"{dias}", "c/ encerramento", "kpi-blue"),
        ("Media/Dia", f"{med}", "atividades/dia", "kpi-blue"),
    ]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")

    _sec("Producao por Dia")
    prod = suc.groupby("DIA_FIM").agg(
        Total=("Número SA", "count"),
        Inst=("Macro Atividade", lambda x: (x=="INST-FTTH").sum()),
        Rep=("Macro Atividade", lambda x: (x=="REP-FTTH").sum()),
    ).reset_index()
    ss = dm[dm["FLAG_CONCLUIDO_SEM_SUCESSO"]=="SIM"].groupby("DIA_FIM").size().reset_index(name="SS")
    prod = prod.merge(ss, on="DIA_FIM", how="left").fillna({"SS": 0})
    prod["SS"] = prod["SS"].astype(int)
    prod["Efic%"] = (prod["Total"]/(prod["Total"]+prod["SS"])*100).round(1)
    prod["Dia"] = pd.to_datetime(prod["DIA_FIM"]).dt.strftime("%d/%m")

    fig = go.Figure()
    fig.add_bar(x=prod["Dia"], y=prod["Inst"], name="INST", marker_color=C["navy"])
    fig.add_bar(x=prod["Dia"], y=prod["Rep"], name="REP", marker_color=C["purple"])
    fig.update_layout(barmode="stack", showlegend=True, **_lyt("Producao Diaria - INST + REP", 320))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        prod[["Dia","Total","Inst","Rep","SS","Efic%"]].rename(
            columns={"Inst":"INST","Rep":"REP","SS":"Sem Suc.","Efic%":"Eficacia%"}),
        use_container_width=True, hide_index=True,
        column_config={"Eficacia%": st.column_config.ProgressColumn("Eficacia%", format="%.1f%%", min_value=0, max_value=100)})

    _sec("Pareto de Tecnicos")
    pt = suc.groupby(["CODIGO_TECNICO_EXTRAIDO","NOME_TEC"]).size().reset_index(name="Prod")
    pt = pt.sort_values("Prod", ascending=False).reset_index(drop=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top 5 — Maior Producao**")
        t5 = pt.head(5)
        st.plotly_chart(_bar_h(t5["NOME_TEC"], t5["Prod"], C["green"], labels=t5["CODIGO_TECNICO_EXTRAIDO"], h=260), use_container_width=True)
    with c2:
        st.markdown("**Top 5 — Menor Producao**")
        b5 = pt.tail(5).sort_values("Prod")
        st.plotly_chart(_bar_h(b5["NOME_TEC"], b5["Prod"], C["yellow"], labels=b5["CODIGO_TECNICO_EXTRAIDO"], h=260), use_container_width=True)

    _sec("Ranking Completo")
    pt["#"] = range(1, len(pt)+1)
    st.dataframe(pt[["#","NOME_TEC","CODIGO_TECNICO_EXTRAIDO","Prod"]].rename(columns={"NOME_TEC":"Nome","CODIGO_TECNICO_EXTRAIDO":"TR","Prod":"Producao"}), use_container_width=True, hide_index=True,
                 column_config={"Producao": st.column_config.ProgressColumn("Producao", format="%d", min_value=0, max_value=int(pt["Prod"].max()))})

# =============================================================================
# TELA - REPETIDOS (original mantida)
# =============================================================================
def tela_repetidos(dm, ds, f):
    _header("🔁", "Repetidos", f)
    _usa_vip = "vip_flag_repetido" in ds.columns and (ds["vip_flag_repetido"] == "SIM").any()

    if _usa_vip:
        den_df = dm[(dm["Macro Atividade"] == "REP-FTTH") & (dm["Estado"] == "CONCLUÍDO COM SUCESSO")]
        den_total = len(den_df)
        rep_vip = dm[(dm["Macro Atividade"] == "REP-FTTH") & (dm["Estado"] == "CONCLUÍDO COM SUCESSO") & (dm["vip_flag_repetido"] == "SIM")]
        num_gpons = rep_vip["FSLOI_GPONAccess"].nunique()
        taxa = round(num_gpons / den_total * 100, 2) if den_total > 0 else 0
        fonte_label = "🏛️ Fonte: VIP Oficial"
    else:
        # fallback simplificado
        den_total = num_gpons = taxa = 0
        rep_vip = pd.DataFrame()
        fonte_label = "⚙️ Fonte: Cálculo Interno"

    rep_ab = ds[ds["FLAG_REPETIDO_ABERTO"] == "SIM"] if "FLAG_REPETIDO_ABERTO" in ds.columns else pd.DataFrame()
    cols = st.columns(5)
    for col, (lb,vl,sb,cl) in zip(cols,[
        ("Total Reparos", f"{den_total:,}", "abertos no mes", "kpi-blue"),
        ("Repetidos", f"{num_gpons:,}", "GPONs unicos", "kpi-red" if taxa>9 else "kpi-yellow"),
        ("Taxa %", f"{taxa}%", "meta: <= 9%", "kpi-red" if taxa>9 else "kpi-green"),
        ("Em Garantia", f"{len(rep_ab):,}", "abertos 30d", "kpi-yellow"),
        ("Alarmados", f"{rep_vip[rep_vip['ALARMADO']=='SIM']['FSLOI_GPONAccess'].nunique() if _usa_vip and 'ALARMADO' in rep_vip.columns else 0}", "GPON alarmado", "kpi-red"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:11px;color:#64748b;">{fonte_label}</div>', unsafe_allow_html=True)

    _sec("Indicador por Tecnico")
    rep_tec = dm[(dm["Macro Atividade"] == "REP-FTTH") & (dm["Estado"] == "CONCLUÍDO COM SUCESSO")]
    if not rep_tec.empty:
        tb = rep_tec.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
            Nome=("Técnico Atribuído", lambda x: str(x.iloc[0]).split(" - ")[0].strip().title()),
            Total=("Número SA", "count"),
            Repetidos=("vip_flag_repetido", lambda x: (x == "SIM").sum())
        ).reset_index()
        tb["Taxa%"] = (tb["Repetidos"]/tb["Total"]*100).round(2)
        tb = tb.sort_values("Taxa%", ascending=False)
        st.dataframe(tb.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"}), use_container_width=True, hide_index=True)

# =============================================================================
# TELA - INFÂNCIA (original mantida)
# =============================================================================
def tela_infancia(dm, ds, f):
    _header("👶", "Infancia", f)
    _usa_vip = "vip_flag_infancia" in dm.columns and (dm["vip_flag_infancia"] == "SIM").any()
    inst = dm[(dm["Macro Atividade"] == "INST-FTTH") & (dm["Estado"] == "CONCLUÍDO COM SUCESSO")]
    if _usa_vip:
        inf = inst[inst["vip_flag_infancia"] == "SIM"]
        fonte_label = "🏛️ Fonte: VIP Oficial"
    else:
        inf = inst[inst["FLAG_INFANCIA_30D"] == "SIM"] if "FLAG_INFANCIA_30D" in inst.columns else pd.DataFrame()
        fonte_label = "⚙️ Fonte: Cálculo Interno"
    taxa = round(len(inf)/len(inst)*100,2) if len(inst)>0 else 0

    cols = st.columns(5)
    for col,(lb,vl,sb,cl) in zip(cols,[
        ("Total Inst.", f"{len(inst):,}", "INST concluidas", "kpi-blue"),
        ("Infancia", f"{len(inf):,}", "reparo em 30d", "kpi-red" if taxa>5 else "kpi-yellow"),
        ("Taxa %", f"{taxa}%", "meta: <= 5%", "kpi-red" if taxa>5 else "kpi-green"),
        ("Inf. Aberta", f"{ds[(ds['Macro Atividade']=='REP-FTTH') & (ds['Estado'].isin(['ATRIBUÍDO','NÃO ATRIBUÍDO','RECEBIDO','EM EXECUÇÃO'])) & (ds['FSLOI_GPONAccess'].isin(inf['FSLOI_GPONAccess']))].shape[0]:,}", "reparo aberto", "kpi-yellow"),
        ("Alarmados", f"{inf[inf['ALARMADO']=='SIM'].shape[0] if 'ALARMADO' in inf.columns else 0}", "GPON alarmado", "kpi-red"),
    ]):
        col.markdown(_kpi(lb,vl,sb,cl), unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:11px;color:#64748b;">{fonte_label}</div>', unsafe_allow_html=True)

    _sec("Indicador por Tecnico")
    if not inst.empty:
        tb = inst.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
            Nome=("Técnico Atribuído", lambda x: str(x.iloc[0]).split(" - ")[0].strip().title()),
            Total=("Número SA", "count"),
            Infancia=("vip_flag_infancia" if _usa_vip else "FLAG_INFANCIA_30D", lambda x: (x == "SIM").sum())
        ).reset_index()
        tb["Taxa%"] = (tb["Infancia"]/tb["Total"]*100).round(2)
        tb = tb.sort_values("Taxa%", ascending=False)
        st.dataframe(tb.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"}), use_container_width=True, hide_index=True)

# =============================================================================
# TELA - CALENDÁRIO (cores atualizadas)
# =============================================================================
def tela_calendario(df, ds, f):
    _header("📆", "Calendario Mensal", f)
    mes_str = f["mes"]
    per = pd.Period(mes_str, freq="M")
    ano, mes = per.year, per.month
    hoje = datetime.now()
    dias_mes = _cal.monthrange(ano, mes)[1]
    dia_max = hoje.day if (ano == hoje.year and mes == hoje.month) else dias_mes
    dias_range = list(range(1, dia_max + 1))
    meses_pt = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    lbl_mes = f"{meses_pt[mes-1]}/{ano}"

    df_m = ds[(ds["FIM_DT"].dt.year==ano) & (ds["FIM_DT"].dt.month==mes)].copy()
    df_m["DIA"] = df_m["FIM_DT"].dt.day.astype(int)
    suc_m = df_m[df_m["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
    if suc_m.empty:
        st.warning("Sem dados de producao.")
        return

    tecs = suc_m["CODIGO_TECNICO_EXTRAIDO"].nunique()
    efic = round(len(suc_m)/(len(suc_m)+len(df_m[df_m["FLAG_CONCLUIDO_SEM_SUCESSO"]=="SIM"]))*100,1) if len(df_m)>0 else 0
    cols = st.columns(5)
    for col,(lb,vl,sb,cl) in zip(cols,[
        ("Tecnicos Ativos", f"{tecs}", lbl_mes, "kpi-blue"),
        ("Concluidos", f"{len(suc_m):,}", "c/ sucesso", "kpi-blue"),
        ("INST", f"{(suc_m['Macro Atividade']=='INST-FTTH').sum():,}", "", "kpi-blue"),
        ("REP", f"{(suc_m['Macro Atividade']=='REP-FTTH').sum():,}", "", "kpi-purple"),
        ("Eficacia", f"{efic}%", "suc/total", "kpi-green" if efic>=85 else "kpi-yellow"),
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
    nomes = suc_m.groupby("CODIGO_TECNICO_EXTRAIDO")["Técnico Atribuído"].first().apply(_n)
    pivot.insert(0, "Nome", nomes)
    pivot["Total"] = pivot[dias_range].sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=False).reset_index()
    pivot = pivot.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"})
    cols_dia = [str(d) for d in dias_range]
    cols_order = ["Nome","TR"] + dias_range + ["Total"]
    pivot = pivot[cols_order]
    pivot.columns = ["Nome","TR"] + cols_dia + ["Total"]

    def _cor_cel(v):
        try:
            v = int(v)
        except:
            return ""
        if v >= 8: return "background-color:#7c3aed;color:white;font-weight:700;text-align:center"
        if v in (6,7): return "background-color:#000000;color:white;font-weight:700;text-align:center"
        if v == 5: return "background-color:#1e40af;color:white;font-weight:700;text-align:center"
        if v == 4: return "background-color:#d4edda;color:#155724;font-weight:600;text-align:center"
        if v == 3: return "background-color:#fff3cd;color:#856404;font-weight:600;text-align:center"
        if v in (1,2): return "background-color:#ffcccc;color:#721c24;text-align:center"
        return "background-color:#f0f0f0;color:#adb5bd;text-align:center"

    styled = pivot.style.map(_cor_cel, subset=cols_dia)
    st.dataframe(styled, use_container_width=True, hide_index=True, height=38 + len(pivot)*35)

# =============================================================================
# TELA - QUALIDADE (original mantida)
# =============================================================================
def tela_qualidade(dm, ds, f):
    _header("🏆", "Qualidade", f)
    st.info("Tela de Qualidade em desenvolvimento.")

# =============================================================================
# TELA - DIÁRIO (COM PAI ROBUSTO E NOVA SEÇÃO)
# =============================================================================
def tela_diario(df, ds, f):
    _header("📅", "Controle do Dia", f)

    datas_disp = sorted(ds["FIM_DT"].dropna().dt.date.unique(), reverse=True)
    if not datas_disp:
        st.warning("Nenhuma data disponivel.")
        return

    c_pick, c_info = st.columns([2, 5])
    with c_pick:
        dia_sel = st.date_input("Data de referencia", value=datas_disp[0],
                                min_value=datas_disp[-1], max_value=datas_disp[0], key="dia_ref")

    dm = ds[ds["FIM_DT"].dt.date == dia_sel].copy()
    dm_ab = ds[ds["AB_DT"].dt.date == dia_sel].copy()

    suc = dm[dm["FLAG_CONCLUIDO_SUCESSO"] == "SIM"]
    sem_suc = dm[dm["FLAG_CONCLUIDO_SEM_SUCESSO"] == "SIM"]
    inst_d = suc[suc["Macro Atividade"] == "INST-FTTH"]
    rep_d = suc[suc["Macro Atividade"] == "REP-FTTH"]
    tecs_atv = suc["CODIGO_TECNICO_EXTRAIDO"].nunique()
    efic = round(len(suc)/(len(suc)+len(sem_suc))*100,1) if (len(suc)+len(sem_suc)) > 0 else 0

    with c_info:
        st.markdown(f"<div style='margin-top:28px;font-size:12px;color:#64748b;'><b>{dia_sel.strftime('%d/%m/%Y')}</b> — {tecs_atv} tecnicos ativos | {len(suc)+len(sem_suc)} atividades concluidas</div>", unsafe_allow_html=True)

    rep_dia_ab = dm_ab[dm_ab["FLAG_REPETIDO_30D"] == "SIM"].copy()
    rep_ab_tot = ds[ds["FLAG_REPETIDO_ABERTO"] == "SIM"].copy()
    inf_dia = suc[suc["FLAG_INFANCIA_30D"] == "SIM"].copy()
    p0_10 = ds[(ds["FIM_DT"].dt.date == dia_sel) & (ds["FLAG_P0_10_DIA"] == "SIM")]
    p0_15 = ds[(ds["FIM_DT"].dt.date == dia_sel) & (ds["FLAG_P0_15_DIA"] == "SIM")]

    cols = st.columns(7)
    for col, (lb, vl, sb, cl) in zip(cols, [
        ("Concluidos", f"{len(suc):,}", f"INST:{len(inst_d)} REP:{len(rep_d)}", "kpi-blue"),
        ("Eficacia", f"{efic}%", "suc/total", "kpi-green" if efic>=85 else "kpi-yellow"),
        ("Sem Sucesso", f"{len(sem_suc):,}", "pendencias", "kpi-red" if len(sem_suc)>0 else "kpi-green"),
        ("Rep. Dia", f"{len(rep_dia_ab):,}", "abertos hoje", "kpi-red" if len(rep_dia_ab)>0 else "kpi-green"),
        ("Rep. Abertos", f"{len(rep_ab_tot):,}", "em garantia", "kpi-yellow" if len(rep_ab_tot)>0 else "kpi-green"),
        ("P0 10h", f"{p0_10['CODIGO_TECNICO_EXTRAIDO'].nunique()}", "tecnicos", "kpi-red" if not p0_10.empty else "kpi-green"),
        ("P0 15h", f"{p0_15['CODIGO_TECNICO_EXTRAIDO'].nunique()}", "tecnicos", "kpi-red" if not p0_15.empty else "kpi-green"),
    ]):
        col.markdown(_kpi(lb, vl, sb, cl), unsafe_allow_html=True)
    st.write("")

    def _extrair_tr(texto):
        if pd.isna(texto) or not texto:
            return ""
        m = re.search(r"(TR|TT|TC)\d+", str(texto), re.I)
        return m.group(0).upper() if m else ""

    def _get_pai_rep(row, df_full):
        nome, tr = "", ""
        val = str(row.get("rep_tecnico_pai", "")).strip()
        if val and val.lower() != "nan":
            nome = val
            tr = _extrair_tr(val)
        if not nome:
            val = str(row.get("rep_agrupador_anterior", "")).strip()
            if val and val.lower() != "nan":
                nome = val
                tr = _extrair_tr(val) or tr
        if not tr:
            val = str(row.get("rep_cod_fech_anterior", "")).strip()
            if val and val.lower() != "nan":
                tr = _extrair_tr(val) or val.upper()
                if not nome:
                    nome = tr
        if df_full is not None and (not nome or not tr):
            for col in ["rep_sa_anterior", "SA_ANTERIOR", "sa_anterior"]:
                if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                    sa_ant = str(row[col]).strip()
                    reg = df_full[df_full["Número SA"].astype(str).str.strip() == sa_ant]
                    if not reg.empty:
                        if not nome:
                            nome = reg.iloc[0].get("NOME_TEC", "")
                        if not tr:
                            tr = reg.iloc[0].get("CODIGO_TECNICO_EXTRAIDO", "")
                    break
        return nome, tr

    def _get_pai_inf(row, df_full):
        nome, tr = "", ""
        val = str(row.get("inf_tecnico_pai", "")).strip()
        if val and val.lower() != "nan":
            nome = val
            tr = _extrair_tr(val)
        if df_full is not None and (not nome or not tr):
            for col in ["inf_sa_anterior", "SA_INST_ANTERIOR"]:
                if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                    sa_ant = str(row[col]).strip()
                    reg = df_full[df_full["Número SA"].astype(str).str.strip() == sa_ant]
                    if not reg.empty:
                        if not nome:
                            nome = reg.iloc[0].get("NOME_TEC", "")
                        if not tr:
                            tr = reg.iloc[0].get("CODIGO_TECNICO_EXTRAIDO", "")
                    break
        return nome, tr

    def _n(v): return str(v).split(" - ")[0].strip().title() if pd.notna(v) else ""

    # Produtividade
    _sec("Produtividade por Tecnico")
    if not suc.empty:
        pt = suc.groupby("CODIGO_TECNICO_EXTRAIDO").agg(
            Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])),
            Total=("Número SA", "count"),
            INST=("Macro Atividade", lambda x: (x=="INST-FTTH").sum()),
            REP=("Macro Atividade", lambda x: (x=="REP-FTTH").sum())
        ).reset_index()
        ss_tec = sem_suc.groupby("CODIGO_TECNICO_EXTRAIDO").size().reset_index(name="SemSuc")
        pt = pt.merge(ss_tec, on="CODIGO_TECNICO_EXTRAIDO", how="left").fillna(0)
        pt["Efic%"] = (pt["Total"]/(pt["Total"]+pt["SemSuc"]).replace(0,1)*100).round(1)
        pt = pt.sort_values("Total", ascending=False)
        st.dataframe(pt.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"}), use_container_width=True, hide_index=True,
                     column_config={"Total": st.column_config.ProgressColumn("Total", format="%d", min_value=0, max_value=int(pt["Total"].max()) if not pt.empty else 1)})

    # Sem sucesso
    _sec("Sem Sucesso — Pendencias do Dia")
    if sem_suc.empty:
        st.success("Nenhuma pendencia no dia.")
    else:
        ok = [c for c in ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","Macro Atividade","Descrição","Observação","Código de encerramento"] if c in sem_suc.columns]
        st.dataframe(sem_suc[ok].rename(columns={"Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico","Macro Atividade":"Tipo","Código de encerramento":"Cod. Enc."}), use_container_width=True, hide_index=True)

    # Repetidos Abertos no Dia
    c1, c2 = st.columns(2)
    with c1:
        _sec("Repetidos Abertos no Dia")
        if rep_dia_ab.empty:
            st.success("Nenhum repetido aberto hoje.")
        else:
            pais = rep_dia_ab.apply(lambda r: _get_pai_rep(r, ds), axis=1)
            rep_dia_ab["Tecnico_PAI"] = [p[0] for p in pais]
            rep_dia_ab["TR_PAI"] = [p[1] for p in pais]
            cols = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess"]
            if "ALARMADO" in rep_dia_ab.columns: cols.append("ALARMADO")
            cols.extend(["Tecnico_PAI","TR_PAI"])
            df_show = rep_dia_ab[cols].rename(columns={
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
                "FSLOI_GPONAccess":"GPON","Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)

    with c2:
        _sec("Repetidos em Garantia (Abertos)")
        if rep_ab_tot.empty:
            st.success("Nenhum reparo em garantia.")
        else:
            pais = rep_ab_tot.apply(lambda r: _get_pai_rep(r, ds), axis=1)
            rep_ab_tot["Tecnico_PAI"] = [p[0] for p in pais]
            rep_ab_tot["TR_PAI"] = [p[1] for p in pais]
            cols = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","DIA_AB"]
            if "ALARMADO" in rep_ab_tot.columns: cols.append("ALARMADO")
            cols.extend(["Tecnico_PAI","TR_PAI"])
            df_show = rep_ab_tot[cols].rename(columns={
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
                "FSLOI_GPONAccess":"GPON","DIA_AB":"Abertura",
                "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)

    # Infância
    c3, c4 = st.columns(2)
    with c3:
        _sec("Infancia — Instalacoes do Dia")
        if inf_dia.empty:
            st.success("Nenhuma infancia hoje.")
        else:
            pais = inf_dia.apply(lambda r: _get_pai_inf(r, ds), axis=1)
            inf_dia["Tecnico_PAI"] = [p[0] for p in pais]
            inf_dia["TR_PAI"] = [p[1] for p in pais]
            cols = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess"]
            if "SA_REPARO_INFANCIA" in inf_dia.columns: cols.append("SA_REPARO_INFANCIA")
            cols.extend(["Tecnico_PAI","TR_PAI"])
            df_show = inf_dia[cols].rename(columns={
                "Número SA":"SA Inst.","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
                "FSLOI_GPONAccess":"GPON","SA_REPARO_INFANCIA":"SA Reparo",
                "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)

    with c4:
        _sec("Infancia Aberta (Reparo em Andamento)")
        estados_ab = ["ATRIBUÍDO","NÃO ATRIBUÍDO","RECEBIDO","EM EXECUÇÃO","EM DESLOCAMENTO"]
        gpons_suc = set(suc["FSLOI_GPONAccess"].dropna().str.upper())
        inf_ab_dia = ds[(ds["Macro Atividade"] == "REP-FTTH") & (ds["Estado"].isin(estados_ab)) &
                        (ds["FLAG_INFANCIA_30D"] == "SIM") & (ds["FSLOI_GPONAccess"].str.upper().isin(gpons_suc))].copy()
        if inf_ab_dia.empty:
            st.success("Nenhuma infancia aberta.")
        else:
            pais = inf_ab_dia.apply(lambda r: _get_pai_inf(r, ds), axis=1)
            inf_ab_dia["Tecnico_PAI"] = [p[0] for p in pais]
            inf_ab_dia["TR_PAI"] = [p[1] for p in pais]
            cols = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","Estado"]
            cols.extend(["Tecnico_PAI","TR_PAI"])
            df_show = inf_ab_dia[cols].rename(columns={
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
                "FSLOI_GPONAccess":"GPON",
                "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)

    # Em Garantia Alarmado
    _sec("Em Garantia Alarmado (Repetido e Infância)")
    rep_alarm = rep_ab_tot[rep_ab_tot["ALARMADO"] == "SIM"] if not rep_ab_tot.empty and "ALARMADO" in rep_ab_tot.columns else pd.DataFrame()
    inf_alarm = inf_ab_dia[inf_ab_dia["ALARMADO"] == "SIM"] if not inf_ab_dia.empty and "ALARMADO" in inf_ab_dia.columns else pd.DataFrame()

    if rep_alarm.empty and inf_alarm.empty:
        st.success("Nenhum registro em garantia alarmado.")
    else:
        tab_rep, tab_inf = st.tabs(["🔁 Repetidos Alarmados", "👶 Infância Alarmada"])
        with tab_rep:
            if rep_alarm.empty:
                st.info("Nenhum repetido alarmado.")
            else:
                pais = rep_alarm.apply(lambda r: _get_pai_rep(r, ds), axis=1)
                rep_alarm["Tecnico_PAI"] = [p[0] for p in pais]
                rep_alarm["TR_PAI"] = [p[1] for p in pais]
                cols = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","DIA_AB"]
                if "Alarm ID" in rep_alarm.columns: cols.append("Alarm ID")
                cols.extend(["Tecnico_PAI","TR_PAI"])
                df_show = rep_alarm[cols].rename(columns={
                    "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
                    "FSLOI_GPONAccess":"GPON","DIA_AB":"Abertura","Alarm ID":"Alarme",
                    "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
                })
                st.dataframe(df_show, use_container_width=True, hide_index=True)
        with tab_inf:
            if inf_alarm.empty:
                st.info("Nenhuma infância alarmada.")
            else:
                pais = inf_alarm.apply(lambda r: _get_pai_inf(r, ds), axis=1)
                inf_alarm["Tecnico_PAI"] = [p[0] for p in pais]
                inf_alarm["TR_PAI"] = [p[1] for p in pais]
                cols = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","Estado"]
                if "Alarm ID" in inf_alarm.columns: cols.append("Alarm ID")
                cols.extend(["Tecnico_PAI","TR_PAI"])
                df_show = inf_alarm[cols].rename(columns={
                    "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR","NOME_TEC":"Tecnico",
                    "FSLOI_GPONAccess":"GPON","Alarm ID":"Alarme",
                    "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
                })
                st.dataframe(df_show, use_container_width=True, hide_index=True)

    # P0
    _sec("P0 — Controle de Encerramento")
    cp1, cp2 = st.columns(2)
    with cp1:
        st.markdown("**P0 10h — Nao encerraram ate as 10h**")
        if p0_10.empty: st.success("Todos encerraram ate 10h.")
        else:
            t10 = p0_10.groupby("CODIGO_TECNICO_EXTRAIDO").agg(Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])), Qtd=("Número SA","count")).reset_index()
            st.dataframe(t10.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"}), use_container_width=True, hide_index=True)
    with cp2:
        st.markdown("**P0 15h — Nao encerraram ate as 15h**")
        if p0_15.empty: st.success("Todos encerraram ate 15h.")
        else:
            t15 = p0_15.groupby("CODIGO_TECNICO_EXTRAIDO").agg(Nome=("Técnico Atribuído", lambda x: _n(x.iloc[0])), Qtd=("Número SA","count")).reset_index()
            st.dataframe(t15.rename(columns={"CODIGO_TECNICO_EXTRAIDO":"TR"}), use_container_width=True, hide_index=True)

# =============================================================================
# MAIN
# =============================================================================
def main():
    df = carregar_base()
    if df is None:
        st.error("Não foi possível carregar a base.")
        return

    f = sidebar(df)
    tela = f["tela"]
    dm = _filtrar(df, f)
    ds = _escopo(df, f)

    if f["supervisor"]:
        ult_att = ultima_atualizacao_base()
        att_str = f" | 🕐 Base atualizada: {ult_att}" if ult_att else ""
        st.markdown(f'<div class="banner-sup">👑 Equipe de <strong>{f["supervisor"]}</strong> — {len(f["tecs_sup"])} tecnico(s) | {f["mes"]}{att_str}</div>', unsafe_allow_html=True)

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
