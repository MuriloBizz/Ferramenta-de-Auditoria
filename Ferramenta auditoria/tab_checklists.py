"""
tab_checklists.py
Aba Checklists: escolhe um checklist e lista seus itens, com categoria,
prioridade, prazo de resolução, responsável e e-mail cadastrados.
"""

from tkinter import ttk

import checklists
import database


def build(app):
    frame = app.tab_checklists
    top = ttk.Frame(frame)
    top.pack(fill="x", padx=20, pady=10)
    ttk.Label(top, text="Checklist:").pack(side="left")

    app.combo_checklist_view = ttk.Combobox(top, state="readonly", width=60)
    app.combo_checklist_view.pack(side="left", padx=10)
    app.combo_checklist_view.bind("<<ComboboxSelected>>", lambda e: _load_items(app))

    cols = ("id", "categoria", "descricao", "prioridade", "prazo_dias", "responsavel", "email")
    titulos = {
        "id": "Ordem", "categoria": "Categoria", "descricao": "Item do checklist",
        "prioridade": "Prioridade", "prazo_dias": "Prazo p/ resolução",
        "responsavel": "Responsável", "email": "E-mail",
    }
    larguras = {"id": 60, "categoria": 280, "descricao": 550, "prioridade": 100,
                "prazo_dias": 140, "responsavel": 200, "email": 300}

    app.tree_itens = ttk.Treeview(frame, columns=cols, show="headings", height=18)
    for c in cols:
        app.tree_itens.heading(c, text=titulos[c])
        anchor = "center" if c in ("id", "prioridade", "prazo_dias") else "w"
        app.tree_itens.column(c, width=larguras[c], anchor=anchor)
    app.tree_itens.pack(fill="both", expand=True, padx=20, pady=10)


def refresh(app):
    app._checklists_cache = checklists.listar_checklists()
    valores = [f"{c['id']} - {c['nome']}" for c in app._checklists_cache]
    atual = app.combo_checklist_view.get()
    app.combo_checklist_view["values"] = valores
    if valores and not atual:
        app.combo_checklist_view.current(0)
        _load_items(app)


def _load_items(app):
    cid = get_checklist_id(app.combo_checklist_view)
    app.tree_itens.delete(*app.tree_itens.get_children())
    if cid is None:
        return
    for item in checklists.listar_itens_checklist(cid):
        app.tree_itens.insert(
            "", "end",
            values=(
                item["ordem"], item["categoria"], item["descricao"],
                database.PRIORIDADES[item["prioridade"]],
                f"{database.PRAZOS_DIAS[item['prioridade']]} dias úteis",
                item["responsavel"], item["email_responsavel"],
            ),
        )


def get_checklist_id(combo):
    valor = combo.get()
    return int(valor.split(" - ")[0]) if valor else None
