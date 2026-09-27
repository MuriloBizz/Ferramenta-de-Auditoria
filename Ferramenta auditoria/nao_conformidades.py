"""
nao_conformidades.py
Ciclo de vida de uma Não Conformidade (NC): abertura automática ao final de
uma auditoria, consulta, escalonamento por prazo vencido e encerramento.
Quando uma NC é solucionada, gera uma nova versão da auditoria de origem
com o item corrigido (ver _criar_versao_auditoria_pos_resolucao).
"""

from datetime import datetime, timedelta

import comunicacoes
import email_service
from database import PRAZOS_DIAS, PRIORIDADES, get_connection, now_str, today_str

TRANSICOES_PERMITIDAS = {
    "Reportada": ["Solucionada", "Escalonada"],
    "Escalonada": ["Solucionada", "Dívida Técnica"],
    "Solucionada": [],
    "Dívida Técnica": [],
}


def adicionar_dias_uteis(data_inicial, quantidade):
    data = data_inicial
    adicionados = 0
    while adicionados < quantidade:
        data += timedelta(days=1)
        if data.weekday() < 5:
            adicionados += 1
    return data


def calcular_prazo(data_base, prioridade):
    ultimo_dia = adicionar_dias_uteis(data_base, PRAZOS_DIAS[prioridade])
    return adicionar_dias_uteis(ultimo_dia, 1)


def abrir_nc(cur, resposta_id, auditoria_id, descricao, prioridade, responsavel, email_responsavel):
    data_abertura = datetime.now().date()
    prazo_atual = calcular_prazo(data_abertura, prioridade).strftime("%Y-%m-%d")

    cur.execute(
        """
        INSERT INTO nao_conformidades
            (resposta_id, auditoria_id, descricao, prioridade, responsavel,
             email_responsavel, status, nivel_escalonamento, data_abertura, prazo_atual)
        VALUES (?, ?, ?, ?, ?, ?, 'Reportada', 0, ?, ?)
        """,
        (
            resposta_id, auditoria_id, descricao, prioridade, responsavel,
            email_responsavel, data_abertura.strftime("%Y-%m-%d"), prazo_atual,
        ),
    )
    nc_id = cur.lastrowid

    cur.execute(
        "INSERT INTO historico_nc (nc_id, data_evento, evento, detalhe) VALUES (?, ?, ?, ?)",
        (
            nc_id, now_str(), "Abertura",
            f"NC aberta automaticamente. Responsável: {responsavel}. "
            f"Prioridade: {PRIORIDADES[prioridade]}. Prazo: {prazo_atual}.",
        ),
    )
    return nc_id


def obter_nc(nc_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM nao_conformidades WHERE id = ?", (nc_id,)).fetchone()
    conn.close()
    return row


def obter_responsaveis_nc(nc_id):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            nc.responsavel AS responsavel_item,
            nc.email_responsavel AS email_item,
            c.responsavel AS responsavel_checklist,
            c.email_responsavel AS email_checklist
        FROM nao_conformidades nc
        JOIN auditorias a ON a.id = nc.auditoria_id
        JOIN checklists c ON c.id = a.checklist_id
        WHERE nc.id = ?
        """,
        (nc_id,),
    ).fetchone()
    conn.close()
    return row


def listar_ncs(status=None):
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM nao_conformidades WHERE status = ? ORDER BY data_abertura", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM nao_conformidades ORDER BY data_abertura").fetchall()
    conn.close()
    return rows


def historico_da_nc(nc_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM historico_nc WHERE nc_id = ? ORDER BY data_evento", (nc_id,)
    ).fetchall()
    conn.close()
    return rows


def verificar_prazos_vencidos():
    conn = get_connection()
    ncs = conn.execute(
        "SELECT * FROM nao_conformidades WHERE status IN ('Reportada', 'Escalonada')"
    ).fetchall()
    conn.close()

    hoje = datetime.now().date()
    return [
        nc for nc in ncs
        if hoje >= datetime.strptime(nc["prazo_atual"], "%Y-%m-%d").date()
    ]


def _criar_versao_auditoria_pos_resolucao(nc_id):
    """
    Gera uma nova linha em 'auditorias' copiando as respostas da auditoria
    mais recente do checklist, com o item da NC resolvida marcado como
    Conforme, e recalcula a % de aderência. A auditoria original não muda.
    """
    conn = get_connection()
    cur = conn.cursor()

    nc = cur.execute("SELECT * FROM nao_conformidades WHERE id = ?", (nc_id,)).fetchone()
    if not nc or not nc["resposta_id"]:
        conn.close()
        return

    resposta_original = cur.execute(
        "SELECT * FROM respostas WHERE id = ?", (nc["resposta_id"],)
    ).fetchone()
    if not resposta_original:
        conn.close()
        return

    auditoria_origem = cur.execute(
        "SELECT * FROM auditorias WHERE id = ?", (resposta_original["auditoria_id"],)
    ).fetchone()
    checklist_id = auditoria_origem["checklist_id"]
    checklist = cur.execute("SELECT * FROM checklists WHERE id = ?", (checklist_id,)).fetchone()

    ultima_auditoria = cur.execute(
        "SELECT * FROM auditorias WHERE checklist_id = ? ORDER BY id DESC LIMIT 1", (checklist_id,)
    ).fetchone()
    respostas_base = cur.execute(
        "SELECT * FROM respostas WHERE auditoria_id = ?", (ultima_auditoria["id"],)
    ).fetchall()

    proxima_versao = (ultima_auditoria["versao_derivada"] or 0) + 1
    novo_nome = f"{checklist['nome']} ({proxima_versao})"

    novas_respostas = []
    for r in respostas_base:
        conforme = 1 if r["item_id"] == resposta_original["item_id"] else r["conforme"]
        novas_respostas.append((r["item_id"], conforme, r["observacao"]))

    aplicaveis = sum(1 for _, c, _ in novas_respostas if c != -1)
    conformes = sum(1 for _, c, _ in novas_respostas if c == 1)
    percentual = round((conformes / aplicaveis) * 100, 2) if aplicaveis > 0 else 0.0

    cur.execute(
        """
        INSERT INTO auditorias (checklist_id, auditor, data_auditoria, percentual_aderencia, nome, versao_derivada)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (checklist_id, ultima_auditoria["auditor"], now_str(), percentual, novo_nome, proxima_versao),
    )
    nova_auditoria_id = cur.lastrowid

    for item_id, conforme, observacao in novas_respostas:
        cur.execute(
            "INSERT INTO respostas (auditoria_id, item_id, conforme, observacao) VALUES (?, ?, ?, ?)",
            (nova_auditoria_id, item_id, conforme, observacao),
        )

    conn.commit()
    conn.close()


