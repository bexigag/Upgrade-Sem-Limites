from unittest.mock import patch, MagicMock, call
from src.notion_db import create_database, add_row, SCHEMA


def test_create_database_returns_id():
    mock_notion = MagicMock()
    mock_notion.databases.create.return_value = {"id": "db-123"}

    with patch("src.notion_db.Client", return_value=mock_notion):
        db_id = create_database(
            token="test-token",
            parent_page_id="page-456",
        )

    assert db_id == "db-123"
    mock_notion.databases.create.assert_called_once()


def test_create_database_has_correct_schema():
    mock_notion = MagicMock()
    mock_notion.databases.create.return_value = {"id": "db-123"}

    with patch("src.notion_db.Client", return_value=mock_notion):
        create_database(token="test-token", parent_page_id="page-456")

    call_kwargs = mock_notion.databases.create.call_args[1]
    properties = call_kwargs["properties"]

    assert "Nome" in properties
    assert "Cargo" in properties
    assert "Link da Entrevista" in properties
    assert "Usa IA" in properties
    assert "Vai Usar IA" in properties
    assert "Visão Estratégica" in properties  # NEW (replaces Inovação, Estratégia Digital, Resumo Estratégico)
    assert "Tecnologias Mencionadas" in properties
    assert "Principais Desafios" in properties
    assert "Tem Departamento AI" in properties  # NEW
    assert "Pessoas Departamento AI" in properties  # NEW
    assert "Outreach" in properties  # NEW
    assert "Nome da Empresa" in properties  # NEW
    assert "Apontamentos" in properties
    assert "Status" in properties


def test_add_row_creates_page():
    mock_notion = MagicMock()
    mock_notion.pages.create.return_value = {"id": "page-789"}

    analysis = {
        "nome": "John Smith",
        "cargo": "CEO",  # Separated from empresa
        "empresa": "TechCorp",  # NEW field
        "usa_ia": "Sim - usa ChatGPT",
        "vai_usar_ia": "Sim - planeia expandir",
        "departamento_ai": "Sim - equipe de 3 pessoas",
        "pessoas_departamento_ai": "Carlos Silva (DataAI)",
        "visao_estrategica": "Cloud-first com foco em IA, expansão planeada para 2025",  # Combined field
        "tecnologias_mencionadas": ["ChatGPT", "AWS"],
        "principais_desafios": "Regulamentação",
        "outreach": "• Desafio com regulamentação\n• Interesse em expansão",  # NEW
    }

    with patch("src.notion_db.Client", return_value=mock_notion):
        page_id = add_row(
            token="test-token",
            database_id="db-123",
            video_url="https://youtube.com/watch?v=abc",
            analysis=analysis,
        )

    assert page_id == "page-789"
    mock_notion.pages.create.assert_called_once()

    call_kwargs = mock_notion.pages.create.call_args[1]
    props = call_kwargs["properties"]
    assert props["Nome"]["title"][0]["text"]["content"] == "John Smith"
    assert props["Status"]["select"]["name"] == "Concluído"
    assert props["Nome da Empresa"]["rich_text"][0]["text"]["content"] == "TechCorp"
    assert props["Visão Estratégica"]["rich_text"][0]["text"]["content"].startswith("Cloud-first")
    assert props["Tem Departamento AI"]["rich_text"][0]["text"]["content"].startswith("Sim")
    assert props["Pessoas Departamento AI"]["rich_text"][0]["text"]["content"] == "Carlos Silva (DataAI)"
    assert "•" in props["Outreach"]["rich_text"][0]["text"]["content"]


def test_add_row_with_error_status():
    mock_notion = MagicMock()
    mock_notion.pages.create.return_value = {"id": "page-err"}

    with patch("src.notion_db.Client", return_value=mock_notion):
        page_id = add_row(
            token="test-token",
            database_id="db-123",
            video_url="https://youtube.com/watch?v=abc",
            analysis=None,
            status="Erro",
        )

    call_kwargs = mock_notion.pages.create.call_args[1]
    assert call_kwargs["properties"]["Status"]["select"]["name"] == "Erro"
