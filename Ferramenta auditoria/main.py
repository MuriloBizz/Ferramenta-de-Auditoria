"""
main.py
Ponto de entrada da Ferramenta de Auditoria de Qualidade.

Uso:
    python main.py            -> abre a interface gráfica (usa o banco já existente,
                                   ou cria um vazio se não existir)
    python main.py --seed     -> recarrega os dados de exemplo (checklist da Forja/RA1)
                                   e depois abre a interface
"""

import sys
import database


def main():
    if "--seed" in sys.argv:
        from seed_data import seed
        seed()
    elif not __import__("os").path.exists(database.DB_PATH):
        database.init_db()

    from gui import main as run_gui
    run_gui()


if __name__ == "__main__":
    main()
