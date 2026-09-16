"""
logic.py
Regras de negócio da ferramenta de Auditoria de Qualidade:
- Criação de checklist
- Execução de auditoria e cálculo de % de aderência
- Abertura automática de Não Conformidades (NC)
- Escalonamento automático por prazo vencido
- Registro de comunicação de NC (simulado em log interno, pronto para
  plugar um envio real de e-mail/webhook em enviar_comunicacao())
"""

from datetime import datetime, timedelta
from database import get_connection, now_str, today_str, PRAZOS_DIAS, NIVEIS_ESCALONAMENTO


# ---------------------------------------------------------------------------
# CHECKLISTS
# ---------------------------------------------------------------------------

def criar_checklist(nome, processo, itens):
    """
    itens: lista de dicts {categoria, descricao, peso}
    Retorna o id do checklist criado.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO checklists (nome, processo, criado_em) VALUES (?, ?, ?)",
        (nome, processo, now_str()),
    )
    checklist_id = cur.lastrowid
    for ordem, item in enumerate(itens):
        cur.execute(
            "INSERT INTO itens_checklist (checklist_id, categoria, descricao, peso, ordem) "
            "VALUES (?, ?, ?, ?, ?)",
            (checklist_id, item["categoria"], item["descricao"], item.get("peso", 1.0), ordem),
        )
    conn.commit()
    conn.close()
    return checklist_id


def listar_checklists():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM checklists ORDER BY id").fetchall()
    conn.close()
    return rows


def listar_itens_checklist(checklist_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM itens_checklist WHERE checklist_id = ? ORDER BY ordem", (checklist_id,)
    ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# AUDITORIA E CÁLCULO DE ADERÊNCIA
# ---------------------------------------------------------------------------

def executar_auditoria(checklist_id, auditor, respostas, responsavel_padrao="Não definido"):
    """
    respostas: lista de dicts:
        {item_id, conforme (1/0/-1), observacao, severidade (se não conforme),
         responsavel (se não conforme)}

    Faz 4 coisas:
    1. Grava a auditoria
    2. Grava cada resposta
    3. Calcula % de aderência ponderado pelo peso do item (ignora N/A)
    4. Abre automaticamente uma NC para cada item não conforme
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO auditorias (checklist_id, auditor, data_auditoria, percentual_aderencia) "
        "VALUES (?, ?, ?, NULL)",
        (checklist_id, auditor, now_str()),
    )
    auditoria_id = cur.lastrowid

    itens = {
        row["id"]: row
        for row in cur.execute(
            "SELECT * FROM itens_checklist WHERE checklist_id = ?", (checklist_id,)
        ).fetchall()
    }

    peso_total = 0.0
    peso_conforme = 0.0
    nc_criadas = []

    for resp in respostas:
        item = itens[resp["item_id"]]
        conforme = resp["conforme"]

        cur.execute(
            "INSERT INTO respostas (auditoria_id, item_id, conforme, observacao) "
            "VALUES (?, ?, ?, ?)",
            (auditoria_id, resp["item_id"], conforme, resp.get("observacao", "")),
        )
        resposta_id = cur.lastrowid

        if conforme != -1:  # -1 = não se aplica, fora do cálculo
            peso_total += item["peso"]
            if conforme == 1:
                peso_conforme += item["peso"]

        if conforme == 0:  # não conforme -> abre NC automaticamente
            severidade = resp.get("severidade", "Média")
            responsavel = resp.get("responsavel", responsavel_padrao)
            nc_id = _abrir_nc(
                cur,
                resposta_id=resposta_id,
                auditoria_id=auditoria_id,
                descricao=f"[{item['categoria']}] {item['descricao']} — {resp.get('observacao', '')}".strip(),
                severidade=severidade,
                responsavel=responsavel,
            )
            nc_criadas.append(nc_id)

    percentual = round((peso_conforme / peso_total) * 100, 2) if peso_total > 0 else 0.0

    cur.execute(
        "UPDATE auditorias SET percentual_aderencia = ? WHERE id = ?",
        (percentual, auditoria_id),
    )

    conn.commit()
    conn.close()

    # Comunica a abertura de cada NC (fora da transação, já com IDs definitivos)
    for nc_id in nc_criadas:
        enviar_comunicacao_abertura(nc_id)

    return {"auditoria_id": auditoria_id, "percentual_aderencia": percentual, "nc_criadas": nc_criadas}


