"""
database.py
Camada de acesso a dados da ferramenta de Auditoria de Qualidade.
Usa SQLite (arquivo local, sem dependências externas, sem Excel).
"""

import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auditoria.db")

# Prazos padrão (em dias) para cada nível de escalonamento por severidade
PRAZOS_DIAS = {
    "Baixa": 10,
    "Média": 5,
    "Alta": 2,
}

NIVEIS_ESCALONAMENTO = ["Responsável", "Supervisor", "Gerência"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(reset=False):
    """Cria as tabelas do banco. Se reset=True, apaga o banco existente antes."""
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            processo TEXT NOT NULL,
            criado_em TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS itens_checklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            peso REAL NOT NULL DEFAULT 1.0,
            ordem INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS auditorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER NOT NULL,
            auditor TEXT NOT NULL,
            data_auditoria TEXT NOT NULL,
            percentual_aderencia REAL,
            FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auditoria_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            conforme INTEGER NOT NULL,  -- 1 = conforme, 0 = não conforme, -1 = não se aplica
            observacao TEXT,
            FOREIGN KEY (auditoria_id) REFERENCES auditorias(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES itens_checklist(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS nao_conformidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resposta_id INTEGER,
            auditoria_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            severidade TEXT NOT NULL, -- Baixa, Média, Alta
            responsavel TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Aberta', -- Aberta, Em Tratativa, Em Verificação, Encerrada
            nivel_escalonamento INTEGER NOT NULL DEFAULT 0, -- índice em NIVEIS_ESCALONAMENTO
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
    )
    conn.commit()
    conn.close()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return date.today().strftime("%Y-%m-%d")
