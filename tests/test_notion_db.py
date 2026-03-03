from unittest.mock import patch, MagicMock, call
from src.notion_db import create_database, SCHEMA


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
    assert "Inovação" in properties
    assert "Estratégia Digital" in properties
    assert "Tecnologias Mencionadas" in properties
    assert "Principais Desafios" in properties
    assert "Resumo Estratégico" in properties
    assert "Apontamentos" in properties
    assert "Status" in properties
