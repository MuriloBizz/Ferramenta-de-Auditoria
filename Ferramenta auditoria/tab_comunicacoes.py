"""
tab_comunicacoes.py
Aba Comunicações: log de todos os e-mails enviados pelo sistema, com
duplo clique para ver a mensagem completa.
"""

from tkinter import messagebox, ttk

import comunicacoes


def build(app):
    frame = app.tab_comunicacoes
    cols = ("data", "nc", "destinatario", "canal", "assunto")
    titulos = {"data": "Data/Hora", "nc": "NC", "destinatario": "Destinatário",
               "canal": "Canal", "assunto": "Assunto"}
    larguras = {"data": 150, "nc": 60, "destinatario": 180, "canal": 130, "assunto": 450}

    app.tree_com = ttk.Treeview(frame, columns=cols, show="headings", height=18)
    for c in cols:
        app.tree_com.heading(c, text=titulos[c])
        app.tree_com.column(c, width=larguras[c])
    app.tree_com.pack(fill="both", expand=True, padx=20, pady=10)
    app.tree_com.bind("<Double-1>", lambda e: _ver_mensagem(app))


def refresh(app):
    app._comunicacoes_cache = {c["id"]: c for c in comunicacoes.listar_comunicacoes()}
    app.tree_com.delete(*app.tree_com.get_children())
    for c in app._comunicacoes_cache.values():
        app.tree_com.insert(
            "", "end", iid=str(c["id"]),
            values=(c["data_envio"], c["nc_id"], c["destinatario"], c["canal"], c["assunto"]),
        )


def _ver_mensagem(app):
    sel = app.tree_com.selection()
    if not sel:
        return
    c = app._comunicacoes_cache[int(sel[0])]
    messagebox.showinfo(c["assunto"], c["mensagem"])
