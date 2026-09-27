"""
tab_dashboard.py
Aba Dashboard: cartões-resumo, histórico de auditorias e a janela de
detalhe que abre ao dar duplo clique numa auditoria (mostra os itens
avaliados, a avaliação, o responsável e a aderência daquela versão).
"""

import tkinter as tk
from tkinter import ttk

import auditorias
import database
import nao_conformidades as ncs


def build(app):
    frame = app.tab_dashboard
    cards = ttk.Frame(frame)
    cards.pack(fill="x", padx=20, pady=20)

    app.card_aderencia = _make_card(cards, "Última aderência")
    app.card_reportadas = _make_card(cards, "NCs reportadas")
    app.card_escalonadas = _make_card(cards, "NCs escalonadas")
    app.card_solucionadas = _make_card(cards, "NCs solucionadas")
    app.card_dividas = _make_card(cards, "Dívidas técnicas")

    ttk.Label(frame, text="Histórico de auditorias").pack(anchor="w", padx=20, pady=(10, 0))
    ttk.Label(
        frame, text="(dê duplo clique numa auditoria para ver os itens avaliados)",
        foreground="gray", font=("TkDefaultFont", 8, "italic"),
    ).pack(anchor="w", padx=20)

    cols = ("data", "auditoria", "auditor", "aderencia")
    app.tree_auditorias = ttk.Treeview(frame, columns=cols, show="headings", height=10)
    for c, label, w in [
        ("data", "Data", 160), ("auditoria", "Auditoria", 380),
        ("auditor", "Auditor", 200), ("aderencia", "% Aderência", 120),
    ]:
        app.tree_auditorias.heading(c, text=label)
        app.tree_auditorias.column(c, width=w)
    app.tree_auditorias.pack(fill="both", expand=True, padx=20, pady=10)
    app.tree_auditorias.bind("<Double-1>", lambda e: _abrir_detalhe(app))


def _make_card(parent, titulo):
    card = ttk.LabelFrame(parent, text=titulo)
    card.pack(side="left", padx=10, fill="both", expand=True)
    lbl = ttk.Label(card, text="—", anchor="center")
    lbl.pack(fill="both", expand=True, pady=10)
    return lbl


def refresh(app):
    lista_auditorias = auditorias.historico_auditorias()
    app.card_aderencia.config(
        text=f"{lista_auditorias[0]['percentual_aderencia']}%" if lista_auditorias else "—"
    )

    lista_ncs = ncs.listar_ncs()
    contagem = {status: 0 for status in database.STATUS_NC}
    for nc in lista_ncs:
        contagem[nc["status"]] += 1

    app.card_reportadas.config(text=str(contagem["Reportada"]))
    app.card_escalonadas.config(text=str(contagem["Escalonada"]))
    app.card_solucionadas.config(text=str(contagem["Solucionada"]))
    app.card_dividas.config(text=str(contagem["Dívida Técnica"]))

    app.tree_auditorias.delete(*app.tree_auditorias.get_children())
    app._auditorias_cache = {}
    for a in lista_auditorias:
        iid = app.tree_auditorias.insert(
            "", "end", values=(a["data_auditoria"], a["nome"], a["auditor"], f"{a['percentual_aderencia']}%")
        )
        app._auditorias_cache[iid] = a["id"]


def _abrir_detalhe(app):
    sel = app.tree_auditorias.selection()
    if not sel:
        return
    auditoria_id = app._auditorias_cache.get(sel[0])
    if auditoria_id is not None:
        DetalheAuditoriaWindow(app, auditoria_id)


class DetalheAuditoriaWindow(tk.Toplevel):
    def __init__(self, master, auditoria_id):
        super().__init__(master)
        self.auditoria_id = auditoria_id
        self.title(f"Detalhe da Auditoria #{auditoria_id}")
        self.geometry("900x560")
        self._build()

    def _build(self):
        todas = {a["id"]: a for a in auditorias.historico_auditorias()}
        auditoria = todas.get(self.auditoria_id)
        if not auditoria:
            ttk.Label(self, text="Auditoria não encontrada.").pack(padx=15, pady=15)
            return

        ttk.Label(
            self,
            text=(
                f"Auditoria: {auditoria['nome']}   |   "
                f"Checklist: {auditoria['checklist_nome']}   |   "
                f"Auditor (responsável): {auditoria['auditor']}   |   "
                f"Data: {auditoria['data_auditoria']}   |   "
                f"Aderência: {auditoria['percentual_aderencia']}%"
            ),
            font=("TkDefaultFont", 9, "bold"),
            wraplength=860, justify="left",
        ).pack(anchor="w", padx=15, pady=4)

        cols = ("categoria", "descricao", "prioridade", "responsavel", "avaliacao", "observacao")
        larguras = {"categoria": 160, "descricao": 320, "prioridade": 80,
                    "responsavel": 140, "avaliacao": 110, "observacao": 220}
        titulos = {"categoria": "Categoria", "descricao": "Item", "prioridade": "Prioridade",
                   "responsavel": "Responsável", "avaliacao": "Avaliação", "observacao": "Observação"}

        tree = ttk.Treeview(self, columns=cols, show="headings", height=20)
        for c in cols:
            tree.heading(c, text=titulos[c])
            tree.column(c, width=larguras[c])
        tree.pack(fill="both", expand=True, padx=15, pady=10)

        mapa_avaliacao = {1: "Conforme", 0: "Não Conforme", -1: "Não se Aplica"}
        for r in auditorias.respostas_da_auditoria(self.auditoria_id):
            tree.insert(
                "", "end",
                values=(
                    r["categoria"], r["descricao"], database.PRIORIDADES[r["prioridade"]],
                    r["responsavel"], mapa_avaliacao[r["conforme"]], r["observacao"] or "",
                ),
            )