def historico_auditorias(checklist_id=None):
    conn = get_connection()
    if checklist_id:
        rows = conn.execute(
            "SELECT a.*, c.nome as checklist_nome FROM auditorias a "
            "JOIN checklists c ON c.id = a.checklist_id "
            "WHERE a.checklist_id = ? ORDER BY a.data_auditoria DESC",
            (checklist_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT a.*, c.nome as checklist_nome FROM auditorias a "
            "JOIN checklists c ON c.id = a.checklist_id "
            "ORDER BY a.data_auditoria DESC"
        ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# NÃO CONFORMIDADES (NC)
# ---------------------------------------------------------------------------

def _abrir_nc(cur, resposta_id, auditoria_id, descricao, severidade, responsavel):
    prazo_dias = PRAZOS_DIAS.get(severidade, 5)
    data_abertura = today_str()
    prazo_atual = (datetime.now() + timedelta(days=prazo_dias)).strftime("%Y-%m-%d")

    cur.execute(
        "INSERT INTO nao_conformidades "
        "(resposta_id, auditoria_id, descricao, severidade, responsavel, status, "
        " nivel_escalonamento, data_abertura, prazo_atual) "
        "VALUES (?, ?, ?, ?, ?, 'Aberta', 0, ?, ?)",
        (resposta_id, auditoria_id, descricao, severidade, responsavel, data_abertura, prazo_atual),
    )
    nc_id = cur.lastrowid
    cur.execute(
        "INSERT INTO historico_nc (nc_id, data_evento, evento, detalhe) VALUES (?, ?, ?, ?)",
        (nc_id, now_str(), "Abertura", f"NC aberta automaticamente. Responsável: {responsavel}. "
                                        f"Severidade: {severidade}. Prazo: {prazo_atual}."),
    )
    return nc_id


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


def obter_nc(nc_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM nao_conformidades WHERE id = ?", (nc_id,)).fetchone()
    conn.close()
    return row


def historico_da_nc(nc_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM historico_nc WHERE nc_id = ? ORDER BY data_evento", (nc_id,)
    ).fetchall()
    conn.close()
    return rows


def atualizar_status_nc(nc_id, novo_status, acao_corretiva=None, usuario="Sistema"):
    """
    Fluxo esperado: Aberta -> Em Tratativa -> Em Verificação -> Encerrada
    Encerrar só é permitido a partir de 'Em Verificação' (garante que houve
    checagem de eficácia antes do fechamento).
    """
    conn = get_connection()
    cur = conn.cursor()
    nc = cur.execute("SELECT * FROM nao_conformidades WHERE id = ?", (nc_id,)).fetchone()

    if novo_status == "Encerrada" and nc["status"] != "Em Verificação":
        conn.close()
        raise ValueError(
            "Só é possível encerrar uma NC que esteja em 'Em Verificação' "
            "(é preciso confirmar a eficácia da ação antes de fechar)."
        )

    data_encerramento = today_str() if novo_status == "Encerrada" else None
    if acao_corretiva:
        cur.execute(
            "UPDATE nao_conformidades SET status = ?, acao_corretiva = ?, data_encerramento = ? "
            "WHERE id = ?",
            (novo_status, acao_corretiva, data_encerramento, nc_id),
        )
    else:
        cur.execute(
            "UPDATE nao_conformidades SET status = ?, data_encerramento = ? WHERE id = ?",
            (novo_status, data_encerramento, nc_id),
        )

    cur.execute(
        "INSERT INTO historico_nc (nc_id, data_evento, evento, detalhe) VALUES (?, ?, ?, ?)",
        (nc_id, now_str(), f"Status -> {novo_status}", f"Alterado por: {usuario}."
         + (f" Ação: {acao_corretiva}" if acao_corretiva else "")),
    )
    conn.commit()
    conn.close()

    if novo_status == "Encerrada":
        enviar_comunicacao_encerramento(nc_id)

    
def verificar_escalonamentos():
    """
    Varre todas as NCs abertas/em tratativa/em verificação com prazo vencido
    e escalona automaticamente para o próximo nível, reiniciando um novo
    prazo (metade do prazo original) e disparando comunicação.
    Deve ser chamada periodicamente (ex: ao abrir a tela de NCs, ou por um
    agendador). Retorna a lista de NCs escalonadas nesta execução.
    """
    conn = get_connection()
    cur = conn.cursor()
    abertas = cur.execute(
        "SELECT * FROM nao_conformidades WHERE status IN ('Aberta', 'Em Tratativa', 'Em Verificação')"
    ).fetchall()

    hoje = datetime.now().date()
    escalonadas = []

    for nc in abertas:
        prazo = datetime.strptime(nc["prazo_atual"], "%Y-%m-%d").date()
        if hoje > prazo and nc["nivel_escalonamento"] < len(NIVEIS_ESCALONAMENTO) - 1:
            novo_nivel = nc["nivel_escalonamento"] + 1
            dias_extra = max(PRAZOS_DIAS.get(nc["severidade"], 5) // 2, 1)
            novo_prazo = (datetime.now() + timedelta(days=dias_extra)).strftime("%Y-%m-%d")

            cur.execute(
                "UPDATE nao_conformidades SET nivel_escalonamento = ?, prazo_atual = ? WHERE id = ?",
                (novo_nivel, novo_prazo, nc["id"]),
            )
            cur.execute(
                "INSERT INTO historico_nc (nc_id, data_evento, evento, detalhe) VALUES (?, ?, ?, ?)",
                (
                    nc["id"],
                    now_str(),
                    "Escalonamento automático",
                    f"Prazo vencido em {nc['prazo_atual']}. Escalonado de "
                    f"'{NIVEIS_ESCALONAMENTO[nc['nivel_escalonamento']]}' para "
                    f"'{NIVEIS_ESCALONAMENTO[novo_nivel]}'. Novo prazo: {novo_prazo}.",
                ),
            )
            escalonadas.append(nc["id"])

    conn.commit()
    conn.close()

    for nc_id in escalonadas:
        enviar_comunicacao_escalonamento(nc_id)

    return escalonadas


# ---------------------------------------------------------------------------
# COMUNICAÇÃO DE NC
# ---------------------------------------------------------------------------
# Neste protótipo a comunicação é registrada em log interno (tabela
# 'comunicacoes'), visível na aba "Comunicações" da interface. Para um envio
# real, basta implementar o corpo de enviar_email()/enviar_webhook() abaixo
# (ex: smtplib para e-mail corporativo, ou requests.post para Slack/Teams).

def _registrar_comunicacao(nc_id, destinatario, canal, assunto, mensagem):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO comunicacoes (nc_id, data_envio, destinatario, canal, assunto, mensagem) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (nc_id, now_str(), destinatario, canal, assunto, mensagem),
    )
    conn.commit()
    conn.close()
    # Ponto de extensão para envio real:
    # enviar_email(destinatario, assunto, mensagem)
    # enviar_webhook(mensagem)


def enviar_comunicacao_abertura(nc_id):
    nc = obter_nc(nc_id)
    assunto = f"[NC-{nc_id:04d}] Nova não conformidade aberta — Severidade {nc['severidade']}"
    mensagem = (
        f"Uma nova não conformidade foi registrada.\n\n"
        f"Descrição: {nc['descricao']}\n"
        f"Severidade: {nc['severidade']}\n"
        f"Responsável: {nc['responsavel']}\n"
        f"Prazo para tratativa: {nc['prazo_atual']}"
    )
    _registrar_comunicacao(nc_id, nc["responsavel"], "E-mail (simulado)", assunto, mensagem)


def enviar_comunicacao_escalonamento(nc_id):
    nc = obter_nc(nc_id)
    nivel_nome = NIVEIS_ESCALONAMENTO[nc["nivel_escalonamento"]]
    assunto = f"[NC-{nc_id:04d}] ESCALONADA para {nivel_nome} — prazo vencido"
    mensagem = (
        f"A não conformidade abaixo teve o prazo vencido e foi escalonada.\n\n"
        f"Descrição: {nc['descricao']}\n"
        f"Severidade: {nc['severidade']}\n"
        f"Novo nível de escalonamento: {nivel_nome}\n"
        f"Novo prazo: {nc['prazo_atual']}"
    )
    _registrar_comunicacao(nc_id, nivel_nome, "E-mail (simulado)", assunto, mensagem)


def enviar_comunicacao_encerramento(nc_id):
    nc = obter_nc(nc_id)
    assunto = f"[NC-{nc_id:04d}] Encerrada"
    mensagem = (
        f"A não conformidade abaixo foi verificada e encerrada.\n\n"
        f"Descrição: {nc['descricao']}\n"
        f"Ação corretiva: {nc['acao_corretiva']}\n"
        f"Data de encerramento: {nc['data_encerramento']}"
    )
    _registrar_comunicacao(nc_id, nc["responsavel"], "E-mail (simulado)", assunto, mensagem)


def listar_comunicacoes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM comunicacoes ORDER BY data_envio DESC").fetchall()
    conn.close()
    return rows


