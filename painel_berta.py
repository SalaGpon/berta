#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bot Telegram Unificado - VERSÃO 10.76 + OPERAÇÕES + SUPERVISOR + PLANILHA DE PENDÊNCIAS
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any, List
import re
import unicodedata
import tempfile
from functools import wraps
import requests  # NOVO: para envio à planilha

# =============================================================================
# IMPORTAÇÕES CONDICIONAIS (OCR)
# =============================================================================
try:
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    OCR_DISPONIVEL = True
except ImportError:
    OCR_DISPONIVEL = False

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)
from telegram.constants import ParseMode

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if not OCR_DISPONIVEL:
    logger.warning("⚠️ pytesseract ou PIL não instalados. OCR desabilitado para pendências.")

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

TOKEN = os.getenv("BERTA_TOKEN", "")
if not TOKEN:
    raise RuntimeError("BERTA_TOKEN não definido")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE_BOT = os.path.join(BASE_DIR, 'BASEBOT.csv')
CAMINHO_PRESENCA = os.path.join(BASE_DIR, 'presenca.xlsx')
if not os.path.exists(CAMINHO_PRESENCA):
    CAMINHO_PRESENCA = os.path.join(BASE_DIR, 'Presença.xlsx')

# Grupo para envio de pendências
GRUPO_PENDENCIAS_ID = -1003695819937

# Supervisores permitidos
SUPERVISORES_PERMITIDOS = ["DANIEL OLIVEIRA", "TIAGO FRANCA", "DANIEL", "TIAGO"]

# URL do Web App para salvar pendências na planilha (ATUALIZE COM A SUA URL REAL)
URL_SALVAR_PENDENCIA = "https://script.google.com/macros/s/AKfycbwVRI7v5XcEXTbqvcYAvOvAeIS693_6kdz1bqpnalddcmTyEwsCKy3-8UnMLut8VcaQjQ/exec"

_df_cache = {
    'base': None,
    'base_timestamp': None,
    'presenca': None,
    'presenca_timestamp': None
}
CACHE_DURATION = 300
_supervisores_cache = {}

# =============================================================================
# FUNÇÕES DE UTILIDADE
# =============================================================================

def limpar_cache():
    global _df_cache, _supervisores_cache
    _df_cache = {'base': None, 'base_timestamp': None, 'presenca': None, 'presenca_timestamp': None}
    _supervisores_cache = {}
    logger.info("🧹 Cache limpo")

def cache_valido(tipo: str) -> bool:
    ts = _df_cache.get(f'{tipo}_timestamp')
    return ts is not None and (datetime.now() - ts).total_seconds() < CACHE_DURATION

def remover_acentos(texto: str) -> str:
    if not isinstance(texto, str):
        return str(texto) if texto is not None else ''
    return ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))

def extrair_codigo_tecnico(tecnico_str) -> Optional[str]:
    try:
        if pd.isna(tecnico_str):
            return None
        match = re.search(r'(TR\d+|TT\d+|TC\d+)', str(tecnico_str).strip())
        return match.group(1) if match else None
    except:
        return None

def extrair_codigo_do_tecnico(tecnico_dict: Dict[str, Any]) -> Optional[str]:
    funcionario = str(tecnico_dict.get('funcionario') or '').strip()
    if funcionario:
        c = extrair_codigo_tecnico(funcionario)
        if c:
            return c.upper()
    for k in ['tc', 'tr', 'tt']:
        v = str(tecnico_dict.get(k) or '').strip().upper()
        if v and re.match(r'^(TR|TT|TC)\d+$', v, re.IGNORECASE):
            return v
    return None

def extrair_nome_tecnico(tecnico_dict: Dict[str, Any]) -> Optional[str]:
    func = tecnico_dict.get('funcionario', '')
    if ' - ' in func:
        return func.split(' - ')[0].strip()
    return func.strip() if func else tecnico_dict.get('nome')

def formatar_data(data) -> str:
    try:
        if pd.isna(data):
            return 'N/A'
        if isinstance(data, (pd.Timestamp, datetime)):
            return data.strftime('%d/%m/%Y %H:%M')
        return str(data)
    except:
        return 'N/A'

def formatar_data_simples(data) -> str:
    try:
        if pd.isna(data):
            return 'N/A'
        if isinstance(data, (pd.Timestamp, datetime)):
            return data.strftime('%d/%m/%Y')
        return str(data)
    except:
        return 'N/A'

def classificar_velocidade(velocidade) -> str:
    try:
        if pd.isna(velocidade):
            return "DESCONHECIDA"
        vel = float(re.sub(r'[^\d.]', '', str(velocidade).replace(',', '.')))
        if vel < 600:
            return "BAIXA"
        if vel <= 999:
            return "ALTA"
        return "GIGA"
    except:
        return "DESCONHECIDA"

def normalizar_codigo(codigo):
    if not codigo:
        return None
    codigo = str(codigo).upper().strip()
    return re.sub(r'[^0-9]', '', codigo)

def formatar_endereco(row) -> str:
    parts = []
    logr = None
    for col in ['LOGRADOURO', 'Logradouro', 'Logradouro_cli']:
        v = row.get(col) if isinstance(row, dict) else getattr(row, col, None)
        if v is not None and pd.notna(v) and str(v).strip():
            logr = str(v).strip()
            break
    if logr:
        parts.append(logr)
    num = row.get('NUMERO') or row.get('Número')
    if num is not None and pd.notna(num) and str(num).strip():
        parts.append(f", {str(num).strip()}")
    bai = row.get('BAIRRO') or row.get('Bairro')
    if bai is not None and pd.notna(bai) and str(bai).strip():
        parts.append(f" - {str(bai).strip()}")
    cid = row.get('CIDADE') or row.get('Cidade')
    if cid is not None and pd.notna(cid) and str(cid).strip():
        parts.append(f", {str(cid).strip()}")
    return ''.join(parts) if parts else 'Endereço não disponível'

# =============================================================================
# CARREGAMENTO DA BASE (mantido)
# =============================================================================