def atualizar_status_nc(nc_id, novo_status, acao_corretiva=None, usuario="Sistema", email_destino=None):
    if novo_status in ("Escalonada", "Dívida Técnica", "Solucionada") and not email_service.configurado():
        raise ValueError(
            "Configure o e-mail remetente e a senha de aplicativo na aba "
            "'Configurações' antes de alterar o status de uma NC."
        )

    conn = get_connection()
    cur = conn.cursor()

    nc = cur.execute("SELECT * FROM nao_conformidades WHERE id = ?", (nc_id,)).fetchone()
    if not nc:
        conn.close()
        raise ValueError("Não conformidade não encontrada.")

    status_atual = nc["status"]
    prazo = datetime.strptime(nc["prazo_atual"], "%Y-%m-%d").date()
    hoje = datetime.now().date()
    prazo_vencido = hoje >= prazo

    if novo_status not in TRANSICOES_PERMITIDAS.get(status_atual, []):
        conn.close()
        raise ValueError(f"Não é permitido alterar uma NC de '{status_atual}' para '{novo_status}'.")

    if novo_status in ("Escalonada", "Dívida Técnica") and not prazo_vencido:
        conn.close()
        raise ValueError("O prazo da NC ainda não venceu.")

    data_encerramento = today_str() if novo_status in ("Solucionada", "Dívida Técnica") else None
    novo_prazo = nc["prazo_atual"]
    nivel_escalonamento = nc["nivel_escalonamento"]

    if novo_status == "Escalonada":
        novo_prazo = calcular_prazo(hoje, nc["prioridade"]).strftime("%Y-%m-%d")
        nivel_escalonamento = 1

    cur.execute(
        """
        UPDATE nao_conformidades
        SET status = ?, prazo_atual = ?, nivel_escalonamento = ?, data_encerramento = ?, acao_corretiva = ?
        WHERE id = ?
        """,
        (novo_status, novo_prazo, nivel_escalonamento, data_encerramento, acao_corretiva, nc_id),
    )

    detalhe = f"Alterado por: {usuario}. Prazo anterior: {nc['prazo_atual']}. Novo prazo: {novo_prazo}."
    if acao_corretiva:
        detalhe += f" Ação: {acao_corretiva}"

    cur.execute(
        "INSERT INTO historico_nc (nc_id, data_evento, evento, detalhe) VALUES (?, ?, ?, ?)",
        (nc_id, now_str(), f"Status -> {novo_status}", detalhe),
    )

    conn.commit()
    conn.close()

    if novo_status == "Solucionada":
        _criar_versao_auditoria_pos_resolucao(nc_id)

    nc_atualizada = obter_nc(nc_id)
    if novo_status == "Escalonada":
        responsaveis = obter_responsaveis_nc(nc_id)
        historico = historico_da_nc(nc_id)
        comunicacoes.enviar_comunicacao_escalonamento(
            nc_atualizada, responsaveis, historico=historico, email_destino=email_destino
        )
    elif novo_status == "Dívida Técnica":
        responsaveis = obter_responsaveis_nc(nc_id)
        comunicacoes.enviar_comunicacao_divida_tecnica(nc_atualizada, responsaveis)
    elif novo_status == "Solucionada":
        comunicacoes.enviar_comunicacao_encerramento(nc_atualizada)
