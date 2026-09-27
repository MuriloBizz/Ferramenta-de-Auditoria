"""
forcar_vencimento_teste.py
Script utilitário SÓ PARA TESTES.

Força o prazo das NCs em aberto (status 'Reportada' ou 'Escalonada') para
ontem, simulando que o prazo já venceu. Assim dá pra testar o botão
"Escalonar" / "Dívida Técnica" e as comunicações automáticas sem precisar
esperar os dias reais passarem.

Uso:
    python forcar_vencimento_teste.py         -> força TODAS as NCs abertas
    python forcar_vencimento_teste.py 3       -> força só a NC de id 3
"""

import sys
from datetime import date, timedelta

import database


def forcar_vencimento(nc_id=None):
    ontem = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    conn = database.get_connection()

    if nc_id:
        cur = conn.execute(
            """
            UPDATE nao_conformidades
            SET prazo_atual = ?
            WHERE id = ? AND status IN ('Reportada', 'Escalonada')
            """,
            (ontem, nc_id),
        )
    else:
        cur = conn.execute(
            """
            UPDATE nao_conformidades
            SET prazo_atual = ?
            WHERE status IN ('Reportada', 'Escalonada')
            """,
            (ontem,),
        )

    conn.commit()
    afetadas = cur.rowcount
    conn.close()

    if afetadas == 0:
        print("Nenhuma NC em aberto encontrada (status Reportada/Escalonada).")
    else:
        print(f"{afetadas} NC(s) tiveram o prazo forçado para {ontem} (vencido).")
        print("Agora, na aba 'Não Conformidades', clique em 'Verificar prazos "
              "vencidos' ou abra o detalhe da NC para ver os botões de "
              "Escalonar/Dívida Técnica liberados.")


if __name__ == "__main__":
    alvo = int(sys.argv[1]) if len(sys.argv) > 1 else None
    forcar_vencimento(alvo)
