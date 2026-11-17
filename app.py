import os
import io
import uuid
import hashlib
import secrets
import time
import unicodedata
import json
from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib.parse import quote

import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from sqlalchemy import (
    create_engine, Column, String, Text, Date, DateTime, LargeBinary,
    ForeignKey, Boolean, select, desc, func, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.engine import URL
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, HRFlowable
from reportlab.lib.units import cm
from xml.sax.saxutils import escape

# ---------------------------------------------------------------------
# CONFIGURAÇÃO & DESIGN SYSTEM (UX/UI ROXO & BRANCO)
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Portal de Autorizações",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def inject_custom_css():
    """Tema claro fixo: superfícies brancas e texto azul-escuro em todos os campos."""
    st.markdown("""
    <style>
    :root { color-scheme:light; --navy:#172B4D; --muted:#52647B; --line:#DCE3EE; --purple:#6D28D9; --pale:#F6F2FF; }
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
      background:#FFFFFF!important;color:var(--navy)!important;color-scheme:light!important;
    }
    .stApp {background:linear-gradient(125deg,#FAF8FF 0%,#FFFFFF 26%,#FFFFFF 80%,#FAF8FF 100%)!important;}
    [data-testid="stMarkdownContainer"] p,[data-testid="stWidgetLabel"] p,
    [data-testid="stCaptionContainer"] p,.stApp h1,.stApp h2,.stApp h3,.stApp h4,
    .stApp label {color:var(--navy)!important;-webkit-text-fill-color:var(--navy)!important;}
    [data-testid="stCaptionContainer"] p {color:var(--muted)!important;-webkit-text-fill-color:var(--muted)!important;}
    [data-testid="stVerticalBlockBorderWrapper"] {
      background:#FFFFFF!important;border:1px solid var(--line)!important;
      border-radius:12px!important;padding:1.05rem!important;box-shadow:none!important;
    }
    /* Os seletores abrangem o input interno e o wrapper do BaseWeb. */
    .stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"],
    .stApp [data-baseweb="textarea"],.stApp [data-baseweb="select"],
    .stApp [data-baseweb="select"]>div,.stApp input,.stApp textarea,
    .stApp select,.stApp input:disabled,.stApp textarea:disabled {
      background-color:#FFFFFF!important;color:var(--navy)!important;
      -webkit-text-fill-color:var(--navy)!important;
      border-color:#CBD5E1!important;color-scheme:light!important;
    }
    .stApp input,.stApp textarea,.stApp [data-baseweb="select"] span,
    .stApp [data-baseweb="select"] div,.stApp [data-baseweb="input"] div,
    .stApp [data-baseweb="base-input"] div {
      color:var(--navy)!important;-webkit-text-fill-color:var(--navy)!important;
    }
    .stApp input::placeholder,.stApp textarea::placeholder {
      color:#718096!important;-webkit-text-fill-color:#718096!important;
    }
    .stApp input:focus,.stApp textarea:focus,.stApp [data-baseweb="select"]:focus-within {
      border-color:var(--purple)!important;outline-color:var(--purple)!important;
    }
    [data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"],
    [data-baseweb="calendar"] {background:#FFFFFF!important;color:var(--navy)!important;color-scheme:light!important;}
    [data-baseweb="popover"] *,[data-baseweb="menu"] *,[role="listbox"] *,
    [data-baseweb="calendar"] * {color:var(--navy)!important;-webkit-text-fill-color:var(--navy)!important;}
    [role="option"]:hover,[role="option"][aria-selected="true"] {background:var(--pale)!important;}
    .stTabs [data-baseweb="tab-list"] {background:transparent!important;gap:.35rem;}
    .stTabs [data-baseweb="tab"] {color:var(--muted)!important;border-radius:8px!important;}
    .stTabs [aria-selected="true"] {background:var(--pale)!important;}
    .stTabs [aria-selected="true"] * {color:#5B21B6!important;}
    .stButton button[kind="primary"],.stFormSubmitButton button[kind="primary"] {
      background:var(--purple)!important;color:#FFFFFF!important;border:0!important;border-radius:8px!important;
    }
    .stButton button[kind="primary"] *, .stFormSubmitButton button[kind="primary"] * {color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;}
    .stButton button[kind="secondary"],.stFormSubmitButton button[kind="secondary"],
    .stDownloadButton button {background:#FFFFFF!important;color:var(--navy)!important;
      border:1px solid var(--line)!important;border-radius:8px!important;}
    .stButton button[kind="secondary"] *, .stFormSubmitButton button[kind="secondary"] *,
    .stDownloadButton button * {color:var(--navy)!important;-webkit-text-fill-color:var(--navy)!important;}
    [data-testid="stMetric"] {background:#FFFFFF!important;
      border:1px solid #ECE5FF!important;border-radius:10px!important;padding:12px;}
    [data-testid="stMetric"] * {color:var(--navy)!important;-webkit-text-fill-color:var(--navy)!important;}
    [data-testid="stExpander"] summary,[data-testid="stSidebar"] {background:#FFFFFF!important;}
    [data-testid="stExpander"] summary * {color:var(--navy)!important;}
    .hero-banner {background:#FFFFFF!important;border:0;
      padding:1.1rem .25rem;border-radius:12px;margin-bottom:1rem;}
    .hero-banner h1 {color:var(--navy)!important;font-size:1.5rem!important;margin:0 0 .3rem!important;}
    .hero-banner p {color:var(--muted)!important;margin:0!important;}
    .status-badge {display:inline-block;padding:4px 10px;border-radius:999px;font-size:.78rem;font-weight:600;}
    .status-active {background:#EDE9FE;color:#5B21B6!important;}
    .status-inactive {background:#E2E8F0;color:#334155!important;}
    .step-header {display:flex;align-items:center;gap:10px;margin-bottom:.75rem;
      padding-bottom:.5rem;border-bottom:1px solid var(--line);}
    .step-number {background:#F1EBFF;color:#5B21B6!important;width:28px;height:28px;
      border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;}
    .step-title {font-size:1.05rem;font-weight:650;color:var(--navy)!important;margin:0;}
    .event-info-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:.75rem 0;background:#F8F5FF!important;border:1px solid #EDE9FE!important;border-radius:12px;padding:1rem;}
    .event-info-item span {display:block;font-size:.75rem;text-transform:uppercase;color:#5B21B6!important;font-weight:600;}
    .event-info-item strong {color:var(--navy)!important;}
    .signature-box-hint {background:#F8F5FF;border-radius:8px;padding:.65rem 1rem;color:var(--navy)!important;margin-bottom:.5rem;}
    .signature-box-hint strong {color:var(--navy)!important;}
    [data-testid="stAlert"] {border-radius:10px!important;}
    [data-testid="stAlert"]:has([data-testid="stAlertContentError"]),
    [data-testid="stAlert"]:has([data-testid="stAlertIconError"]) {background:#FEF2F2!important;}
    [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]),
    [data-testid="stAlert"]:has([data-testid="stAlertIconWarning"]) {background:#FFFBEB!important;}
    [data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]),
    [data-testid="stAlert"]:has([data-testid="stAlertIconInfo"]) {background:#F5F3FF!important;}
    [data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]),
    [data-testid="stAlert"]:has([data-testid="stAlertIconSuccess"]) {background:#ECFDF5!important;}
    [data-testid="stAlert"]:has([data-testid="stAlertContentError"]) *,
    [data-testid="stAlert"]:has([data-testid="stAlertIconError"]) * {color:#991B1B!important;-webkit-text-fill-color:#991B1B!important;}
    [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) *,
    [data-testid="stAlert"]:has([data-testid="stAlertIconWarning"]) * {color:#92400E!important;-webkit-text-fill-color:#92400E!important;}
    [data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) *,
    [data-testid="stAlert"]:has([data-testid="stAlertIconInfo"]) * {color:#4C1D95!important;-webkit-text-fill-color:#4C1D95!important;}
    [data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) *,
    [data-testid="stAlert"]:has([data-testid="stAlertIconSuccess"]) * {color:#065F46!important;-webkit-text-fill-color:#065F46!important;}
    .login-intro {text-align:center;margin:2rem auto 1.25rem;}
    .login-symbol {width:58px;height:58px;border-radius:16px;background:#F3EEFF;display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;color:#6D28D9;}
    .login-intro h1 {font-size:1.65rem;color:var(--navy)!important;margin:.2rem 0 .4rem;}
    .login-intro p {color:var(--muted)!important;font-size:.92rem;}
    .login-footer {text-align:center;color:#64748B!important;font-size:.79rem;margin-top:1rem;}
    .section-intro h1 {font-size:1.65rem;color:var(--navy)!important;margin-bottom:.2rem;}
    .section-intro p {color:var(--muted)!important;margin-bottom:.65rem;font-size:.91rem;}
    .section-intro h1 {font-size:1.4rem!important;margin-bottom:.12rem!important;}
    .admin-kpi-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:.4rem 0 .85rem;}
    .admin-kpi {background:#fff;border:1px solid #E9DFFF;border-radius:11px;padding:12px 14px;min-width:0;}
    .admin-kpi-label {font-size:.83rem;color:#52647B!important;line-height:1.3;}
    .admin-kpi-value {font-size:1.75rem;font-weight:700;line-height:1.2;margin-top:4px;color:#172B4D!important;}
    .parent-intro {text-align:center;padding:5rem 0 0.8rem;}
    .parent-intro h1 {
    font-size: 1.35rem !important;
    font-weight: 700;
    line-height: 1.3;
    margin: .5rem 0 .4rem !important;
}

.parent-intro p {
    font-size: .88rem !important;
    line-height: 1.45;
    color: #52647B !important;
    max-width: 330px;
    margin: 0 auto !important;
}

.parent-icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
}
    .event-guidance {background:#F8F5FF;border:1px solid #EDE9FE;border-radius:9px;padding:.85rem 1rem;color:var(--navy)!important;margin:.7rem 0;}
    .event-guidance strong {color:var(--navy)!important;}
    .signature-area {max-width:100%;overflow-x:auto;}
    [data-testid="stSidebar"] {border-right:1px solid #E2E8F0!important;}
    [data-testid="stSidebar"] [data-testid="stAlert"] {border-radius:8px!important;}
    @media(max-width:700px) {.hero-banner{padding:1.1rem!important;}.hero-banner h1{font-size:1.25rem!important;}
      [data-testid="stVerticalBlockBorderWrapper"]{padding:.75rem!important;}}
    /* Layout responsivo: evitar overflow e garantir largura legível */
    [data-testid="stMainBlockContainer"] {
      max-width:1120px!important;
      padding-top:1.25rem!important;
      padding-left:clamp(.75rem,3vw,2rem)!important;
      padding-right:clamp(.75rem,3vw,2rem)!important;
    }
    .stApp [data-testid="stDataFrame"],.stApp [data-testid="stTable"],
    .stApp [data-testid="stCodeBlock"] {max-width:100%;overflow-x:auto;}
    .stApp [data-testid="stFileUploader"],.stApp [data-testid="stDateInput"],
    .stApp [data-testid="stSelectbox"],.stApp [data-testid="stTextInput"],
    .stApp [data-testid="stTextArea"] {color-scheme:light!important;}
    .stApp [data-baseweb="button"],.stApp button {min-height:42px;}
    .stApp [data-testid="stCanvas"] {max-width:100%;}
    .stApp [data-testid="stWidgetLabel"] {font-weight:550;}
    @media (max-width: 700px) {
    .parent-intro {
        padding: .3rem 0 .7rem !important;
    }

    .parent-intro h1 {
        font-size: 1.25rem !important;
    }

    .parent-intro p {
        font-size: .85rem !important;
    }
}
      .event-info-grid {grid-template-columns:1fr!important;gap:.65rem!important;}
      .stApp [data-testid="stHorizontalBlock"] {flex-wrap:wrap!important;}
      .stApp [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width:min(100%,250px)!important;flex:1 1 100%!important;
      }
      .stTabs [data-baseweb="tab-list"] {overflow-x:auto;flex-wrap:nowrap;}
      .stTabs [data-baseweb="tab"] {white-space:nowrap;}
      .login-intro {margin:.6rem auto 1rem!important;}
      .section-intro h1 {font-size:1.2rem!important;}
      .section-intro p {font-size:.82rem!important;margin-bottom:.45rem!important;}
      .admin-kpi-grid {gap:7px;margin:.25rem 0 .6rem;}
      .admin-kpi {padding:9px 7px;border-radius:9px;text-align:center;}
      .admin-kpi-label {font-size:.69rem;line-height:1.2;}
      .admin-kpi-value {font-size:1.4rem;margin-top:5px;}
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ---------------------------------------------------------------------
# BANCO DE DADOS & VARIÁVEIS DE AMBIENTE (INALTERADOS)
# ---------------------------------------------------------------------
def setting(name, default=""):
    """Environment variables take precedence; Streamlit secrets work in the cloud."""
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    try:
        return str(st.secrets[name])
    except (KeyError, FileNotFoundError, AttributeError):
        return default


DATABASE_URL = setting("DATABASE_URL", "sqlite:///autorizacoes.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

ADMIN_PASSWORD_HASH = setting("ADMIN_PASSWORD_HASH")
SESSION_TIMEOUT_SECONDS = 20 * 60
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCK_SECONDS = 5 * 60
APP_BASE_URL = setting("APP_BASE_URL", "").rstrip("/")
CONTROLLER_NAME = setting("CONTROLLER_NAME", "Comunidade / organização responsável")
CONTROLLER_EMAIL = setting("CONTROLLER_EMAIL", "Informe o e-mail de contato")
PRIVACY_URL = setting("PRIVACY_URL", "")
RETENTION_NOTICE = setting(
    "RETENTION_NOTICE",
    "Os dados serão mantidos somente pelo período necessário para cumprir as finalidades da autorização e obrigações legais aplicáveis."
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


class Event(Base):
    __tablename__ = "events"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(180), nullable=False)
    destination = Column(String(180), nullable=False)
    description = Column(Text, default="")
    event_date = Column(Date, nullable=False)
    departure_time = Column(String(20), default="")
    return_time = Column(String(20), default="")
    meeting_point = Column(String(250), default="")
    responsible_name = Column(String(180), default="")
    responsible_phone = Column(String(60), default="")
    emergency_phone = Column(String(60), default="")
    active = Column(Boolean, default=True, nullable=False)
    public_token = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    authorizations = relationship("Authorization", back_populates="event", cascade="all, delete-orphan")


class Authorization(Base):
    __tablename__ = "authorizations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    child_name = Column(String(180), nullable=False)
    child_name_key = Column(String(180), nullable=False)
    child_birthdate = Column(Date, nullable=False)
    parent_name = Column(String(180), nullable=False)
    cell_leader_name = Column(String(180), nullable=True)
    parent_document = Column(String(40), nullable=False)
    parent_phone = Column(String(60), nullable=False)
    parent_email = Column(String(180), default="")
    relationship_to_child = Column(String(60), nullable=False)
    emergency_contact = Column(String(180), nullable=False)
    emergency_phone = Column(String(60), nullable=False)
    health_notes = Column(Text, default="")
    consent_text_version = Column(String(30), default="1.0")
    privacy_accepted = Column(Boolean, default=False, nullable=False)
    declaration_accepted = Column(Boolean, default=False, nullable=False)
    signature_png = Column(LargeBinary, nullable=False)
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    event = relationship("Event", back_populates="authorizations")


class AuthorizationDraft(Base):
    __tablename__ = "authorization_drafts"
    token_hash = Column(String(64), primary_key=True)
    event_id = Column(String(36), nullable=False)
    encrypted_data = Column(LargeBinary, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


@st.cache_resource(show_spinner=False)
def initialize_database(_engine):
    # Verifica/cria apenas tabelas ausentes, uma vez por processo.
    # Não exclui nem altera registros existentes.
    Base.metadata.create_all(_engine)
    # Migração segura para instalações existentes, sem perder autorizações.
    with _engine.begin() as connection:
        if _engine.dialect.name == "postgresql":
            connection.execute(text("ALTER TABLE authorizations ADD COLUMN IF NOT EXISTS cell_leader_name VARCHAR(180)"))
        elif _engine.dialect.name == "sqlite":
            columns = [row[1] for row in connection.exec_driver_sql("PRAGMA table_info(authorizations)")]
            if "cell_leader_name" not in columns:
                connection.exec_driver_sql("ALTER TABLE authorizations ADD COLUMN cell_leader_name VARCHAR(180)")
    # Remover a restricao antiga no Neon/PostgreSQL sem apagar registros.
    # create_all nao remove restricoes de tabelas ja existentes.
    if _engine.dialect.name == "postgresql":
        with _engine.begin() as connection:
            connection.execute(text(
                'ALTER TABLE authorizations DROP CONSTRAINT IF EXISTS uq_auth_event_child_birthdate'
            ))
    return True

initialize_database(engine)


def db_session():
    return SessionLocal()


# Rascunhos são criptografados no PostgreSQL e identificados por token aleatório.
# O token permanece na URL para permitir restaurar após atualizar a página.
DRAFT_FIELDS = (
    "child_name", "child_birthdate", "parent_name", "cell_leader_name", "parent_document", "relationship",
    "parent_phone", "parent_email", "emergency_contact", "emergency_phone",
    "health_notes", "declaration", "privacy"
)
DRAFT_KEY = setting("DRAFT_ENCRYPTION_KEY")
try:
    DRAFT_CIPHER = Fernet(DRAFT_KEY.encode()) if DRAFT_KEY else None
except (ValueError, TypeError):
    DRAFT_CIPHER = None
DRAFT_TTL_SECONDS = 24 * 60 * 60


def init_parent_draft(event_id):
    if not DRAFT_CIPHER:
        return None
    draft_token = st.query_params.get("draft", "")
    if len(draft_token) < 40 or len(draft_token) > 100:
        draft_token = secrets.token_urlsafe(32)
        st.query_params["draft"] = draft_token
    token_hash = hashlib.sha256(draft_token.encode()).hexdigest()
    session_key = f"loaded_draft_{event_id}"
    if st.session_state.get(session_key) != token_hash:
        with db_session() as db:
            row = db.get(AuthorizationDraft, token_hash)
            if row and row.event_id == event_id and (datetime.utcnow() - row.updated_at).total_seconds() <= DRAFT_TTL_SECONDS:
                try:
                    data = json.loads(DRAFT_CIPHER.decrypt(row.encrypted_data).decode())
                    for field in DRAFT_FIELDS:
                        key = f"draft_{event_id}_{field}"
                        if field in data:
                            st.session_state[key] = date.fromisoformat(data[field]) if field == "child_birthdate" else data[field]
                except (InvalidToken, ValueError, TypeError):
                    pass
        st.session_state[session_key] = token_hash
    return token_hash


def save_parent_draft(event_id, token_hash):
    if not DRAFT_CIPHER or not token_hash:
        return
    data = {}
    for field in DRAFT_FIELDS:
        value = st.session_state.get(f"draft_{event_id}_{field}")
        if value is not None:
            data[field] = value.isoformat() if isinstance(value, date) else value
    encrypted = DRAFT_CIPHER.encrypt(json.dumps(data, ensure_ascii=False).encode())
    with db_session() as db:
        row = db.get(AuthorizationDraft, token_hash)
        if row and row.event_id != event_id:
            return
        if row:
            row.encrypted_data = encrypted
            row.updated_at = datetime.utcnow()
        else:
            db.add(AuthorizationDraft(token_hash=token_hash, event_id=event_id,
                                      encrypted_data=encrypted, updated_at=datetime.utcnow()))
        db.commit()


def delete_parent_draft(token_hash):
    if token_hash:
        with db_session() as db:
            row = db.get(AuthorizationDraft, token_hash)
            if row:
                db.delete(row)
                db.commit()
    if "draft" in st.query_params:
        del st.query_params["draft"]


def normalize_child_name(value):
    """Normaliza nome para comparar duplicidade sem diferenciar caixa, acentos ou espaços extras."""
    value = unicodedata.normalize("NFKD", value.strip().casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.split())


def verify_admin_password(password):
    """Verifica hash PBKDF2 configurado em ADMIN_PASSWORD_HASH."""
    try:
        algorithm, iterations, salt_hex, expected_hex = ADMIN_PASSWORD_HASH.split("$", 3)
        if algorithm != "pbkdf2_sha256" or not 100_000 <= int(iterations) <= 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        ).hex()
        return secrets.compare_digest(actual, expected_hex)
    except (ValueError, TypeError):
        return False


def admin_logged_in():
    if not ADMIN_PASSWORD_HASH or not st.session_state.get("admin_ok", False):
        return False
    last_activity = st.session_state.get("admin_last_activity", 0)
    if time.time() - last_activity > SESSION_TIMEOUT_SECONDS:
        st.session_state.admin_ok = False
        st.session_state.pop("admin_last_activity", None)
        st.warning("Sua sessão expirou por segurança. Entre novamente.")
        return False
    st.session_state.admin_last_activity = time.time()
    return True


def make_public_url(token):
    if APP_BASE_URL:
        return f"{APP_BASE_URL}/?page=parent&token={quote(token)}"
    return f"http://localhost:8502/?page=parent&token={quote(token)}"


def signed_at_brasilia(value, with_seconds=True):
    """Converte timestamps UTC (inclusive registros antigos sem timezone) para Brasilia."""
    if value is None:
        return "Data nao informada"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    local = value.astimezone(ZoneInfo("America/Sao_Paulo"))
    return local.strftime("%d/%m/%Y às %H:%M:%S" if with_seconds else "%d/%m/%Y %H:%M")


def pdf_bytes(auth):
    with db_session() as db:
        event = db.get(Event, auth.event_id)
    if event is None:
        raise ValueError("Evento não encontrado para esta autorização.")
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.7*cm, bottomMargin=1.7*cm
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=16, leading=20))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.grey))
    story = [
        Paragraph("AUTORIZAÇÃO PARA PARTICIPAÇÃO EM ATIVIDADE", styles["CenterTitle"]),
        Spacer(1, 10),
        Paragraph(f"<b>Evento:</b> {escape(event.title)}", styles["BodyText"]),
        Paragraph(f"<b>Destino:</b> {escape(event.destination)}", styles["BodyText"]),
        Paragraph(f"<b>Data:</b> {event.event_date.strftime('%d/%m/%Y')}", styles["BodyText"]),
        Paragraph(f"<b>Saída:</b> {escape(event.departure_time or 'Não informado')} &nbsp;&nbsp; <b>Retorno:</b> {escape(event.return_time or 'Não informado')}", styles["BodyText"]),
        Paragraph(f"<b>Ponto de encontro:</b> {escape(event.meeting_point or 'Não informado')}", styles["BodyText"]),
        Spacer(1, 12),
        HRFlowable(width="100%", color=colors.lightgrey),
        Spacer(1, 10),
        Paragraph("<b>IDENTIFICAÇÃO DO PARTICIPANTE</b>", styles["Heading2"]),
        Paragraph(f"Nome: {escape(auth.child_name)}", styles["BodyText"]),
        Paragraph(f"Data de nascimento: {auth.child_birthdate.strftime('%d/%m/%Y')}", styles["BodyText"]),
        Spacer(1, 8),
        Paragraph("<b>IDENTIFICAÇÃO DO(A) RESPONSÁVEL</b>", styles["Heading2"]),
        Paragraph(f"Nome: {escape(auth.parent_name)}", styles["BodyText"]),
        Paragraph(f"Líder de célula: {escape(auth.cell_leader_name or 'Não informado')}", styles["BodyText"]),
        Paragraph(f"Documento informado: {escape(auth.parent_document)}", styles["BodyText"]),
        Paragraph(f"Telefone: {escape(auth.parent_phone)}", styles["BodyText"]),
        Paragraph(f"E-mail: {escape(auth.parent_email or 'Não informado')}", styles["BodyText"]),
        Paragraph(f"Vínculo com o participante: {escape(auth.relationship_to_child)}", styles["BodyText"]),
        Spacer(1, 8),
        Paragraph("<b>CONTATO PARA EMERGÊNCIA</b>", styles["Heading2"]),
        Paragraph(f"Nome: {escape(auth.emergency_contact)}", styles["BodyText"]),
        Paragraph(f"Telefone: {escape(auth.emergency_phone)}", styles["BodyText"]),
        Spacer(1, 8),
        Paragraph("<b>INFORMAÇÕES IMPORTANTES</b>", styles["Heading2"]),
        Paragraph(escape(auth.health_notes or "Nenhuma informação adicional informada."), styles["BodyText"]),
        Spacer(1, 12),
        Paragraph(
            f"Eu, {escape(auth.parent_name)}, na qualidade de {escape(auth.relationship_to_child)}, "
            f"declaro ser responsável legal pelo participante menor de 18 anos identificado acima e AUTORIZO sua "
            f"participação no evento descrito neste documento. Declaro que as informações fornecidas são verdadeiras "
            f"e que estou ciente dos dados de data, destino e organização apresentados nesta autorização.",
            styles["BodyText"]
        ),
        Spacer(1, 8),
        Paragraph(f"<b>Assinatura eletrônica:</b> {escape(auth.parent_name)}", styles["BodyText"]),
    ]
    try:
        sig = Image.open(io.BytesIO(auth.signature_png)).convert("RGBA")
        sig_io = io.BytesIO()
        sig.save(sig_io, format="PNG")
        sig_io.seek(0)
        story += [Spacer(1, 4), RLImage(sig_io, width=7*cm, height=2.2*cm, kind="proportional")]
    except Exception:
        story.append(Paragraph("Assinatura manuscrita capturada digitalmente.", styles["BodyText"]))
    story += [
        Paragraph(f"Assinado em: {signed_at_brasilia(auth.signed_at)} (horário de Brasília)", styles["Small"]),
        Spacer(1, 10),
        Paragraph(f"<b>Responsável pela atividade:</b> {escape(event.responsible_name or 'Não informado')}", styles["BodyText"]),
        Paragraph(f"<b>Contato da organização:</b> {escape(event.responsible_phone or 'Não informado')}", styles["BodyText"]),
        Spacer(1, 14),
        Paragraph("REGISTRO DIGITAL — guarde este documento como comprovante da autorização.", styles["Small"]),
    ]
    doc.build(story)
    return buffer.getvalue()


# ---------------------------------------------------------------------
# TELAS (UX/UI REDESIGN)
# ---------------------------------------------------------------------
def login_screen():
    _, col_center, _ = st.columns([1, 1.35, 1])
    with col_center:
        st.markdown("""
        <div class="login-intro">
            <div class="login-symbol">
                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/></svg>
            </div>
            <h1>Portal de Autorizações</h1>
            <p>Gestão de autorizações para passeios e atividades</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            if not ADMIN_PASSWORD_HASH:
                st.error("A senha administrativa não foi configurada. Gere um hash e defina ADMIN_PASSWORD_HASH nas variáveis secretas da hospedagem.")
                return

            locked_until = st.session_state.get("login_locked_until", 0)
            remaining = int(locked_until - time.time())
            if remaining > 0:
                st.error(f"Muitas tentativas. Aguarde {remaining} segundos antes de tentar novamente.")
                return

            st.markdown("**Acesso administrativo**")
            st.caption("Entre com sua senha para gerenciar as autorizações.")
            with st.form("login_form"):
                password = st.text_input("Senha de acesso", type="password", placeholder="Digite sua senha")
                submitted = st.form_submit_button("Entrar no painel", type="primary", use_container_width=True)
            if submitted:
                if verify_admin_password(password):
                    st.session_state.admin_ok = True
                    st.session_state.admin_last_activity = time.time()
                    st.session_state.login_attempts = 0
                    st.rerun()
                else:
                    attempts = st.session_state.get("login_attempts", 0) + 1
                    st.session_state.login_attempts = attempts
                    if attempts >= MAX_LOGIN_ATTEMPTS:
                        st.session_state.login_locked_until = time.time() + LOGIN_LOCK_SECONDS
                        st.session_state.login_attempts = 0
                        st.error("Muitas tentativas. O acesso foi temporariamente bloqueado nesta sessão.")
                    else:
                        st.error("Senha incorreta.")
        st.markdown('<div class="login-footer">Área exclusiva para a equipe responsável</div>', unsafe_allow_html=True)


def admin_page():
    if not admin_logged_in():
        login_screen()
        return

    with st.sidebar:
        st.markdown("### 📄 Portal de Autorizações")
        st.caption("Painel administrativo")
        st.divider()
        st.success("✓ Login realizado")
        st.write("")
        if st.button("Sair da conta", use_container_width=True):
            st.session_state.admin_ok = False
            st.session_state.pop("admin_last_activity", None)
            st.rerun()

    st.markdown("""
    <div class="section-intro">
        <h1>Visão geral</h1>
        <p>Acompanhe eventos e autorizações em um só lugar.</p>
    </div>
    """, unsafe_allow_html=True)

    with db_session() as db:
        events = db.scalars(select(Event).order_by(desc(Event.created_at))).all()
        total_auths = db.scalar(select(func.count(Authorization.id))) or 0
        event_auth_counts = dict(db.execute(
            select(Authorization.event_id, func.count(Authorization.id))
            .group_by(Authorization.event_id)
        ).all())

    # Indicadores compactos: três cartões na mesma linha também em telas pequenas.
    active_links = sum(1 for e in events if e.active)
    st.markdown(f"""
    <div class="admin-kpi-grid" aria-label="Resumo do painel">
      <div class="admin-kpi"><div class="admin-kpi-label">Eventos</div><div class="admin-kpi-value">{len(events)}</div></div>
      <div class="admin-kpi"><div class="admin-kpi-label">Links ativos</div><div class="admin-kpi-value">{active_links}</div></div>
      <div class="admin-kpi"><div class="admin-kpi-label">Autorizações</div><div class="admin-kpi-value">{total_auths}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Lembrete administrativo: não executa exclusão nem altera os registros.
    # 30 dias é apenas uma referência operacional configurável, não um prazo legal da LGPD.
    try:
        review_days = max(0, int(os.getenv("RETENTION_REVIEW_DAYS", "30")))
    except ValueError:
        review_days = 30
    today = date.today()
    auth_counts = event_auth_counts
    pending_reviews = [
        (event, auth_counts.get(event.id, 0), event.event_date + timedelta(days=review_days))
        for event in events
        if auth_counts.get(event.id, 0) > 0
        and event.event_date + timedelta(days=review_days) <= today
    ]
    if pending_reviews:
        st.warning(
            f"Revisão de retenção: {len(pending_reviews)} evento(s) com autorizações "
            "atingiram a data sugerida para análise. Nenhum dado será excluído automaticamente."
        )
        with st.expander("Ver eventos que precisam de revisão"):
            for event, count, review_date in pending_reviews:
                st.markdown(
                    f"**{escape(event.title)}** — {count} autorização(ões) · "
                    f"revisão sugerida em {review_date.strftime('%d/%m/%Y')}"
                )
            st.caption(
                "O prazo é uma referência administrativa, não uma obrigação fixa da LGPD. "
                "Avalie a finalidade e eventuais obrigações legais antes de excluir. "
                "A exclusão continua exclusivamente manual na aba Autorizações recebidas."
            )

    tab_events, tab_auth, tab_create = st.tabs(["📅 Eventos", "📄 Autorizações recebidas", "＋ Criar evento"])

    with tab_events:
        if not events:
            st.info("Nenhum evento cadastrado. Comece na aba “＋ Criar evento”.")
        for ev in events:
            with st.container(border=True):
                c1, c2 = st.columns([3.2, 1])
                badge_html = (
                    '<span class="status-badge status-active">● Link Ativo</span>'
                    if ev.active else
                    '<span class="status-badge status-inactive">● Inativo</span>'
                )
                c1.markdown(f"### {escape(ev.title)} &nbsp; {badge_html}", unsafe_allow_html=True)
                c1.markdown(f"📍 **{escape(ev.destination)}** &nbsp;·&nbsp; 📅 **{ev.event_date.strftime('%d/%m/%Y')}**")
                if ev.departure_time or ev.return_time:
                    c1.caption(f"🕒 Saída: {ev.departure_time or '—'} | Retorno: {ev.return_time or '—'}")

                c2.metric("Assinaturas", event_auth_counts.get(ev.id, 0))

                url = make_public_url(ev.public_token)
                u1, u2 = st.columns([4, 1])
                with u1:
                    st.code(url, language=None)
                with u2:
                    st.button("Copiar link", key=f"copy_{ev.id}", use_container_width=True, on_click=lambda u=url: st.session_state.update({"copy_text": u}))

                if st.session_state.get("copy_text") == url:
                    st.info("Selecione e copie o link acima. (Em alguns navegadores, use o ícone de copiar no canto do bloco.)")

                with st.expander("⚙️ Editar ou excluir evento"):
                    with st.form(f"edit_{ev.id}"):
                        ec1, ec2 = st.columns(2)
                        title = ec1.text_input("Nome do evento", value=ev.title)
                        destination = ec2.text_input("Destino", value=ev.destination)
                        event_date = ec1.date_input("Data", value=ev.event_date, format="DD/MM/YYYY")
                        meeting = ec2.text_input("Ponto de encontro", value=ev.meeting_point or "")
                        departure = ec1.text_input("Horário de saída", value=ev.departure_time or "")
                        ret = ec2.text_input("Horário de retorno", value=ev.return_time or "")
                        resp = ec1.text_input("Responsável pela atividade", value=ev.responsible_name or "")
                        phone = ec2.text_input("Telefone da organização", value=ev.responsible_phone or "")
                        emergency = st.text_input("Telefone de emergência da organização", value=ev.emergency_phone or "")
                        description = st.text_area("Descrição / orientações", value=ev.description or "")
                        active = st.checkbox("Link ativo para novas autorizações", value=ev.active)
                        save = st.form_submit_button("Salvar alterações", type="primary")
                    if save:
                        with db_session() as d:
                            obj = d.get(Event, ev.id)
                            obj.title, obj.destination, obj.event_date = title.strip(), destination.strip(), event_date
                            obj.description, obj.departure_time, obj.return_time = description, departure, ret
                            obj.meeting_point, obj.responsible_name = meeting, resp
                            obj.responsible_phone, obj.emergency_phone, obj.active = phone, emergency, active
                            d.commit()
                        st.success("Evento atualizado.")
                        st.rerun()

                    st.divider()
                    st.warning("Excluir um evento também exclui permanentemente todas as autorizações e assinaturas vinculadas.")
                    confirm = st.checkbox("Confirmo que desejo excluir este evento e seus registros", key=f"confirm_del_{ev.id}")
                    if st.button("Excluir evento definitivamente", key=f"delete_{ev.id}", type="secondary", disabled=not confirm):
                        with db_session() as d:
                            obj = d.get(Event, ev.id)
                            if obj:
                                d.delete(obj)
                                d.commit()
                        st.success("Evento e registros excluídos.")
                        st.rerun()

    with tab_create:
        with st.container(border=True):
            with st.form("create_event", clear_on_submit=True):
                st.subheader("Novo evento / passeio")
                st.caption("Preencha as informações principais para gerar o link exclusivo de assinatura.")
                col_a, col_b = st.columns(2)
                title = col_a.text_input("Nome do evento *", placeholder="Ex.: Confraternização Havruta 2026")
                destination = col_b.text_input("Destino *", placeholder="Ex.: Parque / sítio / cidade")
                event_date = col_a.date_input("Data do passeio", value=date.today(), format="DD/MM/YYYY")
                meeting = col_b.text_input("Ponto de encontro", placeholder="Endereço ou local")
                departure = col_a.text_input("Horário de saída", placeholder="08:00")
                ret = col_b.text_input("Horário previsto de retorno", placeholder="18:00")
                resp = col_a.text_input("Nome do responsável pela atividade")
                phone = col_b.text_input("Telefone da organização")
                emergency = st.text_input("Telefone para emergências")
                description = st.text_area("Descrição e orientações", placeholder="Informações que os responsáveis precisam saber")
                create = st.form_submit_button("Criar evento e gerar link", type="primary", use_container_width=True)
            if create:
                if not title.strip() or not destination.strip():
                    st.error("Preencha o nome do evento e o destino.")
                else:
                    ev = Event(
                        title=title.strip(), destination=destination.strip(), event_date=event_date,
                        description=description, departure_time=departure, return_time=ret,
                        meeting_point=meeting, responsible_name=resp, responsible_phone=phone,
                        emergency_phone=emergency, public_token=secrets.token_urlsafe(32), active=True
                    )
                    with db_session() as db:
                        db.add(ev)
                        db.commit()
                    st.success("Evento criado com sucesso!")
                    st.code(make_public_url(ev.public_token), language=None)
                    st.info("Compartilhe este link com os responsáveis legais pelos participantes da atividade.")

    with tab_auth:
        event_options = {f"{e.title} — {e.event_date.strftime('%d/%m/%Y')}": e.id for e in events}
        if not event_options:
            st.info("Crie um evento para começar a receber autorizações.")
        else:
            with st.container(border=True):
                selected_label = st.selectbox("Selecione o evento para visualizar", list(event_options.keys()))
                selected_id = event_options[selected_label]
                with db_session() as db:
                    rows = db.scalars(select(Authorization).where(Authorization.event_id == selected_id).order_by(desc(Authorization.signed_at))).all()
                    export_data = [{
                        "Participante": a.child_name,
                        "Nascimento": a.child_birthdate.strftime("%d/%m/%Y"),
                        "Responsável": a.parent_name,
                        "Líder de célula": a.cell_leader_name or "Não informado",
                        "Vínculo": a.relationship_to_child,
                        "Telefone": a.parent_phone,
                        "E-mail": a.parent_email,
                        "Assinado em": signed_at_brasilia(a.signed_at),
                    } for a in rows]
                    if rows:
                        m1, m2 = st.columns([1, 3])
                        m1.metric("Autorizações recebidas", len(rows))
                        csv = pd.DataFrame(export_data).to_csv(index=False).encode("utf-8-sig")
                        with m2:
                            st.write("")
                            st.download_button("📥 Baixar lista completa (CSV)", csv, file_name="autorizacoes.csv", mime="text/csv")

                        st.dataframe(pd.DataFrame(export_data), use_container_width=True, hide_index=True)
                        st.divider()
                        st.subheader("📄 Comprovantes individuais em PDF")
                        for a in rows:
                            with st.container(border=True):
                                col1, col2 = st.columns([3.5, 1])
                                col1.markdown(f"**{escape(a.child_name)}** <br><span style='color:#64748B;font-size:0.88rem;'>Responsável: {escape(a.parent_name)} ({escape(a.relationship_to_child)}) · Assinado em {signed_at_brasilia(a.signed_at, with_seconds=False)}</span>", unsafe_allow_html=True)
                                # O PDF é preparado apenas sob demanda, evitando gerar
                                # todos os comprovantes em cada atualização da página.
                                pdf_key = f"pdf_ready_{a.id}"
                                if col2.button("Preparar PDF", key=f"prepare_{a.id}", use_container_width=True):
                                    st.session_state[pdf_key] = pdf_bytes(a)
                                if pdf_key in st.session_state:
                                    col2.download_button(
                                        "Baixar PDF", data=st.session_state[pdf_key],
                                        file_name=f"autorizacao_{a.id}.pdf",
                                        mime="application/pdf", key=f"pdf_{a.id}",
                                        use_container_width=True
                                    )
                                # Exclusão individual com confirmação para evitar remoção acidental.
                                with st.expander("Excluir esta autorização"):
                                    st.caption("Esta ação exclui permanentemente o registro e a assinatura digital.")
                                    confirmed = st.checkbox(
                                        "Confirmo a exclusão desta autorização",
                                        key=f"confirm_auth_{a.id}"
                                    )
                                    if st.button(
                                        "Excluir autorização definitivamente",
                                        key=f"delete_auth_{a.id}",
                                        disabled=not confirmed,
                                        use_container_width=True,
                                    ):
                                        with db_session() as delete_db:
                                            target = delete_db.get(Authorization, a.id)
                                            if target is not None and target.event_id == selected_id:
                                                delete_db.delete(target)
                                                delete_db.commit()
                                                st.toast("Autorização excluída.")
                                        st.rerun()
                    else:
                        st.info("Nenhuma autorização recebida. As autorizações assinadas aparecerão aqui.")


def parent_page(token):
    _, main_col, _ = st.columns([0.15, 5, 0.15])

    with main_col:
        with db_session() as db:
            ev = db.scalar(select(Event).where(Event.public_token == token))
            if not ev or not ev.active:
                st.error("Este link não está disponível. Peça à equipe organizadora um link válido.")
                return
            event_id = ev.id
            event_data = {
                "title": ev.title, "destination": ev.destination, "event_date": ev.event_date,
                "description": ev.description, "departure_time": ev.departure_time,
                "return_time": ev.return_time, "meeting_point": ev.meeting_point,
                "responsible_name": ev.responsible_name, "responsible_phone": ev.responsible_phone,
                "emergency_phone": ev.emergency_phone
            }

        draft_hash = init_parent_draft(event_id)
        def draft_key(name):
            return f"draft_{event_id}_{name}"
        def autosave():
            save_parent_draft(event_id, draft_hash)

        def clear_parent_form():
            """Limpa campos, assinatura e rascunho persistido do evento atual."""
            delete_parent_draft(draft_hash)
            defaults = {
                "child_name": "", "child_birthdate": date(2010, 1, 1),
                "parent_name": "", "cell_leader_name": "", "parent_document": "", "relationship": "Mãe",
                "parent_phone": "", "parent_email": "", "emergency_contact": "",
                "emergency_phone": "", "health_notes": "", "declaration": False,
                "privacy": False,
            }
            for field, value in defaults.items():
                st.session_state[draft_key(field)] = value
            # Uma nova chave força o componente de desenho a iniciar vazio.
            nonce_key = f"signature_nonce_{event_id}"
            st.session_state[nonce_key] = st.session_state.get(nonce_key, 0) + 1
            # Não restaurar o rascunho excluído no próximo rerun.
            st.session_state.pop(f"loaded_draft_{event_id}", None)
            st.session_state.pop(f"fields_saved_{event_id}", None)
        if not DRAFT_CIPHER:
            # Falha de configuração interna: não exibir detalhes técnicos ao responsável.
            import logging
            logging.getLogger(__name__).warning("DRAFT_ENCRYPTION_KEY ausente; recuperação de rascunho indisponível.")

        st.markdown("""
        <div class="parent-intro">
            <div class="parent-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/></svg>
            </div>
            <h1>Autorização de Participação</h1>
            <p>Autorize a participação do menor de 18 anos na atividade.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(f"### {escape(event_data['title'])}")
            st.markdown(f"""
            <div class="event-info-grid">
                <div class="event-info-item">
                    <span>📍 Destino</span>
                    <strong>{escape(event_data['destination'])}</strong>
                </div>
                <div class="event-info-item">
                    <span>📅 Data</span>
                    <strong>{event_data['event_date'].strftime('%d/%m/%Y')}</strong>
                </div>
                <div class="event-info-item">
                    <span>🕒 Horários</span>
                    <strong>Saída: {escape(event_data['departure_time'] or 'A confirmar')} · Retorno: {escape(event_data['return_time'] or 'A confirmar')}</strong>
                </div>
                <div class="event-info-item">
                    <span>📌 Ponto de encontro</span>
                    <strong>{escape(event_data['meeting_point'] or 'A confirmar')}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if event_data["description"]:
                st.markdown(
                    '<div class="event-guidance"><strong>Orientações:</strong> '
                    + escape(event_data["description"]).replace("\n", "<br>") + '</div>',
                    unsafe_allow_html=True,
                )

            org_parts = [f"**Organização:** {event_data['responsible_name'] or CONTROLLER_NAME}"]
            if event_data["responsible_phone"]:
                org_parts.append(f"**Contato:** {event_data['responsible_phone']}")
            if event_data["emergency_phone"]:
                org_parts.append(f"**Emergências:** {event_data['emergency_phone']}")
            st.caption("  ·  ".join(org_parts))

        # Fragmentos isolam as atualizacoes de cada secao; sem botao intermediario.
        @st.fragment
        def secao_participante_1():
            with st.container(border=True):
                st.markdown('<div class="step-header"><span class="step-number">1</span><p class="step-title">Dados do participante</p></div>', unsafe_allow_html=True)
                c1, c2 = st.columns([2, 1])
                child_name = c1.text_input("Nome completo do participante *", on_change=autosave, key=draft_key("child_name"))
                child_birthdate = c2.date_input("Data de nascimento *", value=date(2010, 1, 1), min_value=date(1900, 1, 1), max_value=date.today(), format="DD/MM/YYYY", on_change=autosave, key=draft_key("child_birthdate"))


        secao_participante_1()

        @st.fragment
        def secao_participante_2():
            with st.container(border=True):
                st.markdown('<div class="step-header"><span class="step-number">2</span><p class="step-title">Dados do responsável legal</p></div>', unsafe_allow_html=True)
                parent_name = st.text_input("Nome completo do responsável *", on_change=autosave, key=draft_key("parent_name"))
                st.text_input("Nome do líder de célula *", placeholder="Informe o nome do líder de célula", on_change=autosave, key=draft_key("cell_leader_name"))
                r1, r2 = st.columns(2)
                parent_document = r1.text_input("CPF ou outro documento de identificação *", help="Solicite apenas o dado que a organização realmente precisa para confirmar a identidade.", on_change=autosave, key=draft_key("parent_document"))
                relationship = r2.selectbox("Qual é seu vínculo com o participante? *", ["Mãe", "Pai", "Responsável legal", "Tutor(a)", "Outro"], on_change=autosave, key=draft_key("relationship"))
                r3, r4 = st.columns(2)
                parent_phone = r3.text_input("Telefone/WhatsApp *", on_change=autosave, key=draft_key("parent_phone"))
                parent_email = r4.text_input("E-mail (opcional)", on_change=autosave, key=draft_key("parent_email"))


        secao_participante_2()

        @st.fragment
        def secao_participante_3():
            with st.container(border=True):
                st.markdown('<div class="step-header"><span class="step-number">3</span><p class="step-title">Contato para emergência</p></div>', unsafe_allow_html=True)
                e1, e2 = st.columns(2)
                emergency_contact = e1.text_input("Nome do contato de emergência *", on_change=autosave, key=draft_key("emergency_contact"))
                emergency_phone = e2.text_input("Telefone do contato de emergência *", on_change=autosave, key=draft_key("emergency_phone"))


        secao_participante_3()

        @st.fragment
        def secao_participante_4():
            with st.container(border=True):
                st.markdown('<div class="step-header"><span class="step-number">4</span><p class="step-title">Informações importantes</p></div>', unsafe_allow_html=True)
                health_notes = st.text_area(
                    "Existe alguma informação importante para o cuidado do participante durante a atividade? (opcional)",
                    help="Evite incluir detalhes desnecessários. Informe somente o estritamente necessário para o cuidado durante a atividade.", on_change=autosave, key=draft_key("health_notes")
                )


        secao_participante_4()

        with st.container(border=True):
            st.markdown('<div class="step-header"><span class="step-number">5</span><p class="step-title">Confirmação e assinatura</p></div>', unsafe_allow_html=True)
            st.markdown(
                "Declaro ser responsável legal pelo participante menor de 18 anos "
                "identificado neste formulário e autorizo sua participação na atividade "
                "descrita acima. Confirmo que as informações fornecidas são verdadeiras."
            )
            @st.fragment
            def confirmacoes_do_responsavel():
                st.checkbox("Li as informações e autorizo a participação do participante identificado acima. *", key=draft_key("declaration"), on_change=autosave)
                st.checkbox(
                    f"Li as informações de privacidade e estou ciente de que meus dados e os do participante "
                    f"serão tratados pela organização ({CONTROLLER_NAME}) para registrar a autorização, "
                    f"organizar a atividade e atender necessidades de contato e segurança. *",
                    key=draft_key("privacy"), on_change=autosave
                )

            confirmacoes_do_responsavel()
            st.caption(RETENTION_NOTICE)
            st.markdown(
                '<a href="?page=privacy" target="_blank" rel="noopener noreferrer">'
                '🔒 Saiba como seus dados são utilizados (Privacidade e LGPD)</a>',
                unsafe_allow_html=True,
            )
            st.caption("O aviso abre em outra aba para você continuar preenchendo este formulário.")
            if PRIVACY_URL:
                st.markdown(f"[Consultar política de privacidade oficial da organização]({PRIVACY_URL})")

            st.write("")
            st.markdown('<div class="signature-box-hint">✍️ <strong>Assinatura do responsável legal:</strong> desenhe sua assinatura com o dedo ou mouse no quadro branco abaixo.</div>', unsafe_allow_html=True)
            canvas = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=3,
                stroke_color="#1E1B4B",
                background_color="#FFFFFF",
                height=170,
                width=280,
                drawing_mode="freedraw",
                key=f"signature_{event_id}_{st.session_state.get(f'signature_nonce_{event_id}', 0)}",
            )

            st.write("")
            submit_col, clear_col = st.columns([3, 1])
            with submit_col:
                submitted = st.button("Confirmar e enviar autorização", type="primary", use_container_width=True)
            with clear_col:
                st.button(
                    "Limpar formulário", key=f"clear_form_{event_id}",
                    use_container_width=True, on_click=clear_parent_form,
                    help="Apaga os dados preenchidos, a assinatura e o rascunho salvo."
                )

        if submitted:
            # Salva o rascunho atualizado antes da validacao final.
            save_parent_draft(event_id, draft_hash)
            # Fragmentos possuem escopo local; os valores atuais dos widgets
            # sao obtidos do Session State, inclusive apos reruns parciais.
            child_name = st.session_state.get(draft_key("child_name"), "")
            child_birthdate = st.session_state.get(draft_key("child_birthdate"), date(2010, 1, 1))
            parent_name = st.session_state.get(draft_key("parent_name"), "")
            cell_leader_name = st.session_state.get(draft_key("cell_leader_name"), "")
            parent_document = st.session_state.get(draft_key("parent_document"), "")
            relationship = st.session_state.get(draft_key("relationship"), "Mãe")
            parent_phone = st.session_state.get(draft_key("parent_phone"), "")
            parent_email = st.session_state.get(draft_key("parent_email"), "")
            emergency_contact = st.session_state.get(draft_key("emergency_contact"), "")
            emergency_phone = st.session_state.get(draft_key("emergency_phone"), "")
            health_notes = st.session_state.get(draft_key("health_notes"), "")
            declaration = st.session_state.get(draft_key("declaration"), False)
            privacy = st.session_state.get(draft_key("privacy"), False)
            errors = []
            if not child_name.strip(): errors.append("Informe o nome completo do participante.")
            if not parent_name.strip(): errors.append("Informe o nome completo do responsável.")
            if not cell_leader_name.strip(): errors.append("Informe o nome do líder de célula.")
            if not parent_document.strip(): errors.append("Informe um documento de identificação.")
            if not parent_phone.strip(): errors.append("Informe o telefone do responsável.")
            if not emergency_contact.strip() or not emergency_phone.strip(): errors.append("Informe um contato de emergência.")
            if not declaration: errors.append("É necessário confirmar a autorização.")
            if not privacy: errors.append("É necessário confirmar a ciência do aviso de privacidade.")
            if canvas.image_data is None or not (canvas.image_data[:, :, :3] < 245).any():
                errors.append("Faça a assinatura no espaço indicado.")
            if errors:
                for err in errors: st.error(err)
            else:
                image = Image.fromarray(canvas.image_data.astype("uint8")).convert("RGBA")
                sig_io = io.BytesIO()
                image.save(sig_io, format="PNG")
                child_key = normalize_child_name(child_name)
                auth = Authorization(
                    event_id=event_id, child_name=child_name.strip(), child_name_key=child_key,
                    child_birthdate=child_birthdate,
                    parent_name=parent_name.strip(), cell_leader_name=cell_leader_name.strip(), parent_document=parent_document.strip(),
                    parent_phone=parent_phone.strip(), parent_email=parent_email.strip(),
                    relationship_to_child=relationship, emergency_contact=emergency_contact.strip(),
                    emergency_phone=emergency_phone.strip(), health_notes=health_notes.strip(),
                    privacy_accepted=True, declaration_accepted=True, signature_png=sig_io.getvalue(),
                    signed_at=datetime.utcnow()
                )
                try:
                    with db_session() as db:
                        # Cada envio gera um registro independente, mesmo para o
                        # mesmo participante e evento. Nenhum bloqueio de duplicidade.
                        db.add(auth)
                        db.commit()
                        delete_parent_draft(draft_hash)
                        st.success("Autorização enviada com sucesso!")
                        st.info("A equipe organizadora recebeu sua autorização. Para solicitar uma cópia ou corrigir alguma informação, entre em contato diretamente com a organização.")
                except Exception as exc:
                    st.error("Não foi possível salvar a autorização. Tente novamente mais tarde ou contate a equipe.")
                    if setting("SHOW_DEBUG_ERRORS", "false").lower() == "true":
                        st.exception(exc)


def privacy_page():
    """Aviso público simples, sem acesso aos registros de autorizações."""
    _, content, _ = st.columns([0.2, 4, 0.2])
    with content:
        st.markdown("# 🔒 Privacidade dos seus dados")
        st.write(
            "Este aviso explica como as informações fornecidas no Portal de Autorizações "
            "são utilizadas para organizar atividades da igreja envolvendo participantes menores de 18 anos."
        )
        with st.container(border=True):
            st.markdown("#### Para que pedimos esses dados?")
            st.write(
                "Para identificar o participante e seu responsável legal, registrar a autorização, "
                "organizar a atividade e entrar em contato quando necessário, inclusive em emergências."
            )
            st.markdown("#### Quais dados são solicitados?")
            st.write(
                "Nome e data de nascimento do participante; nome, documento, vínculo e contatos "
                "do responsável; contato de emergência; assinatura e eventuais informações adicionais."
            )
            st.caption(
                "No campo de informações adicionais, informe somente o que for necessário "
                "para o cuidado do participante durante a atividade."
            )
            st.markdown("#### Quem pode consultar as informações?")
            st.write(
                "O acesso administrativo aos registros é destinado a pessoas selecionadas "
                "da liderança da igreja, responsáveis pela organização das atividades. "
                "A aplicação também utiliza serviços de hospedagem e armazenamento para processar os dados."
            )
            st.markdown("#### Por quanto tempo ficam armazenados?")
            st.write(RETENTION_NOTICE)
            st.markdown("#### Como tirar dúvidas ou solicitar informações?")
            st.write(
                "O responsável pode pedir informações sobre o uso dos dados e solicitar "
                "acesso, correção ou exclusão, quando aplicável, pelo contato indicado abaixo."
            )
    
        if PRIVACY_URL:
            st.markdown(f"[Consultar aviso de privacidade da organização]({PRIVACY_URL})")
        st.caption(
            "O tratamento dos dados deve observar a LGPD e o melhor interesse dos participantes menores de idade."
        )
        st.caption("Você pode fechar esta aba para retornar ao formulário de autorização.")


def main():
    params = st.query_params
    page = params.get("page", "admin")
    if page == "parent":
        token = params.get("token", "")
        parent_page(token)
    elif page == "privacy":
        privacy_page()
    else:
        admin_page()


if __name__ == "__main__":
    main()
