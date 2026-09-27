"""
auditorias.py
Execução de uma auditoria (grava as respostas, calcula a % de aderência e
abre NCs para os itens não conformes) e consulta ao histórico de auditorias
já realizadas.
"""

import checklists
import comunicacoes
from database import get_connection, now_str
from nao_conformidades import abrir_nc, obter_nc


def executar_auditoria(checklist_id, auditor, respostas):
    conn = get_connection()
    cur = conn.cursor()

    checklist = checklists.obter_checklist(checklist_id)
    cur.execute(
        """
        INSERT INTO auditorias (checklist_id, auditor, data_auditoria, percentual_aderencia, nome, versao_derivada)
        VALUES (?, ?, ?, NULL, ?, 0)
        """,
        (checklist_id, auditor, now_str(), checklist["nome"]),
    )
    auditoria_id = cur.lastrowid

    itens = {item["id"]: item for item in checklists.listar_itens_checklist(checklist_id)}

    itens_aplicaveis = 0
    itens_conformes = 0
    nc_criadas = []

    for resp in respostas:
        item = itens[resp["item_id"]]
        conforme = resp["conforme"]

        cur.execute(
            "INSERT INTO respostas (auditoria_id, item_id, conforme, observacao) VALUES (?, ?, ?, ?)",
            (auditoria_id, resp["item_id"], conforme, resp.get("observacao", "")),
        )
        resposta_id = cur.lastrowid

        if conforme != -1:
            itens_aplicaveis += 1
            if conforme == 1:
                itens_conformes += 1

        if conforme == 0:
            nc_id = abrir_nc(
                cur,
                resposta_id=resposta_id,
                auditoria_id=auditoria_id,
                descricao=f"[{item['categoria']}] {item['descricao']} — {resp.get('observacao', '')}".strip(),
                prioridade=item["prioridade"],
                responsavel=resp.get("responsavel") or item["responsavel"],
                email_responsavel=resp.get("email_responsavel") or item["email_responsavel"],
            )
            nc_criadas.append(nc_id)

    percentual = round((itens_conformes / itens_aplicaveis) * 100, 2) if itens_aplicaveis > 0 else 0.0
    cur.execute("UPDATE auditorias SET percentual_aderencia = ? WHERE id = ?", (percentual, auditoria_id))

    conn.commit()
    conn.close()

    for nc_id in nc_criadas:
        try:
            comunicacoes.enviar_comunicacao_abertura(obter_nc(nc_id))
        except Exception as e:
            print(f"[aviso] Falha ao comunicar abertura da NC {nc_id}: {e}")

    return {"auditoria_id": auditoria_id, "percentual_aderencia": percentual, "nc_criadas": nc_criadas}


def historico_auditorias(checklist_id=None):
    conn = get_connection()
    query = (
        "SELECT a.*, c.nome as checklist_nome FROM auditorias a "
        "JOIN checklists c ON c.id = a.checklist_id "
    )
    if checklist_id:
        rows = conn.execute(query + "WHERE a.checklist_id = ? ORDER BY a.id DESC", (checklist_id,)).fetchall()
    else:
        rows = conn.execute(query + "ORDER BY a.id DESC").fetchall()
    conn.close()
    return rows


def respostas_da_auditoria(auditoria_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT r.conforme, r.observacao, i.categoria, i.descricao, i.prioridade, i.responsavel, i.ordem
        FROM respostas r
        JOIN itens_checklist i ON i.id = r.item_id
        WHERE r.auditoria_id = ?
        ORDER BY i.ordem
        """,
        (auditoria_id,),
    ).fetchall()
    conn.close()
    return rows
