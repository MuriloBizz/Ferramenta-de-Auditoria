"""
gui.py
Janela principal da interface (Tkinter): monta o Notebook com as abas
Dashboard, Checklists, Nova Auditoria, Não Conformidades, Comunicações e
Configurações. Cada aba é implementada em seu próprio arquivo tab_*.py.
"""

import os
from tkinter import Tk
from tkinter import ttk

import database
import email_service
import tab_auditoria
import tab_checklists
import tab_comunicacoes
import tab_config
import tab_dashboard
import tab_ncs


class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("Ferramenta de Auditoria de Qualidade")
        self.geometry("1150x680")
        self.minsize(950, 600)

        if not os.path.exists(database.DB_PATH):
            database.init_db()

        self._build_layout()
        self.refresh_all()

    def _build_layout(self):
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Auditoria de Qualidade", padding=14).pack(side="left")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_checklists = ttk.Frame(self.notebook)
        self.tab_auditoria = ttk.Frame(self.notebook)
        self.tab_ncs = ttk.Frame(self.notebook)
        self.tab_comunicacoes = ttk.Frame(self.notebook)
        self.tab_config = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_checklists, text="Checklists")
        self.notebook.add(self.tab_auditoria, text="Nova Auditoria")
        self.notebook.add(self.tab_ncs, text="Não Conformidades")
        self.notebook.add(self.tab_comunicacoes, text="Comunicações")
        self.notebook.add(self.tab_config, text="Configurações")
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())

        tab_dashboard.build(self)
        tab_checklists.build(self)
        tab_auditoria.build(self)
        tab_ncs.build(self)
        tab_comunicacoes.build(self)
        tab_config.build(self)
        self._atualizar_estado_aba_auditoria()

    def refresh_all(self):
        tab_dashboard.refresh(self)
        tab_checklists.refresh(self)
        tab_auditoria.refresh_checklists(self)
        tab_ncs.refresh(self)
        tab_comunicacoes.refresh(self)
        
    def _atualizar_estado_aba_auditoria(self):
        if email_service.configurado():
            self.notebook.tab(self.tab_auditoria, state="normal")
        else:
            if self.notebook.select() == str(self.tab_auditoria):
                self.notebook.select(self.tab_config)
            self.notebook.tab(self.tab_auditoria, state="disabled")


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
