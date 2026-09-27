"""
tab_config.py
Aba Configurações: cadastro do e-mail remetente e da senha de aplicativo
do Gmail, usados para enviar as comunicações das NCs.
"""

from tkinter import messagebox, ttk

import email_service


def build(app):
    frame = app.tab_config
    box = ttk.LabelFrame(frame, text="E-mail remetente (Gmail)")
    box.pack(fill="x", padx=20, pady=20)

    ttk.Label(box, text="E-mail:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
    app.entry_config_email = ttk.Entry(box, width=40)
    app.entry_config_email.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(box, text="Senha de aplicativo:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
    app.entry_config_senha = ttk.Entry(box, width=40, show="*")
    app.entry_config_senha.grid(row=1, column=1, padx=10, pady=10)

    ttk.Button(box, text="Salvar configuração", command=lambda: _salvar(app)).grid(
        row=2, column=0, columnspan=2, pady=10
    )

    ttk.Label(
        frame,
        text=(
            "Use uma senha de aplicativo do Gmail (não a senha normal da conta).\n"
            "Gere em: Conta Google > Segurança > Senhas de app."
        ),
        foreground="gray",
    ).pack(anchor="w", padx=20)


def _salvar(app):
    email = app.entry_config_email.get().strip()
    senha = app.entry_config_senha.get().strip()
    if not email or not senha:
        messagebox.showwarning("Atenção", "Preencha e-mail e senha de aplicativo.")
        return
    email_service.configurar_email(email, senha)
    app._atualizar_estado_aba_auditoria()
    messagebox.showinfo("E-mail configurado", "Configuração realizada com sucesso.")