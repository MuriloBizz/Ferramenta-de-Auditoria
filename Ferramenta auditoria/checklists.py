"""
checklists.py
Criação e consulta de checklists e seus itens.
"""

from database import get_connection, now_str


def criar_checklist(nome, processo, responsavel, email_responsavel, itens):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO checklists (nome, processo, responsavel, email_responsavel, criado_em)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nome, processo, responsavel, email_responsavel, now_str()),
    )
    checklist_id = cur.lastrowid

    for ordem, item in enumerate(itens, start=1):
        cur.execute(
            """
            INSERT INTO itens_checklist
                (checklist_id, categoria, descricao, prioridade, responsavel, email_responsavel, ordem)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                checklist_id,
                item["categoria"],
                item["descricao"],
                item["prioridade"],
                item["responsavel"],
                item["email_responsavel"],
                ordem,
            ),
        )

    conn.commit()
    conn.close()
    return checklist_id


def listar_checklists():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM checklists ORDER BY id").fetchall()
    conn.close()
    return rows


def obter_checklist(checklist_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM checklists WHERE id = ?", (checklist_id,)).fetchone()
    conn.close()
    return row

def atualizar_responsavel_checklist(checklist_id, responsavel, email_responsavel):
    conn = get_connection()
    conn.execute(
        "UPDATE checklists SET responsavel = ?, email_responsavel = ? WHERE id = ?",
        (responsavel, email_responsavel, checklist_id),
    )
    conn.commit()
    conn.close()


def listar_itens_checklist(checklist_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM itens_checklist WHERE checklist_id = ? ORDER BY ordem", (checklist_id,)
    ).fetchall()
    conn.close()
    return rows
