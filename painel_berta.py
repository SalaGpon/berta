def tela_diario(df, ds, f):
    _header("📅", "Controle do Dia", f)

    # Seletor de data — usa a data mais recente da base como padrao
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

    # KPIs
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

    # Função auxiliar para extrair TR do nome (formato "Nome - TRxxxx")
    def _extrair_tr(nome):
        if pd.isna(nome) or not nome:
            return ""
        import re
        m = re.search(r"(TR|TT|TC)\d+", str(nome), re.I)
        return m.group(0).upper() if m else ""

    # Função para obter nome do técnico PAI e TR_PAI para repetidos (fallback robusto)
    def _get_pai_rep(row):
        pai_nome = ""
        pai_tr = ""
        # Prioridade: rep_tecnico_pai
        if "rep_tecnico_pai" in row.index and pd.notna(row["rep_tecnico_pai"]) and str(row["rep_tecnico_pai"]).strip():
            pai_nome = str(row["rep_tecnico_pai"]).strip()
            pai_tr = _extrair_tr(pai_nome)
        # Fallback: rep_agrupador_anterior (pode conter nome ou código)
        elif "rep_agrupador_anterior" in row.index and pd.notna(row["rep_agrupador_anterior"]) and str(row["rep_agrupador_anterior"]).strip():
            val = str(row["rep_agrupador_anterior"]).strip()
            tr = _extrair_tr(val)
            if tr:
                pai_tr = tr
                pai_nome = val
            else:
                pai_nome = val
        # Fallback: rep_cod_fech_anterior (código do técnico)
        if not pai_tr and "rep_cod_fech_anterior" in row.index and pd.notna(row["rep_cod_fech_anterior"]) and str(row["rep_cod_fech_anterior"]).strip():
            cod = str(row["rep_cod_fech_anterior"]).strip().upper()
            if re.match(r"(TR|TT|TC)\d+", cod, re.I):
                pai_tr = cod
                if not pai_nome:
                    pai_nome = cod
        return pai_nome, pai_tr

    # Função para obter nome do técnico PAI e TR_PAI para infância
    def _get_pai_inf(row):
        pai_nome = ""
        pai_tr = ""
        if "inf_tecnico_pai" in row.index and pd.notna(row["inf_tecnico_pai"]) and str(row["inf_tecnico_pai"]).strip():
            pai_nome = str(row["inf_tecnico_pai"]).strip()
            pai_tr = _extrair_tr(pai_nome)
        return pai_nome, pai_tr

    # Produtividade por tecnico
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

    # Sem sucesso / pendencias
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

    # Repetidos
    c1, c2 = st.columns(2)
    with c1:
        _sec("Repetidos Abertos no Dia")
        if rep_dia_ab.empty:
            st.success("Nenhum repetido aberto hoje.")
        else:
            df_ab = rep_dia_ab.copy()
            # Adiciona colunas de PAI usando função robusta
            pais = df_ab.apply(_get_pai_rep, axis=1)
            df_ab["Tecnico_PAI"] = [p[0] for p in pais]
            df_ab["TR_PAI"] = [p[1] for p in pais]

            cols_show = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess"]
            if "ALARMADO" in df_ab.columns:
                cols_show.append("ALARMADO")
            # Sempre adicionar as colunas PAI que criamos
            cols_show.extend(["Tecnico_PAI","TR_PAI"])

            df_show = df_ab[cols_show].copy()
            rename_map = {
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON",
                "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            }
            st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

    with c2:
        _sec("Repetidos em Garantia (Abertos)")
        if rep_ab_tot.empty:
            st.success("Nenhum reparo em garantia.")
        else:
            df_ab_tot = rep_ab_tot.copy()
            pais = df_ab_tot.apply(_get_pai_rep, axis=1)
            df_ab_tot["Tecnico_PAI"] = [p[0] for p in pais]
            df_ab_tot["TR_PAI"] = [p[1] for p in pais]

            cols_show = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","DIA_AB"]
            if "ALARMADO" in df_ab_tot.columns:
                cols_show.append("ALARMADO")
            cols_show.extend(["Tecnico_PAI","TR_PAI"])

            df_show = df_ab_tot[cols_show].copy()
            rename_map = {
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON","DIA_AB":"Abertura",
                "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            }
            st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

    # Infancia
    c3, c4 = st.columns(2)
    with c3:
        _sec("Infancia — Instalacoes do Dia")
        if inf_dia.empty:
            st.success("Nenhuma infancia hoje.")
        else:
            df_inf = inf_dia.copy()
            pais = df_inf.apply(_get_pai_inf, axis=1)
            df_inf["Tecnico_PAI"] = [p[0] for p in pais]
            df_inf["TR_PAI"] = [p[1] for p in pais]

            cols_show = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess"]
            if "SA_REPARO_INFANCIA" in df_inf.columns:
                cols_show.append("SA_REPARO_INFANCIA")
            cols_show.extend(["Tecnico_PAI","TR_PAI"])

            df_show = df_inf[cols_show].copy()
            rename_map = {
                "Número SA":"SA Inst.","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON",
                "SA_REPARO_INFANCIA":"SA Reparo",
                "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
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
            pais = inf_ab_dia.apply(_get_pai_inf, axis=1)
            inf_ab_dia["Tecnico_PAI"] = [p[0] for p in pais]
            inf_ab_dia["TR_PAI"] = [p[1] for p in pais]

            cols_show = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","Estado"]
            cols_show.extend(["Tecnico_PAI","TR_PAI"])

            df_show = inf_ab_dia[cols_show].copy()
            rename_map = {
                "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON",
                "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
            }
            st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

    # NOVA SEÇÃO: Em Garantia Alarmado (Repetido e Infancia)
    _sec("Em Garantia Alarmado (Repetido e Infância)")
    # Repetidos em garantia alarmados
    rep_alarm_garantia = rep_ab_tot[rep_ab_tot["ALARMADO"] == "SIM"] if not rep_ab_tot.empty and "ALARMADO" in rep_ab_tot.columns else pd.DataFrame()
    # Infâncias abertas alarmadas
    inf_alarm_garantia = inf_ab_dia[inf_ab_dia["ALARMADO"] == "SIM"] if not inf_ab_dia.empty and "ALARMADO" in inf_ab_dia.columns else pd.DataFrame()

    if rep_alarm_garantia.empty and inf_alarm_garantia.empty:
        st.success("Nenhum registro em garantia alarmado.")
    else:
        tab_rep, tab_inf = st.tabs(["🔁 Repetidos Alarmados", "👶 Infância Alarmada"])
        with tab_rep:
            if rep_alarm_garantia.empty:
                st.info("Nenhum repetido alarmado em garantia.")
            else:
                pais = rep_alarm_garantia.apply(_get_pai_rep, axis=1)
                rep_alarm_garantia["Tecnico_PAI"] = [p[0] for p in pais]
                rep_alarm_garantia["TR_PAI"] = [p[1] for p in pais]

                cols_show = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","DIA_AB"]
                if "Alarm ID" in rep_alarm_garantia.columns:
                    cols_show.append("Alarm ID")
                cols_show.extend(["Tecnico_PAI","TR_PAI"])

                df_show = rep_alarm_garantia[cols_show].copy()
                rename_map = {
                    "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                    "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON","DIA_AB":"Abertura",
                    "Alarm ID":"Alarme",
                    "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
                }
                st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

        with tab_inf:
            if inf_alarm_garantia.empty:
                st.info("Nenhuma infância alarmada em garantia.")
            else:
                pais = inf_alarm_garantia.apply(_get_pai_inf, axis=1)
                inf_alarm_garantia["Tecnico_PAI"] = [p[0] for p in pais]
                inf_alarm_garantia["TR_PAI"] = [p[1] for p in pais]

                cols_show = ["Número SA","CODIGO_TECNICO_EXTRAIDO","NOME_TEC","FSLOI_GPONAccess","Estado"]
                if "Alarm ID" in inf_alarm_garantia.columns:
                    cols_show.append("Alarm ID")
                cols_show.extend(["Tecnico_PAI","TR_PAI"])

                df_show = inf_alarm_garantia[cols_show].copy()
                rename_map = {
                    "Número SA":"SA","CODIGO_TECNICO_EXTRAIDO":"TR",
                    "NOME_TEC":"Tecnico","FSLOI_GPONAccess":"GPON",
                    "Alarm ID":"Alarme",
                    "Tecnico_PAI":"Tecnico (PAI)","TR_PAI":"TR (PAI)"
                }
                st.dataframe(df_show.rename(columns=rename_map), use_container_width=True, hide_index=True)

    # P0
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