def carregar_base(forcar_recarregar: bool = False) -> Optional[pd.DataFrame]:
    if not forcar_recarregar and cache_valido('base') and _df_cache['base'] is not None:
        return _df_cache['base'].copy()
    try:
        if not os.path.exists(CAMINHO_BASE_BOT):
            logger.error("BASEBOT.csv não encontrada")
            return None
        
        df = pd.read_csv(CAMINHO_BASE_BOT, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
        logger.info(f"✅ Base carregada: {len(df)} registros")
        df.columns = df.columns.str.strip()
        
        # Filtro UF=SC
        if "UF" in df.columns:
            antes = len(df)
            df = df[df["UF"].astype(str).str.strip().str.upper() == "SC"].copy()
            logger.info(f"✅ Filtro UF=SC: {len(df):,}/{antes:,} registros mantidos")
        
        # Converter datas e remover timezone
        colunas_data = ['AB_BA', 'DH_FIM_EXEC_REAL', 'DH_INI_EXEC_REAL', 'INICIO_AG', 'DH_INICIO_EXEC_PREV']
        for col in colunas_data:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                if df[col].dt.tz is not None:
                    df[col] = df[col].dt.tz_localize(None)
        
        # Criar DATA_ORDENACAO com prioridade
        df['DATA_ORDENACAO'] = None
        if 'DH_INICIO_EXEC_PREV' in df.columns:
            df['DATA_ORDENACAO'] = df['DATA_ORDENACAO'].fillna(df['DH_INICIO_EXEC_PREV'])
        if 'INICIO_AG' in df.columns:
            df['DATA_ORDENACAO'] = df['DATA_ORDENACAO'].fillna(df['INICIO_AG'])
        if 'AB_BA' in df.columns:
            df['DATA_ORDENACAO'] = df['DATA_ORDENACAO'].fillna(df['AB_BA'])
        df['DATA_ORDENACAO'] = df['DATA_ORDENACAO'].fillna(datetime.now())
        
        df['AB_DT'] = df['DATA_ORDENACAO']
        if 'DH_FIM_EXEC_REAL' in df.columns:
            df['FIM_DT'] = df['DH_FIM_EXEC_REAL']
        
        # Garantir flags
        for col, default in [('FLAG_REPETIDO', 'NAO'), ('FLAG_INFANCIA', 'NAO'), ('ALARMADO', 'NAO')]:
            if col not in df.columns:
                df[col] = default
            else:
                df[col] = df[col].fillna(default).astype(str).str.strip().str.upper()
        
        if 'CDOE' not in df.columns:
            df['CDOE'] = ''
        
        _df_cache['base'] = df
        _df_cache['base_timestamp'] = datetime.now()
        logger.info(f"✅ Base pronta: {len(df)} registros")
        return df.copy()
    except Exception as e:
        logger.error(f"Erro ao carregar base: {e}", exc_info=True)
        return None

def carregar_presenca(forcar_recarregar: bool = False) -> Optional[pd.DataFrame]:
    if not forcar_recarregar and cache_valido('presenca') and _df_cache['presenca'] is not None:
        return _df_cache['presenca'].copy()
    try:
        if not os.path.exists(CAMINHO_PRESENCA):
            return None
        df = pd.read_excel(CAMINHO_PRESENCA, sheet_name='Técnicos', dtype=str)
        _df_cache['presenca'] = df
        _df_cache['presenca_timestamp'] = datetime.now()
        logger.info("✅ Presença carregada")
        return df.copy()
    except Exception as e:
        logger.error(f"Erro ao carregar presença: {e}")
        return None

# =============================================================================
# AUTENTICAÇÃO (MOCK)
# =============================================================================

async def autenticar_tecnico(telegram_id: int, matricula: str) -> Optional[Dict[str, Any]]:
    matricula = matricula.strip().upper()
    logger.info(f"🔐 Autenticando {matricula}")
    if re.match(r'^(TR|TT|TC)\d+$', matricula):
        return {
            'funcionario': f'Técnico {matricula}',
            'tr': matricula,
            'supervisor': 'Daniel Oliveira',
            'setor_atual': 'Joinville',
            'telegram_id': telegram_id
        }
    return None

def verificar_autenticacao(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return 'tecnico' in context.user_data

def verificar_supervisor_autenticado(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data.get('modo_supervisor', False)

def usuario_autorizado(context: ContextTypes.DEFAULT_TYPE) -> bool:
    if context.user_data.get('modo_supervisor', False):
        nome_supervisor = context.user_data.get('nome_supervisor', '')
        return any(permitido in nome_supervisor.upper() for permitido in SUPERVISORES_PERMITIDOS)
    tecnico = context.user_data.get('tecnico', {})
    if not tecnico:
        return False
    supervisor = tecnico.get('supervisor', '').upper().strip()
    return any(permitido in supervisor for permitido in SUPERVISORES_PERMITIDOS)

def acesso_restringido(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not usuario_autorizado(context):
            await update.message.reply_text(
                "🚧 Ferramenta em teste exclusiva da equipe de Joinville.\n"
                "Procure seu supervisor para mais informações."
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# =============================================================================
# CONSULTAS POR TÉCNICO (mantidas)
# =============================================================================

def _filtrar_tecnico(df: pd.DataFrame, codigo_tecnico: str = None, nome_tecnico: str = None) -> pd.DataFrame:
    mask_total = pd.Series(False, index=df.index)
    if codigo_tecnico:
        cod_upper = codigo_tecnico.strip().upper()
        if 'TR' in df.columns:
            mask_total |= df['TR'].astype(str).str.strip().str.upper() == cod_upper
        if 'TECNICO_EXECUTOR' in df.columns:
            mask_total |= df['TECNICO_EXECUTOR'].astype(str).str.upper().str.contains(cod_upper, na=False)
    if nome_tecnico and 'TECNICO_EXECUTOR' in df.columns:
        mask_total |= df['TECNICO_EXECUTOR'].astype(str).str.upper().str.contains(nome_tecnico.upper(), na=False)
    return df[mask_total].reset_index(drop=True)

def get_atividades_por_tecnico(codigo_tecnico=None, nome_tecnico=None, tipo='futuras', dias=30):
    df = carregar_base()
    if df is None:
        return None
    df = df.copy()
    
    df_tec = _filtrar_tecnico(df, codigo_tecnico, nome_tecnico)
    if df_tec.empty:
        return pd.DataFrame()
    
    hoje = datetime.now()
    data_limite = hoje - timedelta(days=dias)
    
    if tipo == 'futuras':
        estados_concluidos = ['CONCLUÍDO COM SUCESSO', 'CONCLUÍDO SEM SUCESSO', 'CANCELADO']
        df_tec['ESTADO'] = df_tec['ESTADO'].astype(str).str.strip().str.upper()
        mask_nao_concluida = ~df_tec['ESTADO'].isin(estados_concluidos)
        atividades = df_tec[mask_nao_concluida]
    elif tipo == 'encerradas':
        if 'DH_FIM_EXEC_REAL' not in df_tec.columns:
            return pd.DataFrame()
        df_tec['DH_FIM_EXEC_REAL'] = pd.to_datetime(df_tec['DH_FIM_EXEC_REAL'], errors='coerce')
        df_tec = df_tec[df_tec['DH_FIM_EXEC_REAL'].notna()]
        mask_encerradas = df_tec['ESTADO'].isin(['CONCLUÍDO COM SUCESSO', 'CONCLUÍDO SEM SUCESSO'])
        mask_encerradas &= (df_tec['DH_FIM_EXEC_REAL'] >= data_limite)
        atividades = df_tec[mask_encerradas]
    else:
        atividades = df_tec
    
    colunas = ['SA', 'MACRO', 'DATA_ORDENACAO', 'AB_DT', 'DH_FIM_EXEC_REAL', 'ESTADO', 'CIDADE', 'BAIRRO', 'LOGRADOURO',
               'NUMERO', 'DESCRICAO', 'GPON', 'INICIO_AG', 'DH_INICIO_EXEC_PREV', 'VELOCIDADE', 'ALARMADO', 'CDOE', 'FLAG_REPETIDO']
    colunas = [c for c in colunas if c in atividades.columns]
    
    if not colunas:
        return pd.DataFrame()
    
    atividades = atividades[colunas]
    if 'DATA_ORDENACAO' in atividades.columns:
        atividades = atividades.sort_values('DATA_ORDENACAO', ascending=True)
    elif tipo == 'encerradas' and 'DH_FIM_EXEC_REAL' in atividades.columns:
        atividades = atividades.sort_values('DH_FIM_EXEC_REAL', ascending=False)
    
    return atividades

def get_alarmados_por_tecnico(codigo_tecnico=None, nome_tecnico=None):
    df = carregar_base()
    if df is None:
        return None
    df = df.copy()
    if 'ALARMADO' not in df.columns:
        return pd.DataFrame()
    
    df_tec = _filtrar_tecnico(df, codigo_tecnico, nome_tecnico)
    mask_alarme = df_tec['ALARMADO'].astype(str).str.strip().str.upper() == 'SIM'
    df_alarme = df_tec[mask_alarme].copy()
    
    if 'DH_FIM_EXEC_REAL' in df_alarme.columns:
        df_alarme = df_alarme.sort_values('DH_FIM_EXEC_REAL', ascending=False)
    return df_alarme

def get_atividades_nao_atribuidas(setor: str = None) -> Optional[pd.DataFrame]:
    df = carregar_base()
    if df is None:
        return None
    df = df.copy()
    mask_nao_atribuido = df['TECNICO_EXECUTOR'].isna() | (df['TECNICO_EXECUTOR'].astype(str).str.strip() == '')
    mask_aberto = df['ESTADO'].isin(['ATRIBUÍDO', 'NÃO ATRIBUÍDO', 'RECEBIDO', 'EM EXECUÇÃO', 'EM DESLOCAMENTO', 'PENDENTE'])
    if setor:
        if 'TERRITORIO' in df.columns:
            mask_setor = df['TERRITORIO'].astype(str).str.upper() == setor.upper()
            df_filtrado = df[mask_nao_atribuido & mask_aberto & mask_setor]
        else:
            df_filtrado = df[mask_nao_atribuido & mask_aberto]
    else:
        df_filtrado = df[mask_nao_atribuido & mask_aberto]
    if df_filtrado.empty:
        return pd.DataFrame()
    colunas = ['SA', 'MACRO', 'DATA_ORDENACAO', 'ESTADO', 'CIDADE', 'BAIRRO', 'LOGRADOURO', 'NUMERO', 'GPON', 'VELOCIDADE']
    colunas = [c for c in colunas if c in df_filtrado.columns]
    return df_filtrado[colunas].sort_values('DATA_ORDENACAO', ascending=True)

def formatar_atividades(df, titulo, max_itens=50, ver_todas=False):
    if df is None or df.empty:
        return f"📭 {titulo}:\nNenhuma atividade encontrada."
    
    it = df.iterrows() if ver_todas else df.head(max_itens).iterrows()
    msg = f"📋 {titulo} ({len(df)}):\n\n"
    
    for _, row in it:
        if len(msg) > 3500 and not ver_todas:
            msg += "... (mais atividades não mostradas)"
            break
        
        msg += f"🔹 SA: {row.get('SA','N/A')}\n"
        if 'MACRO' in row:
            msg += f"   Tipo: {row['MACRO']}\n"
        if 'GPON' in row and pd.notna(row['GPON']):
            msg += f"   GPON: {row['GPON']}\n"
            rep = str(row.get('FLAG_REPETIDO','')).strip().upper()
            msg += f"   {'⚠️' if rep == 'SIM' else '✅'} Repetido: {rep}\n"
        if 'CDOE' in row and pd.notna(row['CDOE']) and str(row['CDOE']).strip() not in ('', 'nan'):
            msg += f"   📦 CDOE: {row['CDOE']}\n"
        if 'VELOCIDADE' in row and pd.notna(row['VELOCIDADE']) and str(row['VELOCIDADE']).strip() not in ('', '0', 'nan'):
            try:
                vel = float(re.sub(r'[^\d.]', '', str(row['VELOCIDADE']).replace(',', '.')))
                classe = classificar_velocidade(vel)
                msg += f"   ⚡ Velocidade: {vel:.0f} Mbps ({classe})\n"
            except:
                pass
        if 'ALARMADO' in row and str(row['ALARMADO']).strip().upper() == 'SIM':
            msg += f"   🚨 Alarmado: SIM\n"
        
        # Mostrar a data mais relevante
        if 'DH_INICIO_EXEC_PREV' in row and pd.notna(row['DH_INICIO_EXEC_PREV']):
            msg += f"   📅 Execução Prevista: {row['DH_INICIO_EXEC_PREV'].strftime('%d/%m/%Y %H:%M')}\n"
        elif 'INICIO_AG' in row and pd.notna(row['INICIO_AG']):
            msg += f"   📅 Agendamento: {row['INICIO_AG'].strftime('%d/%m/%Y %H:%M')}\n"
        elif 'DATA_ORDENACAO' in row and pd.notna(row['DATA_ORDENACAO']):
            msg += f"   📅 Abertura: {row['DATA_ORDENACAO'].strftime('%d/%m/%Y')}\n"
        
        end = formatar_endereco(row)
        if end != 'Endereço não disponível':
            msg += f"   📍 {end}\n"
        if 'ESTADO' in row:
            msg += f"   Status: {row['ESTADO']}\n"
        msg += "\n"
    
    if not ver_todas and len(df) > max_itens:
        msg += f"\n... e mais {len(df)-max_itens} atividades não listadas."
    
    return msg

# =============================================================================
# INDICADORES (mantidos)
# =============================================================================

def contar_reparos_repetidos_por_tecnico(df: pd.DataFrame, codigo_tecnico: str, mes_ref: int = None, ano_ref: int = None) -> Dict[str, Any]:
    try:
        if df is None or df.empty:
            return {'erro': 'Base não carregada'}
        
        hoje = datetime.now()
        if mes_ref is None or ano_ref is None:
            mes_ref = hoje.month
            ano_ref = hoje.year
        
        primeiro_dia = datetime(ano_ref, mes_ref, 1)
        if mes_ref == 12:
            ultimo_dia = datetime(ano_ref + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(ano_ref, mes_ref + 1, 1) - timedelta(days=1)
        
        meses_pt = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                    'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
        periodo = f"{meses_pt[mes_ref-1]}/{ano_ref}"
        
        df = df.copy()
        if "UF" in df.columns:
            df = df[df["UF"].astype(str).str.strip().str.upper() == "SC"]
        
        mask_tec = pd.Series(False, index=df.index)
        if 'TR' in df.columns:
            mask_tec |= df['TR'].astype(str).str.strip().str.upper() == codigo_tecnico.upper()
        if 'TECNICO_EXECUTOR' in df.columns:
            mask_tec |= df['TECNICO_EXECUTOR'].astype(str).str.upper().str.contains(codigo_tecnico.upper(), na=False)
        
        df_rep_tec = df[
            mask_tec &
            (df["MACRO"].astype(str).str.strip().str.upper() == "REP-FTTH") &
            (df["ESTADO"].astype(str).str.strip().str.upper() == "CONCLUÍDO COM SUCESSO") &
            (df["AB_DT"] >= primeiro_dia) &
            (df["AB_DT"] <= ultimo_dia) &
            df["AB_DT"].notna()
        ]
        total_reparos = len(df_rep_tec)
        
        if 'FLAG_REPETIDO' in df_rep_tec.columns:
            reparos_repetidos = (df_rep_tec['FLAG_REPETIDO'] == 'SIM').sum()
            fonte = "VIP"
        else:
            reparos_repetidos = 0
            fonte = "cálculo interno"
        
        taxa = round(int(reparos_repetidos) / total_reparos * 100, 2) if total_reparos > 0 else 0
        
        logger.info(f"📊 [{codigo_tecnico}] Repetidos {periodo}: total={total_reparos}, rep={reparos_repetidos}, taxa={taxa}%")
        
        return {
            'total_reparos': total_reparos,
            'reparos_repetidos': int(reparos_repetidos),
            'taxa': taxa,
            'periodo': periodo,
            'fonte': fonte,
        }
    except Exception as e:
        logger.error(f"Erro: {e}", exc_info=True)
        return {'erro': f'Erro no cálculo: {str(e)}'}

def calcular_infancia_por_tecnico(codigo_tecnico: str = None, mes_ref: int = None, ano_ref: int = None) -> Dict[str, Any]:
    try:
        df = carregar_base()
        if df is None:
            return {'erro': 'Base não carregada'}
        
        hoje = datetime.now()
        if mes_ref is None or ano_ref is None:
            mes_ref = hoje.month
            ano_ref = hoje.year
        
        primeiro_dia_mes = datetime(ano_ref, mes_ref, 1)
        if mes_ref == 12:
            primeiro_dia_prox = datetime(ano_ref + 1, 1, 1)
        else:
            primeiro_dia_prox = datetime(ano_ref, mes_ref + 1, 1)
        
        meses_pt = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                    'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
        periodo = f"{meses_pt[mes_ref-1]}/{ano_ref}"
        
        df = df.copy()
        if "UF" in df.columns:
            df = df[df["UF"].astype(str).str.strip().str.upper() == "SC"]
        
        mask_tec = pd.Series(False, index=df.index)
        if 'TR' in df.columns:
            mask_tec |= df['TR'].astype(str).str.strip().str.upper() == codigo_tecnico.upper()
        if 'TECNICO_EXECUTOR' in df.columns:
            mask_tec |= df['TECNICO_EXECUTOR'].astype(str).str.upper().str.contains(codigo_tecnico.upper(), na=False)
        
        df_tec = df[mask_tec]
        if df_tec.empty:
            return {'erro': f'Técnico {codigo_tecnico} não encontrado'}
        
        mask_inst = (
            (df_tec['MACRO'].astype(str).str.strip().str.upper() == 'INST-FTTH') &
            (df_tec['ESTADO'].astype(str).str.strip().str.upper() == 'CONCLUÍDO COM SUCESSO') &
            (df_tec["AB_DT"] >= primeiro_dia_mes) &
            (df_tec["AB_DT"] < primeiro_dia_prox) &
            df_tec["AB_DT"].notna()
        )
        df_inst_periodo = df_tec[mask_inst]
        total_instalacoes = len(df_inst_periodo)
        
        if total_instalacoes == 0:
            return {'total_instalacoes': 0, 'instalacoes_infancia': 0, 'taxa_infancia': 0, 'periodo': periodo, 'fonte': 'VIP'}
        
        if 'FLAG_INFANCIA' in df_inst_periodo.columns:
            instalacoes_infancia = (df_inst_periodo['FLAG_INFANCIA'] == 'SIM').sum()
            fonte = "VIP"
        else:
            instalacoes_infancia = 0
            fonte = "interno"
        
        taxa = round(instalacoes_infancia / total_instalacoes * 100, 2) if total_instalacoes else 0
        
        logger.info(f"📊 [{codigo_tecnico}] Infância {periodo}: inst={total_instalacoes}, inf={instalacoes_infancia}, taxa={taxa}%")
        
        return {
            'total_instalacoes': total_instalacoes,
            'instalacoes_infancia': int(instalacoes_infancia),
            'taxa_infancia': taxa,
            'periodo': periodo,
            'fonte': fonte,
        }
    except Exception as e:
        logger.error(f"Erro: {e}", exc_info=True)
        return {'erro': f'Erro no cálculo: {str(e)}'}

def calcular_p0_por_tecnico(codigo_tecnico: str) -> Dict[str, Any]:
    try:
        df = carregar_base()
        if df is None:
            return {'erro': 'Base não carregada'}
        
        hoje = datetime.now()
        primeiro_dia_mes = datetime(hoje.year, hoje.month, 1)
        status_encerrado = ['CONCLUÍDO COM SUCESSO', 'CONCLUÍDO SEM SUCESSO']
        
        df = df.copy()
        mask_tec = pd.Series(False, index=df.index)
        if 'TR' in df.columns:
            mask_tec |= df['TR'].astype(str).str.strip().str.upper() == codigo_tecnico.upper()
        if 'TECNICO_EXECUTOR' in df.columns:
            mask_tec |= df['TECNICO_EXECUTOR'].astype(str).str.upper().str.contains(codigo_tecnico.upper(), na=False)
        
        df = df[mask_tec]
        if 'DH_FIM_EXEC_REAL' not in df.columns:
            return {'erro': 'Coluna DH_FIM_EXEC_REAL não encontrada'}
        
        df['DH_FIM_EXEC_REAL'] = pd.to_datetime(df['DH_FIM_EXEC_REAL'], dayfirst=True, errors='coerce')
        df = df[
            (df['DH_FIM_EXEC_REAL'].notna()) &
            (df['ESTADO'].isin(status_encerrado)) &
            (df['DH_FIM_EXEC_REAL'] >= primeiro_dia_mes)
        ]
        
        if df.empty:
            return {'p0_10': 0, 'p0_15': 0, 'total_dias': 0}
        
        df['data'] = df['DH_FIM_EXEC_REAL'].dt.date
        df['hora'] = df['DH_FIM_EXEC_REAL'].dt.time
        p0_10 = 0
        p0_15 = 0
        total_dias = 0
        
        for data, grupo in df.groupby('data'):
            total_dias += 1
            grupo = grupo.sort_values('DH_FIM_EXEC_REAL')
            primeiro = grupo.iloc[0]
            if primeiro['hora'] > time(10, 0):
                p0_10 += 1
            tarde = grupo[grupo['hora'] >= time(13, 0)]
            if not tarde.empty:
                primeiro_tarde = tarde.iloc[0]
                if primeiro_tarde['hora'] > time(15, 0):
                    p0_15 += 1
            else:
                p0_15 += 1
        
        return {'p0_10': p0_10, 'p0_15': p0_15, 'total_dias': total_dias}
    except Exception as e:
        logger.error(f"Erro P0: {e}")
        return {'erro': str(e)}

def analisar_velocidades_futuras_por_tecnico(codigo_tecnico: str = None, nome_tecnico: str = None) -> Dict[str, Any]:
    try:
        df = carregar_base()
        if df is None:
            return {'erro': 'Base não carregada'}
        
        df_tec = _filtrar_tecnico(df, codigo_tecnico, nome_tecnico)
        if df_tec.empty:
            return {'erro': f'Técnico não encontrado'}
        
        estados_abertos = ['ATRIBUÍDO', 'RECEBIDO', 'EM DESLOCAMENTO', 'EM EXECUÇÃO', 'PENDENTE']
        mask_abertas = df_tec['ESTADO'].isin(estados_abertos)
        df_futuras = df_tec[mask_abertas].copy()
        
        if df_futuras.empty:
            return {'total': 0, 'baixa': 0, 'alta': 0, 'giga': 0, 'desconhecida': 0, 'lista': []}
        
        def classificar(v):
            if pd.isna(v):
                return 'DESCONHECIDA'
            try:
                vel = float(re.sub(r'[^\d.]', '', str(v).replace(',', '.')))
                if vel < 600:
                    return 'BAIXA'
                elif vel <= 999:
                    return 'ALTA'
                else:
                    return 'GIGA'
            except:
                return 'DESCONHECIDA'
        
        if 'VELOCIDADE' in df_futuras.columns:
            df_futuras['CLASSE_VELOCIDADE'] = df_futuras['VELOCIDADE'].apply(classificar)
        else:
            df_futuras['CLASSE_VELOCIDADE'] = 'DESCONHECIDA'
        
        total = len(df_futuras)
        baixa = (df_futuras['CLASSE_VELOCIDADE'] == 'BAIXA').sum()
        alta = (df_futuras['CLASSE_VELOCIDADE'] == 'ALTA').sum()
        giga = (df_futuras['CLASSE_VELOCIDADE'] == 'GIGA').sum()
        desconhecida = (df_futuras['CLASSE_VELOCIDADE'] == 'DESCONHECIDA').sum()
        
        lista = []
        for _, row in df_futuras.iterrows():
            lista.append({
                'sa': row.get('SA', 'N/A'),
                'velocidade': row.get('VELOCIDADE', 'N/A'),
                'classe': row['CLASSE_VELOCIDADE'],
                'gpon': row.get('GPON', 'N/A'),
                'endereco': formatar_endereco(row)
            })
        
        return {'total': total, 'baixa': baixa, 'alta': alta, 'giga': giga, 'desconhecida': desconhecida, 'lista': lista}
    except Exception as e:
        logger.error(f"Erro: {e}", exc_info=True)
        return {'erro': str(e)}

def formatar_velocidades_futuras(analise: Dict[str, Any]) -> str:
    if 'erro' in analise:
        return f"❌ {analise['erro']}"
    if analise['total'] == 0:
        return "📭 Nenhuma atividade futura encontrada."
    
    msg = f"🚀 *VELOCIDADES - ATIVIDADES FUTURAS*\n\n"
    msg += f"📊 *Total:* {analise['total']}\n"
    msg += f"🐢 *Baixa (<600 Mbps):* {analise['baixa']}\n"
    msg += f"⚡ *Alta (600-999 Mbps):* {analise['alta']}\n"
    msg += f"🏆 *Giga (≥1000 Mbps):* {analise['giga']}\n"
    msg += f"❓ *Desconhecida:* {analise['desconhecida']}\n\n"
    
    if analise['lista']:
        msg += "📋 *Detalhamento:*\n"
        for item in analise['lista'][:20]:
            msg += f"🔹 SA: {item['sa']} - {item['velocidade']} Mbps ({item['classe']})\n"
            msg += f"   GPON: {item['gpon']}\n"
            msg += f"   📍 {item['endereco']}\n\n"
        if len(analise['lista']) > 20:
            msg += f"... e mais {len(analise['lista']) - 20} atividades.\n"
    return msg

# =============================================================================
# DETALHAMENTOS (mantidos)
# =============================================================================

async def repetidos_detalhado_core(message, context):
    """Exibe cadeias completas de repetição onde o técnico logado foi o PAI (primeiro reparo)
       e o segundo reparo (primeira reincidência) ocorreu no MÊS ATUAL.
       Apenas reparos CONCLUÍDO COM SUCESSO são considerados."""
    mat = context.user_data.get('matricula_usada')
    if not mat:
        tecnico = context.user_data.get('tecnico')
        mat = extrair_codigo_do_tecnico(tecnico) or ''
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return

    df = carregar_base()
    if df is None or df.empty:
        await message.reply_text("❌ Base não carregada.")
        return

    try:
        hoje = datetime.now()
        primeiro_dia_mes = datetime(hoje.year, hoje.month, 1)
        if hoje.month == 12:
            ultimo_dia_mes = datetime(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia_mes = datetime(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

        df = df.copy()
        if "UF" in df.columns:
            df = df[df["UF"].astype(str).str.strip().str.upper() == "SC"]

        # Filtrar reparos (apenas CONCLUÍDO COM SUCESSO)
        df_rep = df[
            (df["MACRO"].astype(str).str.strip().str.upper() == "REP-FTTH") &
            (df["ESTADO"].astype(str).str.strip().str.upper() == "CONCLUÍDO COM SUCESSO") &
            df["AB_DT"].notna()
        ].copy()

        if df_rep.empty:
            await message.reply_text("📭 Nenhum reparo encontrado.")
            return

        df_rep = df_rep.sort_values(["GPON", "AB_DT"]).reset_index(drop=True)

        cadeias = []
        for gpon, grupo in df_rep.groupby("GPON"):
            if len(grupo) < 2:
                continue
            grupo = grupo.reset_index(drop=True)
            i = 0
            while i < len(grupo) - 1:
                cadeia_atual = [grupo.iloc[i]]
                j = i + 1
                while j < len(grupo) and (grupo.iloc[j]["AB_DT"] - grupo.iloc[j-1]["AB_DT"]).days <= 30:
                    cadeia_atual.append(grupo.iloc[j])
                    j += 1
                if len(cadeia_atual) >= 2:
                    # Verificar se o SEGUNDO reparo (índice 1) está no mês atual
                    segundo_rep = cadeia_atual[1]
                    if primeiro_dia_mes <= segundo_rep["AB_DT"] <= ultimo_dia_mes:
                        cadeias.append(cadeia_atual)
                i = j

        if not cadeias:
            await message.reply_text("📭 Nenhuma cadeia de repetição com segundo reparo neste mês.")
            return

        # Filtrar cadeias onde o técnico do primeiro reparo (PAI) é o usuário
        cadeias_do_tecnico = []
        for cadeia in cadeias:
            primeiro = cadeia[0]
            tr_primeiro = str(primeiro.get('TR', '')).strip().upper()
            tec_primeiro = str(primeiro.get('TECNICO_EXECUTOR', '')).strip().upper()
            if tr_primeiro == mat.upper() or mat.upper() in tec_primeiro:
                cadeias_do_tecnico.append(cadeia)

        if not cadeias_do_tecnico:
            await message.reply_text("📭 Você não foi o técnico PAI em nenhuma cadeia de repetição com segundo reparo neste mês.")
            return

        # Exibir cada cadeia
        for cadeia in cadeias_do_tecnico:
            primeiro = cadeia[0]
            endereco = formatar_endereco(primeiro)
            if endereco == 'Endereço não disponível':
                endereco = f"GPON: {primeiro.get('GPON', 'N/A')}"

            msg = f"🔄 *REPAROS REPETIDOS DETALHADOS (MÊS ATUAL)*\n\n"
            msg += f"📍 *Endereço:* {endereco}\n"
            msg += f"🔁 *Total de reincidências (≤30 dias):* {len(cadeia) - 1}\n\n"

            for idx, reparo in enumerate(cadeia, 1):
                data_ab = reparo.get("AB_DT")
                data_str = data_ab.strftime('%d/%m/%Y %H:%M') if pd.notna(data_ab) else 'N/A'
                tecnico = reparo.get("TECNICO_EXECUTOR") or reparo.get("TR", "N/A")
                sa = reparo.get("SA", "")
                if pd.isna(sa) or str(sa).strip() == "":
                    sa = "NULL"
                else:
                    sa = str(sa).strip()
                gpon = reparo.get("GPON", "N/A")
                cod_enc = reparo.get("COD_FECHAMENTO", "N/A")
                desc = reparo.get("DESCRICAO", "")
                if desc and len(str(desc)) > 80:
                    desc = str(desc)[:77] + "..."
                estado = reparo.get("ESTADO", "N/A")

                if idx == 1:
                    msg += f"🔹 *1º Reparo (PAI)*\n"
                else:
                    dias = (reparo["AB_DT"] - cadeia[idx-2]["AB_DT"]).days if idx > 1 else 0
                    msg += f"🔸 *{idx}º Reparo (após {dias} dias)*\n"
                msg += f"   SA: {sa}\n"
                msg += f"   📡 GPON: {gpon}\n"
                msg += f"   👤 Técnico: {tecnico}\n"
                msg += f"   📅 Abertura: {data_str}\n"
                msg += f"   🏷️ Estado: {estado}\n"
                if cod_enc and str(cod_enc) != "N/A" and str(cod_enc).strip() != "":
                    msg += f"   🔢 Cód. Encerramento: {cod_enc}\n"
                if desc and desc != "nan":
                    msg += f"   📝 Descrição: {desc}\n"
                msg += "\n"

            msg += "─" * 30 + "\n\n"

            if len(msg) > 4000:
                partes = [msg[i:i+3900] for i in range(0, len(msg), 3900)]
                for parte in partes:
                    await message.reply_text(parte, parse_mode="Markdown")
            else:
                await message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Erro repetidos_detalhado_core: {e}", exc_info=True)
        await message.reply_text(f"❌ Erro ao processar: {str(e)}")


async def infancia_detalhado_core(message, context):
    """Exibe instalações com infância onde o técnico foi o instalador (PAI)
       e o primeiro reparo filho ocorreu no MÊS ATUAL e foi CONCLUÍDO COM SUCESSO."""
    mat = context.user_data.get('matricula_usada')
    if not mat:
        tecnico = context.user_data.get('tecnico')
        mat = extrair_codigo_do_tecnico(tecnico) or ''
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return

    df = carregar_base()
    if df is None or df.empty:
        await message.reply_text("❌ Base não carregada.")
        return

    try:
        hoje = datetime.now()
        primeiro_dia_mes = datetime(hoje.year, hoje.month, 1)
        if hoje.month == 12:
            ultimo_dia_mes = datetime(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia_mes = datetime(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

        df = df.copy()
        if "UF" in df.columns:
            df = df[df["UF"].astype(str).str.strip().str.upper() == "SC"]

        # Instalações do técnico (apenas concluídas com sucesso)
        mask_tec = pd.Series(False, index=df.index)
        if 'TR' in df.columns:
            mask_tec |= df['TR'].astype(str).str.strip().str.upper() == mat.upper()
        if 'TECNICO_EXECUTOR' in df.columns:
            mask_tec |= df['TECNICO_EXECUTOR'].astype(str).str.upper().str.contains(mat.upper(), na=False)

        inst = df[
            mask_tec &
            (df["MACRO"].astype(str).str.strip().str.upper() == "INST-FTTH") &
            (df["ESTADO"].astype(str).str.strip().str.upper() == "CONCLUÍDO COM SUCESSO") &
            df["FIM_DT"].notna()
        ].copy()

        if inst.empty:
            await message.reply_text("📭 Nenhuma instalação sua encontrada.")
            return

        # Reparos que podem ser filhos (apenas concluídos com sucesso)
        rep = df[
            (df["MACRO"].astype(str).str.strip().str.upper() == "REP-FTTH") &
            (df["ESTADO"].astype(str).str.strip().str.upper() == "CONCLUÍDO COM SUCESSO") &
            df["AB_DT"].notna()
        ].copy()

        if rep.empty:
            await message.reply_text("📭 Nenhum reparo filho encontrado.")
            return

        resultados = []
        for _, pai in inst.iterrows():
            gpon = pai.get("GPON")
            if pd.isna(gpon):
                continue
            data_inst = pai.get("FIM_DT")
            if pd.isna(data_inst):
                continue
            limite = data_inst + timedelta(days=30)
            filhos = rep[
                (rep["GPON"] == gpon) &
                (rep["AB_DT"] > data_inst) &
                (rep["AB_DT"] <= limite)
            ].sort_values("AB_DT")
            if not filhos.empty:
                # Verificar se o primeiro filho está no mês atual
                primeiro_filho = filhos.iloc[0]
                if primeiro_dia_mes <= primeiro_filho["AB_DT"] <= ultimo_dia_mes:
                    resultados.append((pai, filhos))

        if not resultados:
            await message.reply_text("📭 Nenhuma infância com primeiro reparo neste mês.")
            return

        for pai, filhos in resultados:
            endereco = formatar_endereco(pai)
            if endereco == 'Endereço não disponível':
                endereco = f"GPON: {pai.get('GPON', 'N/A')}"

            msg = f"👶 *INFÂNCIA DETALHADA (MÊS ATUAL)*\n\n"
            msg += f"📍 *Endereço:* {endereco}\n"
            msg += f"📦 *Total de reparos em até 30 dias:* {len(filhos)}\n\n"

            data_inst = pai.get("FIM_DT")
            data_str = data_inst.strftime('%d/%m/%Y %H:%M') if pd.notna(data_inst) else 'N/A'
            msg += f"🔹 *Instalação (PAI)*\n"
            msg += f"   SA: {pai.get('SA', 'N/A')}\n"
            msg += f"   📡 GPON: {pai.get('GPON', 'N/A')}\n"
            msg += f"   👤 Técnico: {pai.get('TECNICO_EXECUTOR', pai.get('TR', 'N/A'))}\n"
            msg += f"   📅 {data_str}\n"
            if pd.notna(pai.get("COD_FECHAMENTO")):
                msg += f"   🔢 Cód. Encerramento: {pai.get('COD_FECHAMENTO')}\n"
            if pd.notna(pai.get("DESCRICAO")):
                desc = str(pai.get("DESCRICAO"))[:80]
                msg += f"   📝 Descrição: {desc}\n"
            msg += "\n"

            for i, (_, filho) in enumerate(filhos.iterrows(), 1):
                data_ab = filho.get("AB_DT")
                data_str = data_ab.strftime('%d/%m/%Y %H:%M') if pd.notna(data_ab) else 'N/A'
                dias = (filho["AB_DT"] - pai["FIM_DT"]).days
                msg += f"🔸 *Reparo filho {i} (após {dias} dias)*\n"
                msg += f"   SA: {filho.get('SA', 'N/A')}\n"
                msg += f"   📡 GPON: {filho.get('GPON', 'N/A')}\n"
                msg += f"   👤 Técnico: {filho.get('TECNICO_EXECUTOR', filho.get('TR', 'N/A'))}\n"
                msg += f"   📅 Abertura: {data_str}\n"
                if pd.notna(filho.get("COD_FECHAMENTO")):
                    msg += f"   🔢 Cód. Encerramento: {filho.get('COD_FECHAMENTO')}\n"
                if pd.notna(filho.get("DESCRICAO")):
                    desc = str(filho.get("DESCRICAO"))[:80]
                    msg += f"   📝 Descrição: {desc}\n"
                msg += "\n"

            msg += "─" * 30 + "\n\n"

            if len(msg) > 4000:
                partes = [msg[i:i+3900] for i in range(0, len(msg), 3900)]
                for parte in partes:
                    await message.reply_text(parte, parse_mode="Markdown")
            else:
                await message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Erro infancia_detalhado_core: {e}", exc_info=True)
        await message.reply_text(f"❌ Erro ao processar: {str(e)}")

# =============================================================================
# HANDLERS DE COMANDOS (mantidos com adição do supervisor)
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if verificar_autenticacao(user_id, context) or verificar_supervisor_autenticado(user_id, context):
        nome = context.user_data.get('nome_supervisor') or extrair_nome_tecnico(context.user_data.get('tecnico')) or user.first_name
        await update.message.reply_text(f"👋 Olá {nome}, você já está autenticado!\n\nUse /menu para começar.")
        return
    
    await update.message.reply_text(
        f"👋 Olá {user.first_name}! Bem-vindo.\n\n"
        f"🔐 Digite sua matrícula (ex: TR818218, TT123456 ou TC004017):"
    )
    context.user_data['aguardando_matricula'] = True

async def supervisor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ativa o modo supervisor"""
    user_id = update.effective_user.id
    
    if verificar_supervisor_autenticado(user_id, context):
        dados = context.user_data
        await update.message.reply_text(
            f"👑 Modo supervisor ativo.\n"
            f"Equipe: {len(dados.get('tecnicos', []))} técnicos.\n"
            f"Use /menu para ver as opções."
        )
        return
    
    if not context.args:
        await update.message.reply_text("❌ Use: /supervisor SEU_PRIMEIRO_NOME\nEx: /supervisor DANIEL")
        return
    
    nome = " ".join(context.args).strip()
    dados = get_dados_equipe_supervisor(nome)
    
    if dados['tecnicos']:
        context.user_data['modo_supervisor'] = True
        context.user_data['nome_supervisor'] = nome
        context.user_data['tecnicos'] = dados['tecnicos']
        context.user_data['nomes_tecnicos'] = dados['nomes_tecnicos']
        context.user_data['setores'] = dados['setores']
        context.user_data['mapa_tecnicos'] = dados['mapa_tecnicos']
        await update.message.reply_text(
            f"👑 Modo supervisor ativado para {nome}.\n"
            f"Equipe: {len(dados['tecnicos'])} técnicos.\n"
            f"Setores: {', '.join(dados['setores'][:3])}...\n\n"
            f"Use /menu para ver as opções."
        )
    else:
        await update.message.reply_text(
            f"⚠️ Supervisor '{nome}' não encontrado na base de presença.\n"
            f"Verifique o nome e tente novamente."
        )

def get_dados_equipe_supervisor(nome_supervisor: str) -> Dict[str, Any]:
    """Busca os técnicos da equipe de um supervisor na planilha de presença"""
    if nome_supervisor in _supervisores_cache:
        return _supervisores_cache[nome_supervisor]
    
    df = carregar_presenca()
    if df is None:
        logger.error("❌ Base de presença não carregada")
        return {'setores': [], 'tecnicos': [], 'nomes_tecnicos': [], 'mapa_tecnicos': {}}
    
    df.columns = [remover_acentos(str(col)).strip().upper() for col in df.columns]
    
    col_sup = next((c for c in df.columns if any(x in c for x in ['SUPERVISOR', 'SUP', 'LIDER'])), None)
    col_setor = next((c for c in df.columns if 'SETOR' in c), None)
    col_func = next((c for c in df.columns if 'FUNCIONARIO' in c or 'NOME' in c), None)
    col_tr = next((c for c in df.columns if c == 'TR'), None)
    col_tt = next((c for c in df.columns if c == 'TT'), None)
    col_tc = next((c for c in df.columns if c == 'TC'), None)
    
    if not col_sup:
        logger.error("❌ Coluna SUPERVISOR não encontrada")
        return {'setores': [], 'tecnicos': [], 'nomes_tecnicos': [], 'mapa_tecnicos': {}}
    
    nome_busca = remover_acentos(nome_supervisor).upper().strip()
    setores, tecnicos, nomes, mapa = set(), [], [], {}
    
    for _, row in df.iterrows():
        sup_val = str(row.get(col_sup, '')).strip()
        if not sup_val:
            continue
        sup_normalizado = remover_acentos(sup_val).upper()
        if any(parte in sup_normalizado for parte in nome_busca.split()):
            if col_setor:
                setor = str(row.get(col_setor, '')).strip()
                if setor:
                    setores.add(setor)
            codigo = None
            if col_tc and pd.notna(row.get(col_tc)):
                codigo = str(row[col_tc]).strip()
            elif col_tr and pd.notna(row.get(col_tr)):
                codigo = str(row[col_tr]).strip()
            elif col_tt and pd.notna(row.get(col_tt)):
                codigo = str(row[col_tt]).strip()
            nome_tec = ''
            if col_func and pd.notna(row.get(col_func)):
                nome_tec = str(row[col_func]).strip()
            if codigo:
                if codigo not in tecnicos:
                    tecnicos.append(codigo)
                if nome_tec and codigo not in mapa:
                    mapa[codigo] = nome_tec
            if nome_tec and nome_tec not in nomes:
                nomes.append(nome_tec)
    
    resultado = {
        'setores': list(setores),
        'tecnicos': tecnicos,
        'nomes_tecnicos': nomes,
        'mapa_tecnicos': mapa
    }
    
    logger.info(f"📊 Supervisor {nome_supervisor}: {len(tecnicos)} técnicos encontrados")
    _supervisores_cache[nome_supervisor] = resultado
    return resultado

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not verificar_autenticacao(user_id, context) and not verificar_supervisor_autenticado(user_id, context):
        await update.message.reply_text("❌ Você não está autenticado. Use /start primeiro.")
        return
    
    is_supervisor = verificar_supervisor_autenticado(user_id, context)
    
    if is_supervisor:
        teclado = [
            [InlineKeyboardButton("📊 Repetidos Equipe", callback_data="sup_repetidos"),
             InlineKeyboardButton("👶 Infância Equipe", callback_data="sup_inf")],
            [InlineKeyboardButton("📋 Atividades Equipe", callback_data="sup_atividades")],
            [InlineKeyboardButton("📅 Presença", callback_data="cmd_presenca")],
            [InlineKeyboardButton("⚙️ Operações", callback_data="menu_operacoes")],
            [InlineKeyboardButton("🆘 Ajuda", callback_data="cmd_ajuda")]
        ]
        titulo = "👑 *BERTA • Central do Supervisor*"
    else:
        teclado = [
            [InlineKeyboardButton("📋 Consultas", callback_data="menu_consultas")],
            [InlineKeyboardButton("📊 Indicadores", callback_data="menu_indicadores")],
            [InlineKeyboardButton("🔍 Detalhamentos", callback_data="menu_detalhes")],
            [InlineKeyboardButton("⚙️ Operações", callback_data="menu_operacoes")],
            [InlineKeyboardButton("📅 Presença", callback_data="cmd_presenca")],
            [InlineKeyboardButton("🆘 Ajuda", callback_data="cmd_ajuda")]
        ]
        titulo = "🤖 *BERTA • Central do Técnico*"
    
    await update.message.reply_text(
        f"{titulo}\n\nEscolha uma categoria:",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_sup = verificar_supervisor_autenticado(user_id, context)
    
    if not is_sup and not verificar_autenticacao(user_id, context):
        await update.message.reply_text("❌ Não autenticado. Use /start.")
        return
    
    if is_sup:
        texto = """
👑 *BERTA • Supervisor*

📊 *Equipe*
• /sup_ativ - Atividades da equipe
• /sup_rep - Repetidos da equipe
• /sup_inf - Infância da equipe

📅 *Presença*
• /presenca - Resumo do mês

⚙️ *Operações*
• /pendencia - Abrir pendência
• /reversa - Gerar PDF de reversa
• /mascaras - Máscaras

🆘 *Sistema*
• /menu - Menu interativo
• /sair - Encerrar sessão
• /cache - Limpar cache
"""
    else:
        texto = """
🤖 *BERTA • Comandos Disponíveis*

📋 *Consultas*
• /minhas - Atividades futuras
• /encerradas - Últimos 30 dias
• /nao_atribuidas - Atividades não atribuídas
• /alarmados - Atividades alarmadas

📊 *Indicadores*
• /repetidos - Taxa de repetição
• /infancia - Taxa de infância
• /p0 - Performance operacional
• /velocidades - Velocidades das atividades futuras

🔍 *Detalhamentos*
• /repetidos_detalhado - Cadeias onde você é o PAI (mês atual)
• /infancia_detalhado - Instalações que geraram infância (mês atual)

⚙️ *Operações*
• /pendencia - Abrir pendência com fotos
• /reversa - Gerar PDF de reversa
• /mascaras - Registrar cancelamento/reagendamento

📅 *Presença*
• /presenca - Resumo do mês

🆘 *Sistema*
• /menu - Menu interativo
• /sair - Encerrar sessão
• /cache - Limpar cache
"""
    await update.message.reply_text(texto, parse_mode="Markdown")

async def sair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("👋 Sessão encerrada.")

async def cache_limpar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    limpar_cache()
    await update.message.reply_text("✅ Cache limpo.")

async def minhas_atividades_core(message, context, ver_todas=False):
    mat = context.user_data.get('matricula_usada')
    nome = extrair_nome_tecnico(context.user_data.get('tecnico'))
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return
    
    df = get_atividades_por_tecnico(codigo_tecnico=mat, nome_tecnico=nome, tipo='futuras')
    if df is None or df.empty:
        await message.reply_text("📭 Nenhuma atividade futura.")
        return
    
    titulo = "TODAS Atividades Futuras" if ver_todas else "Atividades Futuras"
    msg = formatar_atividades(df, titulo, ver_todas=ver_todas)
    
    if len(msg) > 4000:
        for i in range(0, len(msg), 4000):
            await message.reply_text(msg[i:i+4000])
    else:
        await message.reply_text(msg)

async def minhas_encerradas_core(message, context):
    mat = context.user_data.get('matricula_usada')
    nome = extrair_nome_tecnico(context.user_data.get('tecnico'))
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return
    
    df = get_atividades_por_tecnico(codigo_tecnico=mat, nome_tecnico=nome, tipo='encerradas')
    if df is None or df.empty:
        await message.reply_text("📭 Nenhuma atividade encerrada nos últimos 30 dias.")
        return
    
    msg = formatar_atividades(df, "Atividades Encerradas (30 dias)")
    await message.reply_text(msg)

async def nao_atribuidas_core(message, context):
    tecnico = context.user_data.get('tecnico')
    setor = tecnico.get('setor_atual', '')
    df = get_atividades_nao_atribuidas(setor=setor)
    if df is None or df.empty:
        await message.reply_text("📭 Nenhuma atividade não atribuída no seu setor.")
        return
    msg = formatar_atividades(df, "Atividades Não Atribuídas")
    await message.reply_text(msg)

async def alarmados_core(message, context):
    mat = context.user_data.get('matricula_usada')
    nome = extrair_nome_tecnico(context.user_data.get('tecnico'))
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return
    
    await message.reply_text("🔍 Buscando atividades alarmadas...")
    df = get_alarmados_por_tecnico(codigo_tecnico=mat, nome_tecnico=nome)
    if df is None or df.empty:
        await message.reply_text("✅ Nenhuma atividade alarmada encontrada.")
        return
    
    msg = "🚨 *ATIVIDADES ALARMADAS*\n\n"
    for _, row in df.head(20).iterrows():
        msg += f"🔹 SA: {row.get('SA', 'N/A')}\n"
        if 'MACRO' in row:
            msg += f"   Tipo: {row['MACRO']}\n"
        if 'GPON' in row and pd.notna(row['GPON']):
            msg += f"   GPON: {row['GPON']}\n"
        msg += f"   🚨 Alarmado: SIM\n"
        end = formatar_endereco(row)
        if end != 'Endereço não disponível':
            msg += f"   📍 {end}\n"
        msg += f"   Status: {row.get('ESTADO', 'N/A')}\n\n"
        if len(msg) > 3800:
            break
    
    await message.reply_text(msg, parse_mode="Markdown")

async def repetidos_core(message, context):
    mat = context.user_data.get('matricula_usada')
    if not mat:
        tecnico = context.user_data.get('tecnico')
        mat = extrair_codigo_do_tecnico(tecnico) or ''
    
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return
    
    df = carregar_base()
    if df is None:
        await message.reply_text("❌ Base não carregada.")
        return
    
    hoje = datetime.now()
    ind = contar_reparos_repetidos_por_tecnico(df, mat, hoje.month, hoje.year)
    
    if 'erro' in ind:
        await message.reply_text(f"❌ {ind['erro']}")
        return
    
    fonte_label = "🏛️ Fonte: VIP Oficial" if ind.get('fonte') == 'VIP' else "⚙️ Fonte: Cálculo Interno"
    msg = (
        f"📊 *Taxa de Repetição - {ind['periodo']}*\n\n"
        f"🔧 Total reparos: {ind['total_reparos']}\n"
        f"🔄 Reparos repetidos: {ind['reparos_repetidos']}\n"
        f"📈 Taxa: {ind['taxa']}%\n\n"
        f"{fonte_label}"
    )
    await message.reply_text(msg, parse_mode="Markdown")

async def infancia_core(message, context):
    mat = context.user_data.get('matricula_usada')
    if not mat:
        tecnico = context.user_data.get('tecnico')
        mat = extrair_codigo_do_tecnico(tecnico) or ''
    
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return
    
    hoje = datetime.now()
    ind = calcular_infancia_por_tecnico(codigo_tecnico=mat, mes_ref=hoje.month, ano_ref=hoje.year)
    
    if 'erro' in ind:
        await message.reply_text(f"❌ {ind['erro']}")
        return
    
    fonte_label = "🏛️ Fonte: VIP Oficial" if ind.get('fonte') == 'VIP' else "⚙️ Fonte: Cálculo Interno"
    msg = (
        f"📊 *Taxa de Infância - {ind['periodo']}*\n\n"
        f"📦 Total instalações: {ind['total_instalacoes']}\n"
        f"👶 Com infância: {ind['instalacoes_infancia']}\n"
        f"📉 Taxa: {ind['taxa_infancia']}%\n\n"
        f"{fonte_label}"
    )
    await message.reply_text(msg, parse_mode="Markdown")

async def p0_core(message, context):
    mat = context.user_data.get('matricula_usada')
    if not mat:
        tecnico = context.user_data.get('tecnico')
        mat = extrair_codigo_do_tecnico(tecnico) or ''
    
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return
    
    ind = calcular_p0_por_tecnico(mat)
    if 'erro' in ind:
        await message.reply_text(f"❌ {ind['erro']}")
        return
    
    hoje = datetime.now()
    meses_pt = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    periodo = f"{meses_pt[hoje.month-1]}/{hoje.year}"
    
    msg = (
        f"📊 *P0 - Performance Operacional*\n\n"
        f"📅 Período: {periodo}\n\n"
        f"⏰ *P0 10H:* {ind['p0_10']}\n"
        f"🌇 *P0 15H:* {ind['p0_15']}\n"
        f"📆 Total de dias: {ind['total_dias']}\n\n"
        f"💡 *Regras:*\n"
        f"• P0 10H: primeiro encerramento do dia *após* 10:00\n"
        f"• P0 15H: primeiro encerramento da tarde *após* 15:00"
    )
    await message.reply_text(msg, parse_mode="Markdown")

async def velocidades_core(message, context):
    mat = context.user_data.get('matricula_usada')
    nome = extrair_nome_tecnico(context.user_data.get('tecnico', {}))
    if not mat:
        await message.reply_text("❌ Matrícula não encontrada.")
        return
    
    ana = analisar_velocidades_futuras_por_tecnico(mat, nome)
    if 'erro' in ana:
        await message.reply_text(f"❌ {ana['erro']}")
        return
    
    msg = formatar_velocidades_futuras(ana)
    await message.reply_text(msg, parse_mode="Markdown")

async def presenca_core(message, context):
    mat = context.user_data.get('matricula_usada')
    
    df = carregar_base()
    if df is None:
        await message.reply_text("❌ Base não carregada.")
        return
    
    hoje = datetime.now()
    primeiro_dia = datetime(hoje.year, hoje.month, 1)
    
    mask_tec = pd.Series(False, index=df.index)
    if mat and 'TR' in df.columns:
        mask_tec |= df['TR'].astype(str).str.strip().str.upper() == mat.upper()
    
    df_tec = df[mask_tec & (df['DH_FIM_EXEC_REAL'].notna()) & (df['DH_FIM_EXEC_REAL'] >= primeiro_dia)]
    
    if df_tec.empty:
        await message.reply_text("📭 Nenhuma atividade concluída neste mês.")
        return
    
    dias_trabalhados = df_tec['DH_FIM_EXEC_REAL'].dt.date.nunique()
    total_atividades = len(df_tec)
    media = round(total_atividades / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
    
    meses_pt = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    
    msg = (
        f"📅 *Presença — {meses_pt[hoje.month-1]}/{hoje.year}*\n\n"
        f"📊 Dias trabalhados: {dias_trabalhados}\n"
        f"🔧 Atividades concluídas: {total_atividades}\n"
        f"📈 Média diária: {media} ativ/dia"
    )
    await message.reply_text(msg, parse_mode="Markdown")

# =============================================================================
# SALVAR PENDÊNCIA NA PLANILHA (NOVA FUNÇÃO)
# =============================================================================

async def salvar_pendencia_planilha(dados: dict):
    """Envia os dados da pendência para o Google Sheets via Web App."""
    try:
        response = requests.post(URL_SALVAR_PENDENCIA, json=dados, timeout=10)
        if response.status_code == 200 and response.json().get("status") == "ok":
            logger.info("✅ Pendência salva na planilha com sucesso")
        else:
            logger.error(f"❌ Erro ao salvar na planilha: {response.text}")
    except Exception as e:
        logger.error(f"❌ Falha ao enviar para planilha: {e}")

# =============================================================================
# PENDÊNCIA (CONVERSATION HANDLER) — ATUALIZADO COM PLANILHA
# =============================================================================

(ESTADO_FOTOS, ESTADO_TIPO, ESTADO_SUBCAUSA, ESTADO_OBS) = range(4)

async def pendencia_iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not verificar_autenticacao(user_id, context) and not verificar_supervisor_autenticado(user_id, context):
        await update.message.reply_text("❌ Você não está autenticado. Use /start primeiro.")
        return ConversationHandler.END
    
    context.user_data.pop('pendencia_fotos', None)
    context.user_data.pop('aguardando_sa_manual', None)
    context.user_data['pendencia_fotos'] = []
    await update.message.reply_text(
        "📸 Envie uma ou mais fotos do print da atividade.\n"
        "Após enviar todas, digite /continuar para prosseguir."
    )
    return ESTADO_FOTOS

async def pendencia_receber_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'pendencia_fotos' not in context.user_data:
        context.user_data['pendencia_fotos'] = []
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"pend_{update.effective_user.id}_{len(context.user_data['pendencia_fotos'])}.jpg")
    await file.download_to_drive(file_path)
    context.user_data['pendencia_fotos'].append(file_path)
    await update.message.reply_text(f"📸 Foto {len(context.user_data['pendencia_fotos'])} recebida. Envie mais ou /continuar.")
    return ESTADO_FOTOS

async def pendencia_continuar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fotos = context.user_data.get('pendencia_fotos', [])
    if not fotos:
        await update.message.reply_text("❌ Nenhuma foto enviada. Use /pendencia para começar.")
        return ConversationHandler.END
    
    await update.message.reply_text("🔍 Processando a primeira imagem...")
    ocr = extrair_dados_padrao(fotos[0]) if OCR_DISPONIVEL else {"sa": None}
    context.user_data['pendencia_ocr'] = ocr
    sa = ocr.get("sa")
    if not sa:
        await update.message.reply_text("❌ SA não identificado. Digite o número do SA manualmente (ex: SA-31137505 ou 31137505):")
        context.user_data['aguardando_sa_manual'] = True
        return ESTADO_FOTOS
    
    dados_base = get_dados_por_sa(sa)
    if not dados_base:
        await update.message.reply_text(f"❌ SA {sa} não encontrado na base. Digite o SA manualmente:")
        context.user_data['aguardando_sa_manual'] = True
        return ESTADO_FOTOS
    
    context.user_data['pendencia_dados_base'] = dados_base
    context.user_data['pendencia_sa'] = sa
    await update.message.reply_text("📝 Informe o **Tipo de Pendência** (ex: LOCAL FECHADO, SEM CONTATO):", parse_mode='Markdown')
    return ESTADO_TIPO

async def pendencia_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'tecnico' not in context.user_data and not verificar_supervisor_autenticado(update.effective_user.id, context):
        await update.message.reply_text("❌ Sessão expirada. Use /start novamente.")
        return ConversationHandler.END
    tipo = update.message.text.strip()
    context.user_data['pendencia_tipo'] = tipo
    await update.message.reply_text("📝 Informe a **Sub-Causa** (ex: CLIENTE AUSENTE, REPASSE):", parse_mode='Markdown')
    return ESTADO_SUBCAUSA

async def pendencia_subcausa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'tecnico' not in context.user_data and not verificar_supervisor_autenticado(update.effective_user.id, context):
        await update.message.reply_text("❌ Sessão expirada. Use /start novamente.")
        return ConversationHandler.END
    sub = update.message.text.strip()
    context.user_data['pendencia_subcausa'] = sub
    await update.message.reply_text("📝 **Observação** (opcional, digite - para pular):", parse_mode='Markdown')
    return ESTADO_OBS

# Esta função foi atualizada para incluir mais campos e salvar na planilha
async def pendencia_obs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'tecnico' not in context.user_data and not verificar_supervisor_autenticado(update.effective_user.id, context):
        await update.message.reply_text("❌ Sessão expirada. Use /start novamente.")
        return ConversationHandler.END
    obs = update.message.text.strip()
    if obs == '-':
        obs = ''
    context.user_data['pendencia_obs'] = obs
    
    fotos = context.user_data.get('pendencia_fotos', [])
    ocr = context.user_data.get('pendencia_ocr', {})
    base = context.user_data.get('pendencia_dados_base', {})
    tecnico = context.user_data.get('tecnico', {})
    nome_tecnico = extrair_nome_tecnico(tecnico) or context.user_data.get('nome_supervisor', 'Técnico')
    matricula = context.user_data.get('matricula_usada', 'N/A')
    sa = context.user_data.get('pendencia_sa', 'N/A')
    
    # Coleta de informações ampliada
    cliente = ocr.get('nome') or base.get('cliente', 'N/A')
    contato = ocr.get('contato') or base.get('contato', 'N/A')
    gpon = ocr.get('gpon') or base.get('gpon', '')
    atividade = ocr.get('atividade') or base.get('atividade', '')
    endereco = ocr.get('endereco') or base.get('endereco', '')
    setor = tecnico.get('setor_atual', '') or context.user_data.get('setor_supervisor', '')
    municipio = base.get('cidade', '') or ocr.get('cidade', '')
    id_companhia = ocr.get('id_companhia', '') or base.get('id_companhia', '')
    doc_associado = ocr.get('doc_associado', '') or base.get('doc_associado', '')
    
    tipo = context.user_data.get('pendencia_tipo', 'N/A')
    sub = context.user_data.get('pendencia_subcausa', 'N/A')
    obs_final = context.user_data.get('pendencia_obs', '-')
    
    # Monta a máscara completa
    caption = f"""
━━━━━━━━━━━━━━━━━━━━
🚨 MASCARA PENDÊNCIA
━━━━━━━━━━━━━━━━━━━━

Nome Técnico: {nome_tecnico}
Matricula: {matricula}
Setor: {setor or 'N/A'}
Município: {municipio or 'N/A'}
ID Companhia: {id_companhia or 'N/A'}

Tipo de Pendência: {tipo}
Sub-Causa: {sub}
Atividade: {atividade or 'N/A'}

BA/SA: {sa}
DOC ASSOCIADO: {doc_associado or 'N/A'}
Gpon: {gpon or 'N/A'}
Cliente: {cliente}
Contato: {contato}
Endereço: {endereco or 'N/A'}

OBS: {obs_final}

🚨 @DanielOliveiraGA verificar pendência
━━━━━━━━━━━━━━━━━━━━
"""
    grupo_destino = GRUPO_PENDENCIAS_ID
    try:
        for i, fpath in enumerate(fotos):
            with open(fpath, 'rb') as f:
                if i == 0:
                    await context.bot.send_photo(chat_id=grupo_destino, photo=f, caption=caption)
                else:
                    await context.bot.send_photo(chat_id=grupo_destino, photo=f)
        await context.bot.send_message(chat_id=grupo_destino, text="=========================")
    except Exception as e:
        logger.error(f"Erro ao enviar pendência: {e}")
        await update.message.reply_text("❌ Erro ao enviar pendência. Tente novamente.")
        return ConversationHandler.END
    
    # Salvar na planilha
    dados_planilha = {
        "tecnico": nome_tecnico,
        "matricula": matricula,
        "setor": setor,
        "municipio": municipio,
        "id_companhia": id_companhia,
        "tipo": tipo,
        "subcausa": sub,
        "atividade": atividade,
        "sa": sa,
        "doc_associado": doc_associado,
        "gpon": gpon,
        "cliente": cliente,
        "contato": contato,
        "endereco": endereco,
        "obs": obs_final
    }
    await salvar_pendencia_planilha(dados_planilha)
    
    await update.message.reply_text("✅ Pendência enviada com sucesso e registrada na planilha!")
    for fpath in fotos:
        try:
            os.remove(fpath)
        except:
            pass
    return ConversationHandler.END

async def pendencia_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fotos = context.user_data.get('pendencia_fotos', [])
    for fpath in fotos:
        try:
            os.remove(fpath)
        except:
            pass
    await update.message.reply_text("❌ Processo cancelado.")
    return ConversationHandler.END

def extrair_dados_padrao(caminho: str) -> Dict[str, Optional[str]]:
    if not OCR_DISPONIVEL:
        return {"sa": None, "nome": None, "contato": None}
    res = {"sa": None, "nome": None, "contato": None}
    try:
        img = Image.open(caminho)
        w, h = img.size
        area_sa = img.crop((0, 0, w, int(h * 0.18)))
        txt_sa = pytesseract.image_to_string(area_sa, lang='por')
        match = re.search(r'SA[-\s]?(\d+)', txt_sa, re.IGNORECASE)
        if match:
            res["sa"] = f"SA-{match.group(1)}"
        area_nome = img.crop((0, int(h * 0.42), w, int(h * 0.74)))
        txt_nome = pytesseract.image_to_string(area_nome, lang='por')
        linhas = [l.strip() for l in txt_nome.split('\n') if l.strip()]
        if linhas:
            res["nome"] = linhas[0]
        area_tel = img.crop((0, int(h * 0.70), w, int(h * 0.92)))
        txt_tel = pytesseract.image_to_string(area_tel, lang='por')
        mt = re.search(r'(55\d{10,13})|(\d{2}\s?\d{4,5}-?\d{4})|(\d{10,13})', txt_tel)
        if mt:
            res["contato"] = re.sub(r'\D', '', mt.group(0))
    except Exception as e:
        logger.error(f"Erro OCR: {e}")
    return res

def get_dados_por_sa(sa: str) -> Optional[Dict[str, Any]]:
    df = carregar_base()
    if df is None:
        return None
    sa = str(sa).strip().upper()
    if not sa.startswith("SA-"):
        sa = f"SA-{sa}"
    df_sa = df[df['SA'].astype(str).str.strip().str.upper() == sa]
    if df_sa.empty:
        return None
    row = df_sa.iloc[0]
    return {
        'numero_sa': sa,
        'atividade': row.get('MACRO', 'N/A'),
        'gpon': row.get('GPON', 'N/A'),
        'endereco': formatar_endereco(row),
        'cliente': row.get('Cliente', 'N/A'),
        'contato': row.get('Contato', 'N/A'),
    }

# =============================================================================
# SUBMENUS
# =============================================================================

async def menu_consultas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    teclado = [
        [InlineKeyboardButton("📋 Minhas Atividades", callback_data="cmd_minhas")],
        [InlineKeyboardButton("✅ Minhas Encerradas", callback_data="cmd_encerradas")],
        [InlineKeyboardButton("📌 Não Atribuídas", callback_data="cmd_nao_atribuidas")],
        [InlineKeyboardButton("🚨 Alarmados", callback_data="cmd_alarmados")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_principal")]
    ]
    await query.message.reply_text(
        "📋 *CONSULTAS*\n\nEscolha uma opção:",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def menu_indicadores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    teclado = [
        [InlineKeyboardButton("📊 Repetidos", callback_data="cmd_repetidos")],
        [InlineKeyboardButton("👶 Infância", callback_data="cmd_infancia")],
        [InlineKeyboardButton("🚀 Velocidades", callback_data="cmd_velocidades")],
        [InlineKeyboardButton("⏰ P0", callback_data="cmd_p0")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_principal")]
    ]
    await query.message.reply_text(
        "📊 *INDICADORES*\n\nEscolha uma opção:",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def menu_detalhes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    teclado = [
        [InlineKeyboardButton("🔍 Repetidos Detalhado", callback_data="cmd_repetidos_detalhado")],
        [InlineKeyboardButton("👶 Infância Detalhado", callback_data="cmd_infancia_detalhado")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_principal")]
    ]
    await query.message.reply_text(
        "🔍 *DETALHAMENTOS*\n\nEscolha uma opção:",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def menu_operacoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    teclado = [
        [InlineKeyboardButton("🛠️ Abrir Pendência", callback_data="cmd_pendencia")],
        [InlineKeyboardButton("🔁 Reversa", callback_data="cmd_reversa")],
        [InlineKeyboardButton("🔄 Máscaras", callback_data="cmd_mascaras")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_principal")]
    ]
    await query.message.reply_text(
        "⚙️ *OPERAÇÕES*\n\nEscolha uma opção:",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

# =============================================================================
# CALLBACK HANDLER
# =============================================================================

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    message = query.message
    
    if data == "menu_principal":
        await menu(update, context)
        return
    elif data == "menu_consultas":
        await menu_consultas(update, context)
        return
    elif data == "menu_indicadores":
        await menu_indicadores(update, context)
        return
    elif data == "menu_detalhes":
        await menu_detalhes(update, context)
        return
    elif data == "menu_operacoes":
        await menu_operacoes(update, context)
        return
    
    # Comandos diretos via callback
    if data == "cmd_pendencia":
        await pendencia_iniciar(update, context)
        return
    elif data == "cmd_reversa":
        await reversa_core(message, context)
        return
    elif data == "cmd_mascaras":
        await mascaras_core(message, context)
        return
    
    comandos = {
        "cmd_minhas": lambda: minhas_atividades_core(message, context, False),
        "cmd_encerradas": lambda: minhas_encerradas_core(message, context),
        "cmd_nao_atribuidas": lambda: nao_atribuidas_core(message, context),
        "cmd_alarmados": lambda: alarmados_core(message, context),
        "cmd_repetidos": lambda: repetidos_core(message, context),
        "cmd_repetidos_detalhado": lambda: repetidos_detalhado_core(message, context),
        "cmd_infancia": lambda: infancia_core(message, context),
        "cmd_infancia_detalhado": lambda: infancia_detalhado_core(message, context),
        "cmd_p0": lambda: p0_core(message, context),
        "cmd_velocidades": lambda: velocidades_core(message, context),
        "cmd_presenca": lambda: presenca_core(message, context),
        "cmd_ajuda": lambda: ajuda(update, context),
    }
    
    if data in comandos:
        await comandos[data]()
    elif data.startswith("sup_"):
        await message.reply_text("⚠️ Comando supervisor em desenvolvimento.")
    elif data.startswith("cmd_"):
        await message.reply_text(f"⚠️ Comando {data} em desenvolvimento.")
    else:
        await message.reply_text("❌ Opção não implementada.")

# =============================================================================
# MESSAGE HANDLER
# =============================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if context.user_data.get('aguardando_matricula'):
        mat = text.upper()
        if not re.match(r'^(TR|TT|TC)\d+$', mat):
            await update.message.reply_text("❌ Formato inválido. Ex: TR818218")
            return
        
        tec = await autenticar_tecnico(user_id, mat)
        if tec:
            context.user_data['tecnico'] = tec
            context.user_data['matricula_usada'] = mat
            context.user_data.pop('aguardando_matricula', None)
            nome = extrair_nome_tecnico(tec) or update.effective_user.first_name
            await update.message.reply_text(
                f"✅ Autenticado!\n👤 Técnico: {nome}\n🆔 Matrícula: {mat}\n\nUse /menu para começar.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Matrícula {mat} não encontrada.")
        return
    
    if not verificar_autenticacao(user_id, context) and not verificar_supervisor_autenticado(user_id, context):
        await update.message.reply_text("❌ Não autenticado. Use /start.")
        return
    
    comandos_texto = {
        '/menu': lambda: menu(update, context),
        '/minhas': lambda: minhas_atividades_core(update.message, context, False),
        '/encerradas': lambda: minhas_encerradas_core(update.message, context),
        '/nao_atribuidas': lambda: nao_atribuidas_core(update.message, context),
        '/alarmados': lambda: alarmados_core(update.message, context),
        '/repetidos': lambda: repetidos_core(update.message, context),
        '/repetidos_detalhado': lambda: repetidos_detalhado_core(update.message, context),
        '/infancia': lambda: infancia_core(update.message, context),
        '/infancia_detalhado': lambda: infancia_detalhado_core(update.message, context),
        '/p0': lambda: p0_core(update.message, context),
        '/velocidades': lambda: velocidades_core(update.message, context),
        '/reversa': lambda: reversa_core(update.message, context),
        '/mascaras': lambda: mascaras_core(update.message, context),
        '/presenca': lambda: presenca_core(update.message, context),
        '/ajuda': lambda: ajuda(update, context),
        '/sair': lambda: sair(update, context),
        '/cache': lambda: cache_limpar(update, context),
    }
    
    if text.lower() in comandos_texto:
        await comandos_texto[text.lower()]()
    else:
        await update.message.reply_text("ℹ️ Comando não reconhecido. Use /menu.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erro: {context.error}")
    try:
        await update.effective_message.reply_text("❌ Erro interno. Tente novamente.")
    except:
        pass

# =============================================================================
# MAIN
# =============================================================================

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Comandos gerais
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("supervisor", supervisor_cmd))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("sair", sair))
    app.add_handler(CommandHandler("cache", cache_limpar))
    
    # Comandos de consulta
    app.add_handler(CommandHandler("minhas", lambda u, c: minhas_atividades_core(u.message, c, False)))
    app.add_handler(CommandHandler("encerradas", lambda u, c: minhas_encerradas_core(u.message, c)))
    app.add_handler(CommandHandler("nao_atribuidas", lambda u, c: nao_atribuidas_core(u.message, c)))
    app.add_handler(CommandHandler("alarmados", lambda u, c: alarmados_core(u.message, c)))
    
    # Comandos de indicadores
    app.add_handler(CommandHandler("repetidos", lambda u, c: repetidos_core(u.message, c)))
    app.add_handler(CommandHandler("repetidos_detalhado", lambda u, c: repetidos_detalhado_core(u.message, c)))
    app.add_handler(CommandHandler("infancia", lambda u, c: infancia_core(u.message, c)))
    app.add_handler(CommandHandler("infancia_detalhado", lambda u, c: infancia_detalhado_core(u.message, c)))
    app.add_handler(CommandHandler("p0", lambda u, c: p0_core(u.message, c)))
    app.add_handler(CommandHandler("velocidades", lambda u, c: velocidades_core(u.message, c)))
    
    # Comandos de operações
    app.add_handler(CommandHandler("reversa", lambda u, c: reversa_core(u.message, c)))
    app.add_handler(CommandHandler("mascaras", lambda u, c: mascaras_core(u.message, c)))
    
    # Comando de presença
    app.add_handler(CommandHandler("presenca", lambda u, c: presenca_core(u.message, c)))
    
    # Pendência (ConversationHandler)
    pendencia_conv = ConversationHandler(
        entry_points=[CommandHandler("pendencia", pendencia_iniciar)],
        states={
            ESTADO_FOTOS: [
                MessageHandler(filters.PHOTO, pendencia_receber_foto),
                CommandHandler("continuar", pendencia_continuar)
            ],
            ESTADO_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pendencia_tipo)],
            ESTADO_SUBCAUSA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pendencia_subcausa)],
            ESTADO_OBS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pendencia_obs)],
        },
        fallbacks=[CommandHandler("cancelar", pendencia_cancelar)],
    )
    app.add_handler(pendencia_conv)
    
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("="*60)
    print("🤖 BERTA BOT - VERSÃO 10.76 + OPERAÇÕES + SUPERVISOR + PLANILHA")
    print("✅ Repetidos: apenas cadeias com 2º reparo no mês atual, PAI, exibe GPON")
    print("✅ Infância: apenas instalações com 1º reparo filho no mês atual")
    print("✅ Operações: Pendência (OCR), Reversa, Máscaras")
    print("✅ Supervisor: /supervisor NOME")
    print("✅ Pendência salva automaticamente na planilha Google Sheets")
    print("="*60)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
