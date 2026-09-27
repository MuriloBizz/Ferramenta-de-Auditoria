"""
tab_ncs.py
Aba Não Conformidades: lista as NCs com filtro por status, e a janela de
detalhe onde se vê o histórico de status e de comunicações, e se avança a
NC para Solucionada, Escalonada ou Dívida Técnica.
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk

import comunicacoes
import database
import nao_conformidades as ncs

FILTROS_STATUS = ["Todas"] + database.STATUS_NC


def build(app):
    frame = app.tab_ncs
    top = ttk.Frame(frame)
    top.pack(fill="x", padx=20, pady=10)

    ttk.Label(top, text="Filtrar por status:").pack(side="left")
    app.combo_filtro_status = ttk.Combobox(top, state="readonly", width=20, values=FILTROS_STATUS)
    app.combo_filtro_status.set("Todas")
    app.combo_filtro_status.pack(side="left", padx=10)
    app.combo_filtro_status.bind("<<ComboboxSelected>>", lambda e: refresh(app))

    ttk.Button(top, text="Verificar prazos vencidos", command=lambda: _verificar_prazos(app)).pack(
        side="left", padx=20
    )

    cols = ("id", "descricao", "prioridade", "responsavel", "status", "prazo")
    titulos = {"id": "ID", "descricao": "Descrição", "prioridade": "Prioridade",
               "responsavel": "Responsável", "status": "Status", "prazo": "Prazo"}
    larguras = {"id": 50, "descricao": 400, "prioridade": 90, "responsavel": 150, "status": 130, "prazo": 100}

    app.tree_ncs = ttk.Treeview(frame, columns=cols, show="headings", height=14)
    for c in cols:
        app.tree_ncs.heading(c, text=titulos[c])
        app.tree_ncs.column(c, width=larguras[c], anchor="w" if c == "descricao" else "center")
    app.tree_ncs.pack(fill="both", expand=True, padx=20, pady=10)
    app.tree_ncs.bind("<Double-1>", lambda e: _abrir_detalhe(app))

    bottom = ttk.Frame(frame)
    bottom.pack(fill="x", padx=20, pady=(0, 15))
    ttk.Button(bottom, text="Ver histórico / avançar status", command=lambda: _abrir_detalhe(app)).pack(side="left")


def refresh(app):
    filtro = app.combo_filtro_status.get() if hasattr(app, "combo_filtro_status") else "Todas"
    status = None if filtro in ("Todas", "") else filtro

    app.tree_ncs.delete(*app.tree_ncs.get_children())
    for nc in ncs.listar_ncs(status):
        app.tree_ncs.insert(
            "", "end", iid=str(nc["id"]),
            values=(
                nc["id"], nc["descricao"][:90], database.PRIORIDADES[nc["prioridade"]],
                nc["responsavel"], nc["status"], nc["prazo_atual"],
            ),
        )


def _verificar_prazos(app):
    vencidas = ncs.verificar_prazos_vencidos()
    refresh(app)
    if vencidas:
        messagebox.showinfo(
            "Prazos vencidos",
            f"{len(vencidas)} NC(s) possuem prazo vencido.\nAbra cada NC para decidir a próxima ação.",
        )
    else:
        messagebox.showinfo("Prazos", "Nenhuma NC possui prazo vencido.")


def _abrir_detalhe(app):
    sel = app.tree_ncs.selection()
    if not sel:
        messagebox.showwarning("Atenção", "Selecione uma não conformidade na lista.")
        return
    DetalheNCWindow(app, int(sel[0]))


class DetalheNCWindow(tk.Toplevel):
    def __init__(self, master_app, nc_id):
        super().__init__(master_app)
        self.master_app = master_app
        self.nc_id = nc_id
        self.title(f"Não Conformidade NC-{nc_id:04d}")
        self.geometry("620x640")
        self._build()

    def _build(self):
        nc = ncs.obter_nc(self.nc_id)
        pad = {"padx": 15, "pady": 4}

        prazo = datetime.strptime(nc["prazo_atual"], "%Y-%m-%d").date()
        prazo_vencido = datetime.now().date() >= prazo

        ttk.Label(self, text=nc["descricao"], wraplength=580, justify="left").pack(anchor="w", **pad)

        info = ttk.Frame(self)
        info.pack(anchor="w", **pad)
        ttk.Label(
            info,
            text=(
                f"Prioridade: {database.PRIORIDADES[nc['prioridade']]}   |   "
                f"Responsável: {nc['responsavel']}   |   "
                f"Status atual: {nc['status']}   |   "
                f"Prazo: {nc['prazo_atual']}"
            ),
        ).pack(anchor="w")

        ttk.Label(self, text="Histórico:").pack(anchor="w", **pad)
        hist_box = tk.Text(self, height=8, wrap="word")
        hist_box.pack(fill="x", padx=15)
        for h in ncs.historico_da_nc(self.nc_id):
            hist_box.insert("end", f"[{h['data_evento']}] {h['evento']}\n    {h['detalhe']}\n\n")
        hist_box.config(state="disabled")

        ttk.Label(self, text="Histórico de comunicações:").pack(anchor="w", **pad)
        com_box = tk.Text(self, height=6, wrap="word")
        com_box.pack(fill="x", padx=15)
        registros = comunicacoes.comunicacoes_da_nc(self.nc_id)
        if registros:
            for c in registros:
                com_box.insert("end", f"[{c['data_envio']}] Para: {c['destinatario']} — {c['assunto']}\n")
        else:
            com_box.insert("end", "Nenhuma comunicação registrada até o momento.")
        com_box.config(state="disabled")

        ttk.Label(self, text="Avançar status:").pack(anchor="w", **pad)
        actions = ttk.Frame(self)
        actions.pack(anchor="w", **pad)

        if nc["status"] == "Reportada":
            ttk.Button(actions, text="Solucionar", command=lambda: self._avancar("Solucionada")).pack(
                side="left", padx=5
            )
            if prazo_vencido:
                ttk.Button(actions, text="Escalonar", command=lambda: self._avancar("Escalonada")).pack(
                    side="left", padx=5
                )
        elif nc["status"] == "Escalonada":
            ttk.Button(actions, text="Solucionar", command=lambda: self._avancar("Solucionada")).pack(
                side="left", padx=5
            )
            if prazo_vencido:
                ttk.Button(actions, text="Dívida Técnica", command=lambda: self._avancar("Dívida Técnica")).pack(
                    side="left", padx=5
                )
        else:
            ttk.Label(actions, text=f"NC finalizada como: {nc['status']}").pack(side="left")

    def _avancar(self, novo_status):
        usuario = simpledialog.askstring("Responsável pela ação", "Seu nome:", parent=self)
        if not usuario:
            return

        acao = None
        email_escalonamento = None

        if novo_status == "Solucionada":
            acao = simpledialog.askstring(
                "Ação corretiva",
                "Descreva a ação corretiva aplicada e a verificação de eficácia:",
                parent=self,
            )
            if not acao:
                messagebox.showwarning("Atenção", "É necessário descrever a ação corretiva.")
                return

        if novo_status == "Escalonada":
            if not messagebox.askyesno(
                "Confirmar escalonamento", "O prazo está vencido.\n\nDeseja realmente escalonar esta NC?"
            ):
                return
            email_escalonamento = simpledialog.askstring(
                "E-mail para escalonamento",
                "Informe o e-mail para o qual a NC deve ser escalonada:",
                parent=self,
            )
            if not email_escalonamento:
                messagebox.showwarning("Atenção", "É necessário informar um e-mail para escalonar.")
                return

        if novo_status == "Dívida Técnica":
            if not messagebox.askyesno(
                "Confirmar Dívida Técnica",
                "O segundo prazo está vencido.\n\nDeseja realmente encerrar esta NC como Dívida Técnica?",
            ):
                return

        try:
            ncs.atualizar_status_nc(
                self.nc_id, novo_status, acao_corretiva=acao, usuario=usuario,
                email_destino=email_escalonamento,
            )
            messagebox.showinfo("Sucesso", f"NC atualizada para '{novo_status}'.")
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        self.destroy()
        self.master_app.refresh_all()
