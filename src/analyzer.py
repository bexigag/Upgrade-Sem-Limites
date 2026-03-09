import json
from google import genai
from google.genai import types


SYSTEM_PROMPT = """És um analista de inteligência estratégica. Analisa transcrições de entrevistas e identifica TODAS as pessoas com substância (nome, cargo, empresa, opiniões relevantes).

A nossa empresa implementa soluções de AI, ensina a usar AI e otimiza processos com AI. O objetivo é identificar oportunidades de negócio nestas entrevistas.

REGRAS IMPORTANTES:
- Exclui apresentadores/entrevistadores que apenas fazem perguntas.
- Identifica TODAS as pessoas entrevistadas que partilham opiniões, estratégias ou informação relevante.
- Retorna SEMPRE um array JSON, mesmo que haja apenas 1 pessoa.
- Máximo de 5 pessoas por entrevista.

Responde APENAS com um array JSON válido, sem texto adicional. Cada elemento do array deve ter exatamente estes campos:

[
  {
    "nome": "Nome completo da pessoa",
    "cargo": "Cargo e empresa",
    "usa_ia": "Sim/Não - informação extra sobre isto",
    "vai_usar_ia": "Sim/Não - informação extra sobre isto",
    "inovacao": "Inovações em curso",
    "estrategia_digital": "Insights sobre estratégia digital",
    "tecnologias_mencionadas": ["lista", "de", "tecnologias", "os elementos nao podem ter virgulas"],
    "principais_desafios": "Desafios principais",
    "resumo_estrategico": "Resumo conciso (2-3 frases)",
    "potencial_cliente": "N/10 (Quente/Morno/Frio) - justificação breve do potencial desta empresa como cliente para os nossos serviços de AI"
  }
]

Cada pessoa deve ter TODOS os campos preenchidos de forma independente.

Para o potencial_cliente, avalia considerando: se já usa AI (pode querer mais), se quer usar AI (oportunidade direta), se tem desafios que AI resolve, se mencionou orçamento ou parcerias tecnológicas.

Se algum campo não puder ser determinado, usa "Não mencionado".
Responde em Português."""


def build_prompt(transcript: str, metadata: dict) -> str:
    return f"""Analisa a seguinte entrevista de CEO.

Título do vídeo: {metadata.get('title', 'Desconhecido')}
Descrição: {metadata.get('description', 'Sem descrição')}

Transcrição:
{transcript}"""


def analyze_transcript(transcript: str, metadata: dict, api_key: str) -> list[dict] | None:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=build_prompt(transcript, metadata),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=8192,
        ),
    )

    try:
        response_text = response.text.strip()
        # Remove markdown code block wrapping (```json ... ```)
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            response_text = "\n".join(lines)
        parsed = json.loads(response_text)

        # Backward compatibility: wrap single dict in a list
        if isinstance(parsed, dict):
            parsed = [parsed]

        if not isinstance(parsed, list):
            return None

        # Cap at 5 persons maximum
        return parsed[:5]
    except (json.JSONDecodeError, IndexError, AttributeError):
        return None
