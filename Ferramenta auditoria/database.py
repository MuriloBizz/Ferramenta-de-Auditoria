"""
database.py
Conexão com o SQLite, criação/migração do schema e constantes do domínio
(prioridades, prazos em dias úteis e status possíveis de uma NC).
"""

import os
import sqlite3
from datetime import date, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auditoria.db")

PRAZOS_DIAS = {1: 10, 2: 5, 3: 2}
PRIORIDADES = {1: "Baixa", 2: "Média", 3: "Alta"}
STATUS_NC = ["Reportada", "Escalonada", "Solucionada", "Dívida Técnica"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS checklists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    processo TEXT NOT NULL,
    responsavel TEXT NOT NULL,
    email_responsavel TEXT NOT NULL,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS itens_checklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_id INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    descricao TEXT NOT NULL,
    prioridade INTEGER NOT NULL DEFAULT 2,
    responsavel TEXT NOT NULL,
    email_responsavel TEXT NOT NULL,
    ordem INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS auditorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_id INTEGER NOT NULL,
    auditor TEXT NOT NULL,
    data_auditoria TEXT NOT NULL,
    percentual_aderencia REAL,
    nome TEXT,
    versao_derivada INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS respostas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auditoria_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    conforme INTEGER NOT NULL,
    observacao TEXT,
    FOREIGN KEY (auditoria_id) REFERENCES auditorias(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES itens_checklist(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS nao_conformidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resposta_id INTEGER,
    auditoria_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    prioridade INTEGER NOT NULL,
    responsavel TEXT NOT NULL,
    email_responsavel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Reportada',
    nivel_escalonamento INTEGER NOT NULL DEFAULT 0,
    data_abertura TEXT NOT NULL,
    prazo_atual TEXT NOT NULL,
    data_encerramento TEXT,
    acao_corretiva TEXT,
    FOREIGN KEY (resposta_id) REFERENCES respostas(id) ON DELETE SET NULL,
    FOREIGN KEY (auditoria_id) REFERENCES auditorias(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS historico_nc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nc_id INTEGER NOT NULL,
    data_evento TEXT NOT NULL,
    evento TEXT NOT NULL,
    detalhe TEXT,
    FOREIGN KEY (nc_id) REFERENCES nao_conformidades(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comunicacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nc_id INTEGER NOT NULL,
    data_envio TEXT NOT NULL,
    destinatario TEXT NOT NULL,
    canal TEXT NOT NULL,
    assunto TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    FOREIGN KEY (nc_id) REFERENCES nao_conformidades(id) ON DELETE CASCADE
);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(reset=False):
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_connection()
    conn.executescript(_SCHEMA)
    conn.commit()
    _migrar_schema(conn)
    conn.close()


def _migrar_schema(conn):
    """Adiciona colunas novas em bancos criados por versões antigas do app."""
    colunas = {row["name"] for row in conn.execute("PRAGMA table_info(auditorias)")}

    if "nome" not in colunas:
        conn.execute("ALTER TABLE auditorias ADD COLUMN nome TEXT")
    if "versao_derivada" not in colunas:
        conn.execute("ALTER TABLE auditorias ADD COLUMN versao_derivada INTEGER NOT NULL DEFAULT 0")

    conn.execute(
        """
        UPDATE auditorias
        SET nome = (SELECT nome FROM checklists WHERE checklists.id = auditorias.checklist_id)
        WHERE nome IS NULL
        """
    )
    conn.commit()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return date.today().strftime("%Y-%m-%d")
