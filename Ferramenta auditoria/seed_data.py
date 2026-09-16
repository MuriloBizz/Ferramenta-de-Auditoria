"""
seed_data.py
Carrega um checklist de exemplo baseado na especificação oficial do RA1
(Especificação_do_Projeto_-_RA1_turmaA.pdf), para auditar o artefato
"Projeto de Design de Software" da equipe Forja.

Pesos refletem a pontuação de cada critério na rubrica da disciplina.
"""

from database import init_db
from logic import criar_checklist


def seed():
    init_db(reset=True)

    itens = [
        # Critério 1 - Especificação de Requisitos (2,0 pts)
        {"categoria": "1. Especificação de Requisitos", "descricao": "Lista de RFs numerada e completa", "peso": 2.0},
        {"categoria": "1. Especificação de Requisitos", "descricao": "Quantidade de RFs próxima de 20", "peso": 2.0},
        {"categoria": "1. Especificação de Requisitos", "descricao": "RFs claros e sem ambiguidade", "peso": 2.0},
        {"categoria": "1. Especificação de Requisitos", "descricao": "RFs alinhados ao domínio/regras de negócio", "peso": 2.0},
        {"categoria": "1. Especificação de Requisitos", "descricao": "RFs consistentes (sem duplicidade/conflito)", "peso": 2.0},

        # Critério 2 - Diagrama de Componentes (4,0 pts)
        {"categoria": "2. Diagrama de Componentes", "descricao": "Diagrama tem entre 30 e 35 componentes", "peso": 4.0},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Agrupamento lógico de classes/componentes", "peso": 4.0},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Todos os componentes se comunicam via interface/dependência", "peso": 4.0},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Estereótipos UML usados quando necessário", "peso": 4.0},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Organização obrigatória em pacotes presente", "peso": 4.0},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Pacotes agrupam elementos correlatos coerentemente", "peso": 4.0},

        # Critério 3 - Qualidade da Documentação (1,0 pt)
        {"categoria": "3. Qualidade da Documentação", "descricao": "Documento consolidado em um único PDF", "peso": 1.0},
        {"categoria": "3. Qualidade da Documentação", "descricao": "Contém as 5 seções obrigatórias, na ordem", "peso": 1.0},
        {"categoria": "3. Qualidade da Documentação", "descricao": "Contextualização clara do projeto", "peso": 1.0},
        {"categoria": "3. Qualidade da Documentação", "descricao": "Descrição técnica detalhada do diagrama presente", "peso": 1.0},
        {"categoria": "3. Qualidade da Documentação", "descricao": "Reflexão sobre desafios enfrentados presente", "peso": 1.0},
    ]

    checklist_id = criar_checklist(
        nome="Auditoria RA1 - Especificação de Design de Software",
        processo="Projeto de Design de Software - Equipe Forja",
        itens=itens,
    )
    print(f"Checklist criado com id={checklist_id} e {len(itens)} itens.")
    return checklist_id


if __name__ == "__main__":
    seed()
