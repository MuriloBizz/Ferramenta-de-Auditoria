"""
gui.py
Interface gráfica própria (Tkinter) da Ferramenta de Auditoria de Qualidade.

Abas:
 1. Checklists       - visualizar checklists e itens cadastrados
 2. Nova Auditoria   - executar auditoria marcando C/NC item a item
 3. Não Conformidades- acompanhar, tratar e escalonar NCs até a resolução
 4. Comunicações     - trilha de comunicações disparadas automaticamente
 5. Dashboard        - visão geral de aderência e NCs
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os

import database
import logic


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ferramenta de Auditoria de Qualidade")
        self.geometry("1150x680")
        self.minsize(950, 600)

        if not os.path.exists(database.DB_PATH):
            database.init_db()

        self._build_layout()
        self.refresh_all()

    # ------------------------------------------------------------------
    def _build_layout(self):
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(
            header, text="Auditoria de Qualidade", padding=14
        ).pack(side="left")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_checklists = ttk.Frame(self.notebook)
        self.tab_auditoria = ttk.Frame(self.notebook)
        self.tab_ncs = ttk.Frame(self.notebook)
        self.tab_comunicacoes = ttk.Frame(self.notebook)
        self.tab_dashboard = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_checklists, text="Checklists")
        self.notebook.add(self.tab_auditoria, text="Nova Auditoria")
        self.notebook.add(self.tab_ncs, text="Não Conformidades")
        self.notebook.add(self.tab_comunicacoes, text="Comunicações")

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())

        self._build_dashboard_tab()
        self._build_checklists_tab()
        self._build_auditoria_tab()
        self._build_ncs_tab()
        self._build_comunicacoes_tab()

    def refresh_all(self):
        logic.verificar_escalonamentos()
        self._refresh_dashboard()
        self._refresh_checklists()
        self._refresh_ncs()
        self._refresh_comunicacoes()
        self.carregar_checklists_audit()

    # ------------------------------------------------------------------
    # DASHBOARD
    # ------------------------------------------------------------------
    def _build_dashboard_tab(self):
        frame = self.tab_dashboard
        cards = ttk.Frame(frame)
        cards.pack(fill="x", padx=20, pady=20)

        self.card_aderencia = self._make_card(cards, "Última aderência", "—")
        self.card_abertas = self._make_card(cards, "NCs abertas", "—")
        self.card_tratativa = self._make_card(cards, "Em tratativa/verificação", "—")
        self.card_encerradas = self._make_card(cards, "NCs encerradas", "—")

        ttk.Label(frame, text="Histórico de auditorias").pack(
            anchor="w", padx=20, pady=(10, 0)
        )
        cols = ("data", "checklist", "auditor", "aderencia")
        self.tree_auditorias = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for c, label, w in [
            ("data", "Data", 160), ("checklist", "Checklist", 380),
            ("auditor", "Auditor", 200), ("aderencia", "% Aderência", 120),
        ]:
            self.tree_auditorias.heading(c, text=label)
            self.tree_auditorias.column(c, width=w)
        self.tree_auditorias.pack(fill="both", expand=True, padx=20, pady=10)

    def _make_card(self, parent, titulo, valor):
        card = ttk.LabelFrame(parent, text=titulo)
        card.pack(side="left", padx=10, fill="both", expand=True)
        lbl = ttk.Label(card, text=valor, anchor="center")
        lbl.pack(fill="both", expand=True, pady=10)
        return lbl

    def _refresh_dashboard(self):
        auditorias = logic.historico_auditorias()
        if auditorias:
            self.card_aderencia.config(text=f"{auditorias[0]['percentual_aderencia']}%")
        else:
            self.card_aderencia.config(text="—")

        ncs = logic.listar_ncs()
        abertas = sum(1 for nc in ncs if nc["status"] == "Aberta")
        tratativa = sum(1 for nc in ncs if nc["status"] in ("Em Tratativa", "Em Verificação"))
        encerradas = sum(1 for nc in ncs if nc["status"] == "Encerrada")
        self.card_abertas.config(text=str(abertas))
        self.card_tratativa.config(text=str(tratativa))
        self.card_encerradas.config(text=str(encerradas))

        self.tree_auditorias.delete(*self.tree_auditorias.get_children())
        for a in auditorias:
            self.tree_auditorias.insert(
                "", "end",
                values=(a["data_auditoria"], a["checklist_nome"], a["auditor"], f"{a['percentual_aderencia']}%"),
            )

    # ------------------------------------------------------------------
    # CHECKLISTS
    # ------------------------------------------------------------------
    def _build_checklists_tab(self):
        frame = self.tab_checklists
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=20, pady=10)
        ttk.Label(top, text="Checklist:").pack(side="left")
        self.combo_checklist_view = ttk.Combobox(top, state="readonly", width=60)
        self.combo_checklist_view.pack(side="left", padx=10)
        self.combo_checklist_view.bind("<<ComboboxSelected>>", lambda e: self._load_checklist_items())

        cols = ("categoria", "descricao", "peso")
        self.tree_itens = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        self.tree_itens.heading("categoria", text="Categoria")
        self.tree_itens.heading("descricao", text="Item do checklist")
        self.tree_itens.heading("peso", text="Peso")
        self.tree_itens.column("categoria", width=280)
        self.tree_itens.column("descricao", width=650)
        self.tree_itens.column("peso", width=80, anchor="center")
        self.tree_itens.pack(fill="both", expand=True, padx=20, pady=10)

    def _refresh_checklists(self):
        self._checklists_cache = logic.listar_checklists()
        valores = [f"{c['id']} - {c['nome']}" for c in self._checklists_cache]
        atual = self.combo_checklist_view.get()
        self.combo_checklist_view["values"] = valores
        if valores and not atual:
            self.combo_checklist_view.current(0)
            self._load_checklist_items()

    def _get_checklist_id_selecionado(self, combo):
        val = combo.get()
        if not val:
            return None
        return int(val.split(" - ")[0])

    def _load_checklist_items(self):
        cid = self._get_checklist_id_selecionado(self.combo_checklist_view)
        self.tree_itens.delete(*self.tree_itens.get_children())
        if cid is None:
            return
        for item in logic.listar_itens_checklist(cid):
            self.tree_itens.insert("", "end", values=(item["categoria"], item["descricao"], item["peso"]))

    # ------------------------------------------------------------------
    # NOVA AUDITORIA
    # ------------------------------------------------------------------
    def _build_auditoria_tab(self):
        frame = self.tab_auditoria
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=20, pady=10)

        ttk.Label(top, text="Checklist:").grid(row=0, column=0, sticky="w")
        self.combo_checklist_audit = ttk.Combobox(top, state="readonly", width=55)
        self.combo_checklist_audit.grid(row=0, column=1, padx=10)
        self.combo_checklist_audit.bind("<<ComboboxSelected>>", lambda e: self._load_audit_form())

        ttk.Label(top, text="Auditor:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.entry_auditor = ttk.Entry(top, width=25)
        self.entry_auditor.grid(row=0, column=3, padx=10)

        # área rolável com os itens
        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True, padx=20, pady=10)
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.audit_items_frame = ttk.Frame(canvas)
        self.audit_items_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.audit_items_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn = ttk.Button(
            frame, text="Concluir auditoria e calcular aderência",
            command=self._submit_auditoria,
        )
        btn.pack(pady=10)

        self._audit_widgets = []  # lista de dicts com referências aos widgets por item
        self.carregar_checklists_audit()        
        
    def carregar_checklists_audit(self):
        
        checklists = logic.listar_checklists()  # Ou a função correspondente no seu logic.py
        
        if checklists:
            # Formata o texto exibido no combo: "ID - Nome do Checklist"
            valores = [f"{c['id']} - {c['nome']}" for c in checklists]
            self.combo_checklist_audit['values'] = valores
        else:
            self.combo_checklist_audit['values'] = []
            self.combo_checklist_audit.set("")
            
    def _load_audit_form(self):
        for w in self.audit_items_frame.winfo_children():
            w.destroy()
        self._audit_widgets = []

        cid = self._get_checklist_id_selecionado(self.combo_checklist_audit)
        if cid is None:
            return

        itens = logic.listar_itens_checklist(cid)
        categoria_atual = None
        for item in itens:
            if item["categoria"] != categoria_atual:
                categoria_atual = item["categoria"]
                ttk.Label(
                    self.audit_items_frame, text=categoria_atual
                ).pack(anchor="w", pady=(14, 4))

            row = ttk.Frame(self.audit_items_frame, padding=8)
            row.pack(fill="x", pady=3)

            ttk.Label(row, text=item["descricao"], wraplength=480, justify="left", anchor="w").grid(
                row=0, column=0, rowspan=3, sticky="w", padx=(0, 10)
            )

            status_var = tk.StringVar(value="Conforme")
            for i, opt in enumerate(["Conforme", "Não Conforme", "Não se Aplica"]):
                ttk.Radiobutton(row, text=opt, variable=status_var, value=opt).grid(
                    row=0, column=1 + i, sticky="w"
                )

            obs_entry = ttk.Entry(row, width=40)
            obs_entry.grid(row=1, column=1, columnspan=3, sticky="w", pady=(4, 0))
            obs_entry.insert(0, "Observação (opcional)")

            sev_combo = ttk.Combobox(row, values=["Baixa", "Média", "Alta"], width=10, state="readonly")
            sev_combo.set("Média")
            sev_combo.grid(row=2, column=1, sticky="w", pady=(4, 0))

            resp_entry = ttk.Entry(row, width=25)
            resp_entry.grid(row=2, column=2, columnspan=2, sticky="w", pady=(4, 0))
            resp_entry.insert(0, "Responsável (se NC)")

            self._audit_widgets.append(
                {
                    "item_id": item["id"],
                    "status_var": status_var,
                    "obs_entry": obs_entry,
                    "sev_combo": sev_combo,
                    "resp_entry": resp_entry,
                }
            )

    def _submit_auditoria(self):
        cid = self._get_checklist_id_selecionado(self.combo_checklist_audit)
        auditor = self.entry_auditor.get().strip()
        if cid is None or not self._audit_widgets:
            messagebox.showwarning("Atenção", "Selecione um checklist antes de iniciar a auditoria.")
            return
        if not auditor:
            messagebox.showwarning("Atenção", "Informe o nome do auditor.")
            return

        mapa = {"Conforme": 1, "Não Conforme": 0, "Não se Aplica": -1}
        respostas = []
        for w in self._audit_widgets:
            conforme = mapa[w["status_var"].get()]
            obs = w["obs_entry"].get().strip()
            if obs == "Observação (opcional)":
                obs = ""
            resp = w["resp_entry"].get().strip()
            if resp == "Responsável (se NC)":
                resp = ""
            respostas.append(
                {
                    "item_id": w["item_id"],
                    "conforme": conforme,
                    "observacao": obs,
                    "severidade": w["sev_combo"].get(),
                    "responsavel": resp or "Não definido",
                }
            )

        resultado = logic.executar_auditoria(cid, auditor, respostas)
        n_nc = len(resultado["nc_criadas"])
        messagebox.showinfo(
            "Auditoria concluída",
            f"% de aderência: {resultado['percentual_aderencia']}%\n"
            f"Não conformidades abertas automaticamente: {n_nc}",
        )
        self.refresh_all()
        self.notebook.select(self.tab_dashboard)

    # ------------------------------------------------------------------
    # NÃO CONFORMIDADES
    # ------------------------------------------------------------------
    def _build_ncs_tab(self):
        frame = self.tab_ncs

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=20, pady=10)
        ttk.Label(top, text="Filtrar por status:").pack(side="left")
        self.combo_filtro_status = ttk.Combobox(
            top, state="readonly", width=20,
            values=["Todas", "Aberta", "Em Tratativa", "Em Verificação", "Encerrada"],
        )
        self.combo_filtro_status.set("Todas")
        self.combo_filtro_status.pack(side="left", padx=10)
        self.combo_filtro_status.bind("<<ComboboxSelected>>", lambda e: self._refresh_ncs())

        ttk.Button(top, text="Verificar prazos/escalonar agora", command=self._forcar_verificacao).pack(
            side="left", padx=20
        )

        cols = ("id", "descricao", "severidade", "responsavel", "status", "nivel", "prazo")
        self.tree_ncs = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        headers = {
            "id": ("ID", 40), "descricao": ("Descrição", 380), "severidade": ("Severidade", 90),
            "responsavel": ("Responsável", 150), "status": ("Status", 110),
            "nivel": ("Nível escalonamento", 130), "prazo": ("Prazo atual", 100),
        }
        for c, (label, w) in headers.items():
            self.tree_ncs.heading(c, text=label)
            self.tree_ncs.column(c, width=w, anchor="center" if c not in ("descricao",) else "w")
        self.tree_ncs.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree_ncs.bind("<Double-1>", lambda e: self._abrir_detalhe_nc())

        bottom = ttk.Frame(frame)
        bottom.pack(fill="x", padx=20, pady=(0, 15))
        ttk.Button(bottom, text="Ver histórico / avançar status", command=self._abrir_detalhe_nc).pack(side="left")
        ttk.Button(bottom, text="Excluir NC selecionada", command=self._excluir_nc_selecionada).pack(side="left", padx=10)

    def _refresh_ncs(self):
        logic.verificar_escalonamentos()
        filtro = self.combo_filtro_status.get() if hasattr(self, "combo_filtro_status") else "Todas"
        status = None if filtro in ("Todas", "") else filtro
        self.tree_ncs.delete(*self.tree_ncs.get_children())
        for nc in logic.listar_ncs(status):
            nivel_nome = database.NIVEIS_ESCALONAMENTO[nc["nivel_escalonamento"]]
            self.tree_ncs.insert(
                "", "end", iid=str(nc["id"]),
                values=(nc["id"], nc["descricao"][:90], nc["severidade"], nc["responsavel"],
                        nc["status"], nivel_nome, nc["prazo_atual"]),
            )

    def _forcar_verificacao(self):
        escalonadas = logic.verificar_escalonamentos()
        self._refresh_ncs()
        if escalonadas:
            messagebox.showinfo("Escalonamento", f"{len(escalonadas)} NC(s) escalonada(s) por prazo vencido.")
        else:
            messagebox.showinfo("Escalonamento", "Nenhuma NC com prazo vencido no momento.")

    def _abrir_detalhe_nc(self):
        sel = self.tree_ncs.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma não conformidade na lista.")
            return
        nc_id = int(sel[0])
        DetalheNCWindow(self, nc_id)

    # ------------------------------------------------------------------
    # COMUNICAÇÕES
    # ------------------------------------------------------------------
    def _build_comunicacoes_tab(self):
        frame = self.tab_comunicacoes
        cols = ("data", "nc", "destinatario", "canal", "assunto")
        self.tree_com = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        headers = {
            "data": ("Data/Hora", 150), "nc": ("NC", 60), "destinatario": ("Destinatário", 180),
            "canal": ("Canal", 130), "assunto": ("Assunto", 450),
        }
        for c, (label, w) in headers.items():
            self.tree_com.heading(c, text=label)
            self.tree_com.column(c, width=w)
        self.tree_com.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree_com.bind("<Double-1>", lambda e: self._ver_mensagem())

    def _refresh_comunicacoes(self):
        self._comunicacoes_cache = {c["id"]: c for c in logic.listar_comunicacoes()}
        self.tree_com.delete(*self.tree_com.get_children())
        for c in self._comunicacoes_cache.values():
            self.tree_com.insert(
                "", "end", iid=str(c["id"]),
                values=(c["data_envio"], c["nc_id"], c["destinatario"], c["canal"], c["assunto"]),
            )

    def _ver_mensagem(self):
        sel = self.tree_com.selection()
        if not sel:
            return
        c = self._comunicacoes_cache[int(sel[0])]
        messagebox.showinfo(c["assunto"], c["mensagem"])


class DetalheNCWindow(tk.Toplevel):
    def __init__(self, master, nc_id):
        super().__init__(master)
        self.master_app = master
        self.nc_id = nc_id
        self.title(f"Não Conformidade NC-{nc_id:04d}")
        self.geometry("620x520")
        self._build()

    def _build(self):
        nc = logic.obter_nc(self.nc_id)
        pad = {"padx": 15, "pady": 4}

        ttk.Label(self, text=nc["descricao"], wraplength=580, justify="left").pack(anchor="w", **pad)

        info = ttk.Frame(self)
        info.pack(anchor="w", **pad)
        ttk.Label(info, text=f"Severidade: {nc['severidade']}   |   Responsável: {nc['responsavel']}   |   "
                             f"Status atual: {nc['status']}   |   Prazo: {nc['prazo_atual']}").pack(anchor="w")

        ttk.Label(self, text="Histórico:").pack(anchor="w", **pad)
        hist_box = tk.Text(self, height=10, wrap="word")
        hist_box.pack(fill="x", padx=15)
        for h in logic.historico_da_nc(self.nc_id):
            hist_box.insert("end", f"[{h['data_evento']}] {h['evento']}\n    {h['detalhe']}\n\n")
        hist_box.config(state="disabled")

        ttk.Label(self, text="Avançar status:").pack(anchor="w", **pad)
        actions = ttk.Frame(self)
        actions.pack(anchor="w", **pad)

        fluxo = {
            "Aberta": "Em Tratativa",
            "Em Tratativa": "Em Verificação",
            "Em Verificação": "Encerrada",
        }
        proximo = fluxo.get(nc["status"])

        if proximo:
            ttk.Button(
                actions, text=f"Avançar para '{proximo}'",
                command=lambda: self._avancar(proximo),
            ).pack(side="left")
        else:
            ttk.Label(actions, text="NC encerrada — fluxo concluído.").pack(side="left")

    def _avancar(self, novo_status):
        usuario = simpledialog.askstring("Responsável pela ação", "Seu nome:", parent=self)
        if not usuario:
            return
        acao = None
        if novo_status == "Encerrada":
            acao = simpledialog.askstring(
                "Ação corretiva", "Descreva a ação corretiva aplicada e a verificação de eficácia:",
                parent=self,
            )
            if not acao:
                messagebox.showwarning("Atenção", "É necessário descrever a ação corretiva para encerrar.")
                return
        try:
            logic.atualizar_status_nc(self.nc_id, novo_status, acao_corretiva=acao, usuario=usuario)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return
        self.destroy()
        self.master_app.refresh_all()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()