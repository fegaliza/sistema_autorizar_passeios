import os
import io
import uuid
import hashlib
import hmac
import base64
import secrets
import time
import unicodedata
import json
import streamlit.components.v1 as components
from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib.parse import quote
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from streamlit_cookies_controller import CookieController
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
from pypdf import PdfReader, PdfWriter

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
    """Interface mobile-first: superficies simples, sem wrappers aninhados."""
    st.markdown("""
    <style>
    :root{--ink:#20253B;--muted:#667085;--violet:#6343B6;--line:#E7E9F0;--soft:#F6F4FC}
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#fff!important;color:var(--ink)!important}
    [data-testid="stMainBlockContainer"]{max-width:850px!important;padding:1.25rem 1.5rem 4rem!important}
    .stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label{color:var(--ink)}
    .stApp h1{letter-spacing:-.035em!important}
    .stApp [data-testid="stCaptionContainer"] p{color:var(--muted)!important}
    /* Remove molduras de containers, forms e wrappers; preserva inputs. */
    .stApp [data-testid="stVerticalBlockBorderWrapper"],
    .stApp [data-testid="stVerticalBlockBorderWrapper"] > div,
    .stApp [data-testid="stVerticalBlockBorderWrapper"] > div > div,
    .stApp [data-testid="stForm"],.stApp [data-testid="stForm"] > div,
    .stApp [data-testid="stMetric"]{
      border:0!important;outline:0!important;box-shadow:none!important;
      background:transparent!important;border-radius:0!important;padding:0!important}
    .stApp [data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:10px!important;box-shadow:none!important}
    .stApp [data-testid="stExpander"] details{border:0!important}
    .stApp [data-testid="stTabs"] [role="tablist"]{gap:0!important;border-bottom:1px solid var(--line)!important;overflow-x:auto!important}
    .stApp [data-testid="stTabs"] button[role="tab"]{font-weight:650!important;white-space:nowrap!important;font-size:.86rem!important;padding:.7rem .8rem!important}
    .stApp [data-testid="stTabs"] button[role="tab"][aria-selected="true"]{color:var(--violet)!important}
    .stApp [data-baseweb="input"],.stApp [data-baseweb="textarea"],.stApp [data-baseweb="select"]{border-radius:9px!important;background:white!important}
    .stApp input,.stApp textarea{color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important}
    .stApp .stButton button,.stApp .stDownloadButton button,.stApp .stFormSubmitButton button{
      min-height:44px!important;border-radius:9px!important;box-shadow:none!important;font-weight:650!important}
    .stApp .stButton button[kind="primary"],.stApp .stFormSubmitButton button[kind="primary"]{
      background:var(--violet)!important;border-color:var(--violet)!important;color:#fff!important}
    .stApp .stButton button[kind="primary"] *, .stApp .stFormSubmitButton button[kind="primary"] *{color:#fff!important}
    .stApp hr{border-color:var(--line)!important;margin:.85rem 0!important}
    .section-intro{margin:.1rem 0 1rem}
    .section-intro h1{font-size:1.75rem!important;margin:0 0 .1rem!important}
    .section-intro p{font-size:.89rem!important;color:var(--muted)!important;margin:0!important}
    .admin-kpi-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;margin:.4rem 0 1.15rem;border-bottom:1px solid var(--line);padding-bottom:1rem}
    .admin-kpi{border:0;border-right:1px solid var(--line);padding:.25rem .8rem;min-width:0;background:transparent}
    .admin-kpi:first-child{padding-left:0}.admin-kpi:last-child{border-right:0}
    .admin-kpi-label{color:var(--muted);font-size:.73rem;line-height:1.3}
    .admin-kpi-value{font-size:1.7rem;line-height:1.25;font-weight:750;color:var(--ink);margin-top:.25rem}
    .status-badge{display:inline-block;font-size:.73rem;font-weight:650;padding:3px 8px;border-radius:30px}
    .status-active{background:#E8F7F0;color:#166E4B}.status-inactive{background:#F1F2F5;color:#5F6778}
    .event-heading{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin:.1rem 0 .35rem}
    .event-heading h3{font-size:1.08rem!important;margin:0!important;line-height:1.3}
    .event-details{font-size:.86rem;line-height:1.65;color:var(--muted);margin:.1rem 0 .65rem}
    .event-details strong{color:var(--ink)}
    .event-count{text-align:right}.event-count span{display:block;color:var(--muted);font-size:.73rem}
    .event-count strong{display:block;font-size:1.45rem;line-height:1.25;color:var(--ink)}
    .step-header{display:flex;align-items:center;gap:10px;margin:1.25rem 0 .75rem;padding-bottom:.5rem;border-bottom:1px solid var(--line)}
    .step-number{display:inline-flex;align-items:center;justify-content:center;width:27px;height:27px;border-radius:50%;background:var(--soft);color:var(--violet);font-size:.82rem;font-weight:750;flex-shrink:0}
    .step-title{font-size:1rem!important;font-weight:700!important;margin:0!important}
    .event-info-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 22px;padding:.9rem 0;margin:.3rem 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);background:transparent}
    .event-info-item span{display:block;color:var(--muted);font-size:.73rem;font-weight:600;margin-bottom:3px}
    .event-info-item strong{font-size:.91rem;color:var(--ink);font-weight:650;overflow-wrap:anywhere}
    .event-guidance,.signature-box-hint{border-left:3px solid #B6A3E6;background:var(--soft);border-radius:0 7px 7px 0;padding:.7rem .85rem;margin:.6rem 0}
    .parent-intro{text-align:left;margin:.2rem 0 .8rem}.parent-intro h1{font-size:1.65rem!important;margin:0 0 .2rem!important}.parent-intro p{font-size:.9rem!important;color:var(--muted)!important}
    .login-intro{text-align:center;margin:1.5rem 0}.login-intro h1{font-size:1.5rem!important}.login-footer{text-align:center;color:var(--muted);font-size:.78rem;margin-top:1rem}
    .parent-icon,.login-symbol{display:none}.interface-version{font-size:.67rem;color:#98A1B1;text-align:right;margin-bottom:.3rem}
    .copy-hint{font-size:.78rem;color:var(--muted);margin:.2rem 0 .25rem}
    .stApp [data-testid="stCodeBlock"]{border:1px solid var(--line)!important;border-radius:9px!important;box-shadow:none!important}
    @media(max-width:700px){
      [data-testid="stMainBlockContainer"]{padding:.65rem .9rem 3rem!important}
      .section-intro h1,.parent-intro h1{font-size:1.4rem!important}
      .admin-kpi-grid{margin:.25rem 0 .85rem;padding-bottom:.8rem}
      .admin-kpi{padding:.1rem .5rem}.admin-kpi-label{font-size:.66rem}.admin-kpi-value{font-size:1.35rem}
      .event-info-grid{grid-template-columns:1fr 1fr;gap:13px 12px}
      .event-heading h3{font-size:1rem!important}
      .event-count{text-align:left;padding:.2rem 0 .5rem}.event-count span,.event-count strong{display:inline!important;margin-right:.45rem;font-size:.82rem!important}
      .stApp [data-testid="stTabs"] button[role="tab"]{font-size:.76rem!important;padding:.65rem .5rem!important}
      /* Uma coluna de verdade no celular, inclusive para widgets Streamlit. */
      .stApp [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.55rem!important}
      .stApp [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
         flex:1 1 100%!important;width:100%!important;min-width:0!important}
      .stApp [data-testid="stHorizontalBlock"] [data-testid="stColumn"] > div{min-width:0!important}
      .stApp .stButton button,.stApp .stDownloadButton button,.stApp .stFormSubmitButton button{width:100%!important}
      .step-header{margin-top:1.1rem}
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


# Cookie autenticado: permite atualizar o navegador sem perder o login.
# A assinatura HMAC impede que um visitante invente uma sessao administrativa.
ADMIN_COOKIE_NAME = "havruta_admin_session"
ADMIN_COOKIE_MAX_AGE = 8 * 60 * 60


def admin_cookie_controller():
    if "admin_cookie_controller" not in st.session_state:
        st.session_state.admin_cookie_controller = CookieController(key="havruta_admin_cookie")
    return st.session_state.admin_cookie_controller


def admin_cookie_signature(expires_at):
    return hmac.new(
        ADMIN_PASSWORD_HASH.encode("utf-8"),
        f"havruta-admin-v1:{expires_at}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def issue_admin_cookie():
    expires_at = int(time.time()) + ADMIN_COOKIE_MAX_AGE
    value = f"{expires_at}.{admin_cookie_signature(expires_at)}"
    admin_cookie_controller().set(ADMIN_COOKIE_NAME, value, max_age=ADMIN_COOKIE_MAX_AGE)
    # A escrita acontece no navegador. Nao desmontar o componente imediatamente.
    time.sleep(1.2)


def restore_admin_cookie():
    if not ADMIN_PASSWORD_HASH:
        return False
    try:
        value = admin_cookie_controller().get(ADMIN_COOKIE_NAME)
        if not value:
            return False
        expires_text, signature = value.split(".", 1)
        expires_at = int(expires_text)
        if expires_at <= time.time():
            return False
        return hmac.compare_digest(signature, admin_cookie_signature(expires_at))
    except (ValueError, TypeError, AttributeError):
        return False


def logout_admin():
    st.session_state.admin_ok = False
    st.session_state.pop("admin_last_activity", None)
    admin_cookie_controller().remove(ADMIN_COOKIE_NAME)
    # Aguarda a remocao no navegador antes de reiniciar a pagina.
    time.sleep(0.7)


def delete_authorization(authorization_id, event_id):
    with db_session() as db:
        target = db.get(Authorization, authorization_id)
        if target is None or target.event_id != event_id:
            return False
        db.delete(target)
        db.commit()
    st.session_state.pop(f"pdf_ready_{authorization_id}", None)
    return True


def admin_logged_in():
    if not ADMIN_PASSWORD_HASH:
        return False
    if not st.session_state.get("admin_ok", False):
        # A leitura e assincrona. Reruns forçados em sequencia desmontam o
        # componente antes que ele consiga ler o cookie no navegador.
        if not restore_admin_cookie():
            return False
        st.session_state.admin_cookie_restore_attempts = 0
        st.session_state.admin_ok = True
        st.session_state.admin_last_activity = time.time()
    last_activity = st.session_state.get("admin_last_activity", 0)
    if time.time() - last_activity > SESSION_TIMEOUT_SECONDS:
        logout_admin()
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



def pdf_completo_evento(autorizacoes, titulo_evento):
    """Reune os comprovantes originais em um PDF para consulta offline."""
    writer = PdfWriter()

    # Capa simples com orientacoes para o portador do documento.
    capa_buffer = io.BytesIO()
    capa = SimpleDocTemplate(
        capa_buffer, pagesize=A4, rightMargin=2.2*cm, leftMargin=2.2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    estilos = getSampleStyleSheet()
    conteudo = [
        Paragraph("AUTORIZACOES DO PASSEIO", estilos["Title"]),
        Spacer(1, 14),
        Paragraph(f"<b>Evento:</b> {escape(titulo_evento)}", estilos["BodyText"]),
        Paragraph(f"<b>Autorizações incluídas:</b> {len(autorizacoes)}", estilos["BodyText"]),
        Paragraph(
            f"<b>Gerado em:</b> {datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y às %H:%M')} (Brasília)",
            estilos["BodyText"]
        ),
        Spacer(1, 20),
        Paragraph("ORIENTACOES DE CONFIDENCIALIDADE", estilos["Heading2"]),
        Paragraph(
            "Este documento contem dados pessoais de criancas e adolescentes, de seus responsaveis "
            "e possivelmente informacoes de saude. Seu uso deve ficar restrito a pessoas autorizadas "
            "pela organizacao e as necessidades da atividade.", estilos["BodyText"]
        ),
        Spacer(1, 10),
        Paragraph("1. Nao compartilhe o arquivo com pessoas nao autorizadas ou em grupos de mensagens.", estilos["BodyText"]),
        Paragraph("2. Mantenha o documento em um aparelho protegido por senha ou biometria.", estilos["BodyText"]),
        Paragraph("3. Baixe e salve o PDF no dispositivo enquanto houver internet; teste sua abertura offline.", estilos["BodyText"]),
        Paragraph("4. Exclua as copias locais quando nao forem mais necessarias, inclusive da lixeira e de backups, quando aplicavel.", estilos["BodyText"]),
        Paragraph("5. Em caso de perda do aparelho ou compartilhamento indevido, avise imediatamente a organizacao.", estilos["BodyText"]),
        Spacer(1, 18),
        Paragraph("As autorizacoes individuais estao nas paginas seguintes, em ordem alfabetica.", estilos["BodyText"]),
    ]
    capa.build(conteudo)
    capa_buffer.seek(0)
    writer.append(PdfReader(capa_buffer))

    for autorizacao in sorted(autorizacoes, key=lambda a: (normalize_child_name(a.child_name), a.id)):
        # Reutiliza integralmente o comprovante individual, incluindo assinatura.
        writer.append(PdfReader(io.BytesIO(pdf_bytes(autorizacao))))

    resultado = io.BytesIO()
    writer.write(resultado)
    return resultado.getvalue()


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

        with st.container(border=False):
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
                    st.session_state.admin_cookie_restore_attempts = 0
                    st.session_state.login_attempts = 0
                    issue_admin_cookie()
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
        st.markdown("### Portal de Autorizações")
        st.caption("Painel administrativo")
        st.divider()
        st.success("✓ Login realizado")
        st.write("")
        if st.button("Sair da conta", use_container_width=True):
            logout_admin()
            st.rerun()

    if st.session_state.pop("admin_delete_notice", None):
        st.success("Autorização excluída com sucesso. Atualize a lista para conferir.")

    st.markdown('<div class="interface-version">Havruta · Mobile UX v4</div>', unsafe_allow_html=True)
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

    tab_events, tab_auth, tab_create = st.tabs(["Eventos", "Autorizações", "Criar evento"])

    with tab_events:
        if not events:
            st.info("Nenhum evento cadastrado. Comece na aba “Criar evento”.")
        for ev in events:
            st.divider()
            with st.container(border=False):
                c1, c2 = st.columns([3, 1])
                badge_html = (
                    '<span class="status-badge status-active">● Link Ativo</span>'
                    if ev.active else
                    '<span class="status-badge status-inactive">● Inativo</span>'
                )
                c1.markdown(f'<div class="event-heading"><h3>{escape(ev.title)}</h3>{badge_html}</div>', unsafe_allow_html=True)
                time_detail = (f'<br>Saída: {escape(ev.departure_time or "—")} &nbsp;·&nbsp; Retorno: {escape(ev.return_time or "—")}') if (ev.departure_time or ev.return_time) else ''
                c1.markdown(f'<div class="event-details"><strong>Destino:</strong> {escape(ev.destination)} &nbsp;·&nbsp; <strong>Data:</strong> {ev.event_date.strftime("%d/%m/%Y")}{time_detail}</div>', unsafe_allow_html=True)

                c2.markdown(f'<div class="event-count"><span>Assinaturas</span><strong>{event_auth_counts.get(ev.id, 0)}</strong></div>', unsafe_allow_html=True)
                url = make_public_url(ev.public_token)

                st.caption("🔗 Link para compartilhar com os responsáveis:")

                components.html(
                    f"""
                    <input id="link" value="{escape(url, {'"': '&quot;'})}" readonly
                        style="width:65%;padding:10px;border:1px solid #ddd;border-radius:6px;">

                    <button id="btn" onclick="copiar()"
                        style="background:#6343B6;color:white;padding:10px;
                        border:0;border-radius:6px;cursor:pointer;">
                        Copiar link
                    </button>

                    <p id="mensagem" role="status" aria-live="polite"
                       style="font-size:13px;margin-top:6px;"></p>

                    <script>
                    async function copiar() {{
                        const link = document.getElementById("link");
                        const mensagem = document.getElementById("mensagem");

                        try {{
                            if (navigator.clipboard && window.isSecureContext) {{
                                await navigator.clipboard.writeText(link.value);
                            }} else {{
                                link.select();
                                if (!document.execCommand("copy")) {{
                                    throw new Error("Falha na cópia");
                                }}
                            }}
                            mensagem.innerText = "✓ Link copiado com sucesso!";
                            mensagem.style.color = "green";
                            document.getElementById("btn").innerText = "✓ Copiado!";
                        }} catch (erro) {{
                            mensagem.innerText = "Não foi possível copiar. Selecione o link manualmente.";
                            mensagem.style.color = "red";
                            link.focus();
                            link.select();
                        }}
                    }}
                    </script>
                    """,
                    height=100,
                )
               

                with st.expander("Editar ou excluir evento"):
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
        with st.container(border=False):
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
            with st.container(border=False):
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
                            st.download_button("Baixar lista (CSV)", csv, file_name="autorizacoes.csv", mime="text/csv")

                        st.dataframe(pd.DataFrame(export_data), use_container_width=True, hide_index=True)

                        # Download opcional: nao altera os comprovantes individuais.
                        with st.expander("Consulta offline · PDF completo do passeio"):
                            st.caption(
                                "Baixe enquanto estiver conectado à internet e salve o arquivo no celular "
                                "antes do passeio. Confira se ele abre em modo avião."
                            )
                            st.caption(
                                "Privacidade (LGPD): contém dados de menores e responsáveis. "
                                "Não compartilhe com pessoas não autorizadas; proteja o aparelho e "
                                "exclua as cópias quando não forem mais necessárias."
                            )
                            confirmado = st.checkbox(
                                "Estou ciente dos cuidados de confidencialidade e uso restrito.",
                                key=f"offline_confirm_{selected_id}"
                            )
                            chave_pdf = f"offline_pdf_{selected_id}"
                            assinatura_atual = tuple(sorted((a.id, a.signed_at.isoformat()) for a in rows))
                            if st.session_state.get(f"{chave_pdf}_versao") != assinatura_atual:
                                st.session_state.pop(chave_pdf, None)
                            if st.button(
                                "Preparar PDF completo", key=f"offline_prepare_{selected_id}",
                                disabled=not confirmado, type="secondary"
                            ):
                                try:
                                    with st.spinner("Reunindo as autorizações..."):
                                        st.session_state[chave_pdf] = pdf_completo_evento(
                                            rows, selected_label
                                        )
                                        st.session_state[f"{chave_pdf}_versao"] = assinatura_atual
                                except Exception:
                                    st.error("Não foi possível preparar o PDF. Tente novamente.")
                            if confirmado and chave_pdf in st.session_state:
                                st.download_button(
                                    "Baixar PDF completo do passeio",
                                    data=st.session_state[chave_pdf],
                                    file_name=f"autorizacoes_passeio_{selected_id}.pdf",
                                    mime="application/pdf", key=f"offline_download_{selected_id}"
                                )
                        st.divider()
                        st.subheader("Comprovantes em PDF")
                        for a in rows:
                            with st.container(border=False):
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
                                # Formulario de exclusao: um unico envio com confirmacao.
                                with st.expander("Excluir esta autorização"):
                                    st.warning("A exclusão é permanente e remove também a assinatura armazenada.")
                                    with st.form(f"delete_authorization_form_{a.id}"):
                                        confirmed = st.checkbox(
                                            f"Confirmo que desejo excluir a autorização de {a.child_name}",
                                            key=f"confirm_auth_{a.id}",
                                        )
                                        delete_submitted = st.form_submit_button(
                                            "Excluir autorização definitivamente",
                                            type="secondary",
                                            use_container_width=True,
                                        )
                                    if delete_submitted:
                                        if not confirmed:
                                            st.error("Marque a caixa de confirmação antes de excluir.")
                                        else:
                                            try:
                                                deleted = delete_authorization(a.id, selected_id)
                                                if deleted:
                                                    st.session_state["admin_delete_notice"] = "Autorização excluída com sucesso."
                                                else:
                                                    st.session_state["admin_delete_notice"] = "Autorização não encontrada; atualize a lista."
                                                st.rerun()
                                            except Exception:
                                                st.error("Não foi possível excluir esta autorização. Verifique a conexão com o banco e tente novamente.")
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

        try:
            draft_hash = init_parent_draft(event_id)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Falha temporaria ao restaurar rascunho")
            draft_hash = None
        def draft_key(name):
            return f"draft_{event_id}_{name}"
        def autosave():
            try:
                save_parent_draft(event_id, draft_hash)
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Falha temporaria ao salvar rascunho")

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

        st.markdown('<div class="interface-version">Havruta · Mobile UX v4</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="parent-intro">
            <div class="parent-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/></svg>
            </div>
            <h1>Autorização de Participação</h1>
            <p>Autorize a participação do menor de 18 anos na atividade.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=False):
            st.markdown(f"### {escape(event_data['title'])}")
            st.markdown(f"""
            <div class="event-info-grid">
                <div class="event-info-item">
                    <span>Destino</span>
                    <strong>{escape(event_data['destination'])}</strong>
                </div>
                <div class="event-info-item">
                    <span>Data</span>
                    <strong>{event_data['event_date'].strftime('%d/%m/%Y')}</strong>
                </div>
                <div class="event-info-item">
                    <span>Horários</span>
                    <strong>Saída: {escape(event_data['departure_time'] or 'A confirmar')} · Retorno: {escape(event_data['return_time'] or 'A confirmar')}</strong>
                </div>
                <div class="event-info-item">
                    <span>Ponto de encontro</span>
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
            with st.container(border=False):
                st.markdown('<div class="step-header"><span class="step-number">1</span><p class="step-title">Dados do participante</p></div>', unsafe_allow_html=True)
                c1, c2 = st.columns([2, 1])
                child_name = c1.text_input("Nome completo do participante *", on_change=autosave, key=draft_key("child_name"))
                child_birthdate = c2.date_input("Data de nascimento *", value=date(2010, 1, 1), min_value=date(1900, 1, 1), max_value=date.today(), format="DD/MM/YYYY", on_change=autosave, key=draft_key("child_birthdate"))
        secao_participante_1()

        @st.fragment
        def secao_participante_2():
            with st.container(border=False):
                st.markdown('<div class="step-header"><span class="step-number">2</span><p class="step-title">Dados do responsável legal</p></div>', unsafe_allow_html=True)
                parent_name = st.text_input("Nome completo do responsável *", on_change=autosave, key=draft_key("parent_name"))
                st.text_input("Nome do líder de célula *", placeholder="Informe o nome completo do líder de célula", on_change=autosave, key=draft_key("cell_leader_name"))
                r1, r2 = st.columns(2)
                parent_document = r1.text_input("CPF ou outro documento de identificação *", help="Solicite apenas o dado que a organização realmente precisa para confirmar a identidade.", on_change=autosave, key=draft_key("parent_document"))
                relationship = r2.selectbox("Qual é seu vínculo com o participante? *", ["Mãe", "Pai", "Responsável legal", "Tutor(a)", "Outro"], on_change=autosave, key=draft_key("relationship"))
                r3, r4 = st.columns(2)
                parent_phone = r3.text_input("Telefone/WhatsApp *", on_change=autosave, key=draft_key("parent_phone"))
                parent_email = r4.text_input("E-mail (opcional)", on_change=autosave, key=draft_key("parent_email"))


        secao_participante_2()

        @st.fragment
        def secao_participante_3():
            with st.container(border=False):
                st.markdown('<div class="step-header"><span class="step-number">3</span><p class="step-title">Contato para emergência</p></div>', unsafe_allow_html=True)
                e1, e2 = st.columns(2)
                emergency_contact = e1.text_input("Nome do contato de emergência *", on_change=autosave, key=draft_key("emergency_contact"))
                emergency_phone = e2.text_input("Telefone do contato de emergência *", on_change=autosave, key=draft_key("emergency_phone"))


        secao_participante_3()

        @st.fragment
        def secao_participante_4():
            with st.container(border=False):
                st.markdown('<div class="step-header"><span class="step-number">4</span><p class="step-title">Informações importantes</p></div>', unsafe_allow_html=True)
                health_notes = st.text_area(
                    "Existe alguma informação importante para o cuidado do participante durante a atividade? (opcional)",
                    help="Evite incluir detalhes desnecessários. Informe somente o estritamente necessário para o cuidado durante a atividade.", on_change=autosave, key=draft_key("health_notes")
                )


        secao_participante_4()

        with st.container(border=False):
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
                'Saiba como seus dados são utilizados (Privacidade e LGPD)</a>',
                unsafe_allow_html=True,
            )
            st.caption("O aviso abre em outra aba para você continuar preenchendo este formulário.")
            if PRIVACY_URL:
                st.markdown(f"[Consultar política de privacidade oficial da organização]({PRIVACY_URL})")

            st.write("")
            st.markdown('<div class="signature-box-hint"><strong>Assinatura do responsável legal:</strong> desenhe sua assinatura com o dedo ou mouse no quadro branco abaixo.</div>', unsafe_allow_html=True)
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
                    event_id=event_id,
                    child_name=child_name.strip(),
                    child_name_key=child_key,
                    child_birthdate=child_birthdate,
                    parent_name=parent_name.strip(),
                    cell_leader_name=cell_leader_name.strip(),
                    parent_document=parent_document.strip(),
                    parent_phone=parent_phone.strip(),
                    parent_email=parent_email.strip(),
                    relationship_to_child=relationship,
                    emergency_contact=emergency_contact.strip(),
                    emergency_phone=emergency_phone.strip(),
                    health_notes=health_notes.strip(),
                    privacy_accepted=True,
                    declaration_accepted=True,
                    signature_png=sig_io.getvalue(),
                    signed_at=datetime.utcnow()
                )
                try:
                    with db_session() as db:
                        # Evita envios simultaneos no PostgreSQL.
                        if engine.dialect.name == "postgresql":
                            db.execute(
                                select(Event.id)
                                .where(Event.id == event_id)
                                .with_for_update()
                            ).scalar_one()

                        # Verifica duplicidade.
                        existing_auth = db.scalar(
                            select(Authorization.id).where(
                                Authorization.event_id == event_id,
                                Authorization.child_name_key == child_key,
                                Authorization.child_birthdate == child_birthdate
                            ).limit(1)
                        )

                        if existing_auth is not None:
                            st.warning(
                                "Inscrição do participante já realizada! "
                                "Não é necessário enviar novamente. "
                                "Caso precise corrigir alguma informação, "
                                "entre em contato com a equipe organizadora."
                            )
                            return

                        db.add(auth)
                        db.commit()
                        delete_parent_draft(draft_hash)
                        st.success("Autorização enviada com sucesso!")
                        st.info("A equipe organizadora recebeu sua autorização.")

                except Exception as exc:
                    st.error("Não foi possível salvar a autorização. Tente novamente mais tarde ou contate a equipe.")
                    if setting("SHOW_DEBUG_ERRORS", "false").lower() == "true":
                        st.exception(exc)
def privacy_page():
    """Aviso público simples, sem acesso aos registros de autorizações."""
    _, content, _ = st.columns([0.2, 4, 0.2])
    with content:
        st.markdown("# Privacidade dos seus dados")
        st.write(
            "Este aviso explica como as informações fornecidas no Portal de Autorizações "
            "são utilizadas para organizar atividades da igreja envolvendo participantes menores de 18 anos."
        )
        with st.container(border=False):
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
