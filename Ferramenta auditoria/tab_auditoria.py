"""
tab_auditoria.py
Aba Nova Auditoria: tabela com os itens do checklist selecionado, onde o
auditor marca Conforme/Não Conforme/Não se Aplica, escreve uma observação
e informa o e-mail do responsável por item, e conclui gerando a auditoria
e a % de aderência.
"""

import tkinter as tk
from tkinter import messagebox, ttk

import auditorias
import checklists
import database
import email_service
from tab_checklists import get_checklist_id

MAPA_STATUS = {"Conforme": 1, "Não Conforme": 0, "Não se Aplica": -1}

COLUNAS_TABELA = [
    ("Item", 40, "w"),
    ("Prioridade", 10, "center"),
    ("C", 4, "center"),
    ("NC", 4, "center"),
    ("N/A", 5, "center"),
    ("Observação", 24, "w"),
    ("E-mail do responsável", 24, "w"),
]


def build(app):
    frame = app.tab_auditoria
    top = ttk.Frame(frame)
    top.pack(fill="x", padx=20, pady=10)

    ttk.Label(top, text="Checklist:").grid(row=0, column=0, sticky="w")
    app.combo_checklist_audit = ttk.Combobox(top, state="readonly", width=55)
    app.combo_checklist_audit.grid(row=0, column=1, padx=10)
    app.combo_checklist_audit.bind("<<ComboboxSelected>>", lambda e: _load_form(app))

    ttk.Label(top, text="Auditor:").grid(row=0, column=2, sticky="w", padx=(20, 0))
    app.entry_auditor = ttk.Entry(top, width=25)
    app.entry_auditor.grid(row=0, column=3, padx=10)

    ttk.Label(top, text="Responsável pelo checklist:").grid(row=1, column=0, sticky="w", pady=(10, 0))
    app.entry_checklist_responsavel = ttk.Entry(top, width=25)
    app.entry_checklist_responsavel.grid(row=1, column=1, padx=10, sticky="w", pady=(10, 0))

    ttk.Label(top, text="E-mail do responsável:").grid(row=1, column=2, sticky="w", padx=(20, 0), pady=(10, 0))
    app.entry_checklist_email = ttk.Entry(top, width=30)
    app.entry_checklist_email.grid(row=1, column=3, padx=10, pady=(10, 0))

    container = ttk.Frame(frame)
    container.pack(fill="both", expand=True, padx=20, pady=10)
    canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    app.audit_items_frame = ttk.Frame(canvas)
    app.audit_items_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=app.audit_items_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    ttk.Button(
        frame, text="Concluir auditoria e calcular aderência",
        command=lambda: _submit(app),
    ).pack(pady=10)

    app._audit_widgets = []
    refresh_checklists(app)


def refresh_checklists(app):
    valores = [f"{c['id']} - {c['nome']}" for c in checklists.listar_checklists()]
    app.combo_checklist_audit["values"] = valores
    if not valores:
        app.combo_checklist_audit.set("")


