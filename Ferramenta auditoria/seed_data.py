"""
seed_data.py
Carrega um checklist de exemplo baseado na especificação oficial do RA1
(Especificação_do_Projeto_-_RA1_turmaA.pdf), para auditar o artefato
"Projeto de Design de Software" da equipe Forja.

prioridades refletem a pontuação de cada critério na rubrica da disciplina.
"""

from checklists import criar_checklist
from database import init_db


def seed():
    init_db(reset=True)

    itens = [
        {"categoria": "1. Especificação de Requisitos", "descricao": "Lista de RFs numerada e completa", "prioridade": 2, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "1. Especificação de Requisitos", "descricao": "Quantidade de RFs próxima de 20", "prioridade": 2, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "1. Especificação de Requisitos", "descricao": "RFs claros e sem ambiguidade", "prioridade": 2, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "1. Especificação de Requisitos", "descricao": "RFs alinhados ao domínio/regras de negócio", "prioridade": 2, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "1. Especificação de Requisitos", "descricao": "RFs consistentes (sem duplicidade/conflito)", "prioridade": 2, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},

        {"categoria": "2. Diagrama de Componentes", "descricao": "Diagrama tem entre 30 e 35 componentes", "prioridade": 3, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Agrupamento lógico de classes/componentes", "prioridade": 3, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Todos os componentes se comunicam via interface/dependência", "prioridade": 3, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Estereótipos UML usados quando necessário", "prioridade": 3, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Organização obrigatória em pacotes presente", "prioridade": 3, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "2. Diagrama de Componentes", "descricao": "Pacotes agrupam elementos correlatos coerentemente", "prioridade": 3, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},

        {"categoria": "3. Qualidade da Documentação", "descricao": "Documento consolidado em um único PDF", "prioridade": 1, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "3. Qualidade da Documentação", "descricao": "Contém as 5 seções obrigatórias, na ordem", "prioridade": 1, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "3. Qualidade da Documentação", "descricao": "Contextualização clara do projeto", "prioridade": 1, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "3. Qualidade da Documentação", "descricao": "Descrição técnica detalhada do diagrama presente", "prioridade": 1, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
        {"categoria": "3. Qualidade da Documentação", "descricao": "Reflexão sobre desafios enfrentados presente", "prioridade": 1, "responsavel": "teste", "email_responsavel": "responsavelNC@gmail.com"},
    ]

    checklist_id = criar_checklist(
        nome="Auditoria RA1 - Especificação de Design de Software",
        processo="Projeto de Design de Software - Equipe Forja",
        responsavel="responsável pelo checklist",
        email_responsavel="responsavelCL@gmail.com",
        itens=itens,
    )
    print(f"Checklist criado com id={checklist_id} e {len(itens)} itens.")
    return checklist_id


if __name__ == "__main__":
    seed()
