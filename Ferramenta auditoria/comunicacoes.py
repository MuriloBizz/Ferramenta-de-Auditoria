"""
comunicacoes.py
Monta e envia as mensagens de e-mail ligadas ao ciclo de vida de uma NC
(abertura, escalonamento, dívida técnica e encerramento), registrando cada
envio na tabela 'comunicacoes'.
"""

from database import PRIORIDADES, get_connection, now_str
from email_service import enviar_email


def _registrar_e_enviar_email(nc_id, destinatario, assunto, mensagem):
    enviar_email(destinatario, assunto, mensagem)

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO comunicacoes (nc_id, data_envio, destinatario, canal, assunto, mensagem)
        VALUES (?, ?, ?, 'E-mail', ?, ?)
        """,
        (nc_id, now_str(), destinatario, assunto, mensagem),
    )
    conn.commit()
    conn.close()


def enviar_comunicacao_abertura(nc):
    assunto = f"[NC-{nc['id']:04d}] Nova não conformidade"
    mensagem = (
        f"Uma nova não conformidade foi registrada.\n\n"
        f"Descrição: {nc['descricao']}\n"
        f"Prioridade: {PRIORIDADES[nc['prioridade']]}\n"
        f"Responsável: {nc['responsavel']}\n"
        f"Prazo: {nc['prazo_atual']}"
    )
    _registrar_e_enviar_email(nc["id"], nc["email_responsavel"], assunto, mensagem)


def enviar_comunicacao_escalonamento(nc, responsaveis, historico=None, email_destino=None):
    assunto = f"[NC-{nc['id']:04d}] NC escalonada — Prioridade {PRIORIDADES[nc['prioridade']]}"

    bloco_historico = ""
    if historico:
        eventos = "\n".join(
            f"[{h['data_evento']}] {h['evento']} — {h['detalhe']}" for h in historico
        )
        bloco_historico = f"\n\nHistórico da NC:\n{eventos}"

    mensagem = (
        f"A não conformidade abaixo teve seu prazo vencido e foi escalonada.\n\n"
        f"Descrição: {nc['descricao']}\n"
        f"Prioridade: {PRIORIDADES[nc['prioridade']]}\n"
        f"Responsável pelo item: {responsaveis['responsavel_item']}\n"
        f"Novo prazo: {nc['prazo_atual']}\n\n"
        f"Responsável pelo checklist: {responsaveis['responsavel_checklist']}"
        f"{bloco_historico}"
    )

    destinatarios = {responsaveis["email_item"]}
    if email_destino:
        destinatarios.add(email_destino)
    else:
        destinatarios.add(responsaveis["email_checklist"])

    for email in destinatarios:
        _registrar_e_enviar_email(nc["id"], email, assunto, mensagem)


def enviar_comunicacao_divida_tecnica(nc, responsaveis):
    assunto = f"[NC-{nc['id']:04d}] Fechamento como Dívida Técnica"
    mensagem = (
        f"A não conformidade abaixo não foi solucionada dentro dos dois "
        f"períodos disponibilizados.\n\n"
        f"Descrição: {nc['descricao']}\n"
        f"Prioridade: {PRIORIDADES[nc['prioridade']]}\n\n"
        f"A NC foi encerrada como Dívida Técnica.\n\n"
        f"Responsável pelo checklist: {responsaveis['responsavel_checklist']}"
    )
    _registrar_e_enviar_email(nc["id"], responsaveis["email_checklist"], assunto, mensagem)


def enviar_comunicacao_encerramento(nc):
    assunto = f"[NC-{nc['id']:04d}] NC solucionada"
    mensagem = (
        f"A não conformidade abaixo foi solucionada.\n\n"
        f"Descrição: {nc['descricao']}\n"
        f"Prioridade: {PRIORIDADES[nc['prioridade']]}\n"
        f"Ação corretiva: {nc['acao_corretiva']}\n"
        f"Data de solução: {nc['data_encerramento']}"
    )
    _registrar_e_enviar_email(nc["id"], nc["email_responsavel"], assunto, mensagem)


def listar_comunicacoes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM comunicacoes ORDER BY data_envio DESC").fetchall()
    conn.close()
    return rows


def comunicacoes_da_nc(nc_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM comunicacoes WHERE nc_id = ? ORDER BY data_envio", (nc_id,)
    ).fetchall()
    conn.close()
    return rows