def _load_form(app):
    for w in app.audit_items_frame.winfo_children():
        w.destroy()
    app._audit_widgets = []

    cid = get_checklist_id(app.combo_checklist_audit)
    if cid is None:
        app.entry_checklist_responsavel.delete(0, "end")
        app.entry_checklist_email.delete(0, "end")
        return
    
    checklist = checklists.obter_checklist(cid)
    app.entry_checklist_responsavel.delete(0, "end")
    app.entry_checklist_responsavel.insert(0, checklist["responsavel"] or "")
    app.entry_checklist_email.delete(0, "end")
    app.entry_checklist_email.insert(0, checklist["email_responsavel"] or "")

    ttk.Label(
        app.audit_items_frame,
        text="Legenda:  C = Conforme   |   NC = Não Conforme   |   N/A = Não se Aplica",
        font=("TkDefaultFont", 8, "italic"), foreground="gray",
    ).grid(row=0, column=0, columnspan=7, sticky="w", pady=(0, 8))

    for col, (texto, largura, ancora) in enumerate(COLUNAS_TABELA):
        sticky = "w" if ancora == "w" else ""
        ttk.Label(
            app.audit_items_frame, text=texto, font=("TkDefaultFont", 9, "bold"),
            width=largura, anchor=ancora,
        ).grid(row=1, column=col, sticky=sticky, padx=4, pady=(0, 4))

    row_idx = 2
    categoria_atual = None
    for item in checklists.listar_itens_checklist(cid):
        if item["categoria"] != categoria_atual:
            categoria_atual = item["categoria"]
            ttk.Label(
                app.audit_items_frame, text=categoria_atual, font=("TkDefaultFont", 9, "bold"),
            ).grid(row=row_idx, column=0, columnspan=7, sticky="w", pady=(14, 4))
            row_idx += 1

        ttk.Label(
            app.audit_items_frame, text=item["descricao"], wraplength=260,
            justify="left", anchor="w", width=40,
        ).grid(row=row_idx, column=0, sticky="w", padx=4, pady=3)

        ttk.Label(
            app.audit_items_frame, text=database.PRIORIDADES[item["prioridade"]],
            width=10, anchor="center",
        ).grid(row=row_idx, column=1, padx=4)

        status_var = tk.StringVar(value="Conforme")
        ttk.Radiobutton(app.audit_items_frame, text="C", variable=status_var, value="Conforme").grid(
            row=row_idx, column=2, padx=4
        )
        ttk.Radiobutton(app.audit_items_frame, text="NC", variable=status_var, value="Não Conforme").grid(
            row=row_idx, column=3, padx=4
        )
        ttk.Radiobutton(app.audit_items_frame, text="N/A", variable=status_var, value="Não se Aplica").grid(
            row=row_idx, column=4, padx=4
        )

        obs_entry = ttk.Entry(app.audit_items_frame, width=24)
        obs_entry.grid(row=row_idx, column=5, padx=4, sticky="w")

        email_entry = ttk.Entry(app.audit_items_frame, width=24)
        email_entry.insert(0, item["email_responsavel"] or "")
        email_entry.grid(row=row_idx, column=6, padx=4, sticky="w")

        app._audit_widgets.append(
            {
                "item_id": item["id"],
                "status_var": status_var,
                "obs_entry": obs_entry,
                "email_entry": email_entry,
                "responsavel": item["responsavel"],
            }
        )
        row_idx += 1


def _submit(app):
    if not email_service.configurado():
        messagebox.showwarning(
            "Atenção",
            "Configure o e-mail remetente e a senha de aplicativo na aba "
            "'Configurações' antes de concluir uma auditoria — as NCs "
            "precisam ser comunicadas automaticamente por e-mail.",
        )
        return

    cid = get_checklist_id(app.combo_checklist_audit)
    auditor = app.entry_auditor.get().strip()
    checklist_responsavel = app.entry_checklist_responsavel.get().strip()
    checklist_email = app.entry_checklist_email.get().strip()

    if cid is None or not app._audit_widgets:
        messagebox.showwarning("Atenção", "Selecione um checklist antes de iniciar a auditoria.")
        return
    if not auditor:
        messagebox.showwarning("Atenção", "Informe o nome do auditor.")
        return
    if not checklist_responsavel or not checklist_email:
        messagebox.showwarning(
            "Atenção", "Informe o nome e o e-mail do responsável pelo checklist."
        )
        return

    checklists.atualizar_responsavel_checklist(cid, checklist_responsavel, checklist_email)

    respostas = []
    for w in app._audit_widgets:
        conforme = MAPA_STATUS[w["status_var"].get()]
        observacao = w["obs_entry"].get().strip()
        email = w["email_entry"].get().strip()

        if conforme == 0 and not email:
            messagebox.showwarning(
                "Atenção", "Informe o e-mail do responsável para o item marcado como Não Conforme."
            )
            return

        respostas.append(
            {
                "item_id": w["item_id"],
                "conforme": conforme,
                "observacao": observacao,
                "email_responsavel": email,
                "responsavel": w["responsavel"],
            }
        )

    resultado = auditorias.executar_auditoria(cid, auditor, respostas)
    messagebox.showinfo(
        "Auditoria concluída",
        f"% de aderência: {resultado['percentual_aderencia']}%\n"
        f"Não conformidades abertas automaticamente: {len(resultado['nc_criadas'])}",
    )
    app.refresh_all()
    app.notebook.select(app.tab_dashboard)
