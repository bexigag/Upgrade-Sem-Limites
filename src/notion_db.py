from notion_client import Client


SCHEMA = {
    "Nome": {"title": {}},
    "Cargo": {"rich_text": {}},
    "Link da Entrevista": {"url": {}},
    "Usa IA": {"rich_text": {}},
    "Vai Usar IA": {"rich_text": {}},
    "Inovação": {"rich_text": {}},
    "Estratégia Digital": {"rich_text": {}},
    "Tecnologias Mencionadas": {"multi_select": {"options": []}},
    "Principais Desafios": {"rich_text": {}},
    "Resumo Estratégico": {"rich_text": {}},
    "Apontamentos": {"rich_text": {}},
    "Status": {
        "select": {
            "options": [
                {"name": "A Processar", "color": "yellow"},
                {"name": "Concluído", "color": "green"},
                {"name": "Erro", "color": "red"},
            ]
        }
    },
}


def create_database(token: str, parent_page_id: str) -> str:
    notion = Client(auth=token)

    database = notion.databases.create(
        parent={"page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "CEO Video Transcriber"}}],
        properties=SCHEMA,
    )

    return database["id"]
