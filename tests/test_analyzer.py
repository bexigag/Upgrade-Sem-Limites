import json
from unittest.mock import patch, MagicMock
from src.analyzer import analyze_transcript, build_prompt


def test_build_prompt_includes_transcript_and_metadata():
    prompt = build_prompt(
        transcript="The CEO said AI is transforming our business...",
        metadata={"title": "CEO Interview", "description": "John Smith talks AI"}
    )

    assert "The CEO said AI is transforming our business" in prompt
    assert "CEO Interview" in prompt
    assert "John Smith talks AI" in prompt


def test_analyze_transcript_returns_structured_data():
    mock_response = MagicMock()
    mock_response.text = json.dumps([
        {
            "nome": "John Smith",
            "cargo": "CEO",
            "empresa": "TechCorp",
            "usa_ia": "Sim - utiliza IA para automação de processos internos",
            "vai_usar_ia": "Sim - planeia expandir uso de IA generativa",
            "departamento_ai": "Não mencionado",
            "pessoas_departamento_ai": "",
            "visao_estrategica": "Transformação digital focada em cloud e IA, com expansão planeada para 2025",
            "tecnologias_mencionadas": ["ChatGPT", "AWS", "Kubernetes"],
            "principais_desafios": "Regulamentação e talento técnico",
            "outreach": "• Desafio com talento técnico\n• Interesse em IA generativa",
            "potencial_cliente": "7/10 (Quente) - Já usa IA e planeia expandir"
        }
    ])

    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        result = analyze_transcript(
            transcript="The CEO said AI is transforming...",
            metadata={"title": "CEO Interview", "description": "John Smith, CEO"},
            api_key="test-key",
        )

    assert result[0]["nome"] == "John Smith"
    assert result[0]["cargo"] == "CEO"
    assert result[0]["empresa"] == "TechCorp"
    assert "ChatGPT" in result[0]["tecnologias_mencionadas"]
    assert result[0]["usa_ia"].startswith("Sim")


def test_analyze_transcript_handles_invalid_json():
    mock_response = MagicMock()
    mock_response.text = "This is not JSON"

    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        result = analyze_transcript(
            transcript="text",
            metadata={"title": "t", "description": "d"},
            api_key="test-key",
        )

    assert result is None
