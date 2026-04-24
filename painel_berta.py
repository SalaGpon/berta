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
    _cores = ["#1e3a5f",   "#15803d","#16a34a", "#d97706", "#dc2626",           "#94a3b8"]
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

    # ── Geração de Atas inline ──
    _sec("Gerar Atas de Qualidade — Assinatura Digital")
    st.caption("Clique em 📄 ATA para abrir o formulário de assinatura logo abaixo.")

    _h1, _h2, _h3, _h4, _h5, _h6, _h7 = st.columns([3, 1, 1, 1, 1, 1, 1])
    for col, txt in zip(
        [_h1, _h2, _h3, _h4, _h5, _h6, _h7],
        ["**Tecnico**", "**Prod.**", "**Efic.**", "**Repet.**", "**Inf.**", "**Nota**", ""],
    ):
        col.markdown(txt)

    sup_nome = f.get("supervisor", "N/I") or "N/I"

    # Inicializa a ata selecionada no estado
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
                st.rerun()  # força a atualização para exibir o componente imediatamente

    # Exibe a ata logo abaixo, se houver uma ativa
    if st.session_state.ata_html:
        st.markdown(f"**📝 Assinatura de {st.session_state.ata_nome}**")
        st.components.v1.html(st.session_state.ata_html, height=900, scrolling=True)
        if st.button("❌ Fechar ATA"):
            st.session_state.ata_html = None
            st.session_state.ata_nome = ""
            st.rerun()
