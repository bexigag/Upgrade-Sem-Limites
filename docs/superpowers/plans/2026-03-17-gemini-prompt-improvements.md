# Gemini Prompt Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Gemini prompt quality to extract better strategic information from CEO interviews, focusing on potential AI customers

**Architecture:** Update Gemini SYSTEM_PROMPT with new field structure, add Python validation for person quality, update Notion mapping to new schema. No data migration - only new videos use new structure.

**Tech Stack:** Python, Google Gemini API, Notion API, pytest

---

## File Structure

- **Modify:** `src/analyzer.py` - Update SYSTEM_PROMPT, add `_is_person_valid()` validation function
- **Modify:** `src/notion_db.py` - Update SCHEMA dict, update `add_row()` field mapping
- **Modify:** `tests/test_analyzer.py` - Update existing test for list return type, add 8 new test cases
- **Modify:** `tests/test_notion_db.py` - Update tests for new schema

---

## Task Group 1: Update Tests First (Prevent Breaking Changes)

### Task 1: Update test_notion_db.py for new schema

**Files:**
- Modify: `tests/test_notion_db.py:34-40` and `tests/test_notion_db.py:47-57`

- [ ] **Step 1: Update test_create_database_has_correct_schema()**

Replace lines 34-40 with new field assertions:

```python
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
```

- [ ] **Step 2: Update test_add_row_creates_page() analysis data**

Replace lines 47-57 with new field structure:

```python
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
```

- [ ] **Step 3: Add assertions for new fields**

After line 73, add:

```python
    assert props["Nome da Empresa"]["rich_text"][0]["text"]["content"] == "TechCorp"
    assert props["Visão Estratégica"]["rich_text"][0]["text"]["content"].startswith("Cloud-first")
    assert props["Tem Departamento AI"]["rich_text"][0]["text"]["content"].startswith("Sim")
    assert props["Pessoas Departamento AI"]["rich_text"][0]["text"]["content"] == "Carlos Silva (DataAI)"
    assert "•" in props["Outreach"]["rich_text"][0]["text"]["content"]
```

- [ ] **Step 4: Run test to verify it fails (expected - code not updated yet)**

Run: `pytest tests/test_notion_db.py -v`
Expected: FAIL (tests expect new fields that don't exist yet)

- [ ] **Step 5: Commit test updates**

```bash
git add tests/test_notion_db.py
git commit -m "test: update test_notion_db.py for new schema

- Update test_create_database_has_correct_schema to check new fields
- Update test_add_row_creates_page with new field structure
- Add assertions for Nome da Empresa, Visão Estratégica, Tem Departamento AI, etc.
- Tests will fail until code is updated (TDD approach)"
```

---

### Task 2: Update test_analyzer.py for list return type

**Files:**
- Modify: `tests/test_analyzer.py:19-45`

- [ ] **Step 1: Update mock to return array**

Change line 19 to return an array (wrap in `[...]`):

```python
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
```

- [ ] **Step 2: Update assertions to access list**

Replace lines 42-45 with:

```python
    assert result[0]["nome"] == "John Smith"
    assert result[0]["cargo"] == "CEO"
    assert result[0]["empresa"] == "TechCorp"
    assert "ChatGPT" in result[0]["tecnologias_mencionadas"]
    assert result[0]["usa_ia"].startswith("Sim")
```

- [ ] **Step 3: Run test to verify it fails (expected)**

Run: `pytest tests/test_analyzer.py::test_analyze_transcript_returns_structured_data -v`
Expected: FAIL (mock has new fields that code doesn't handle yet)

- [ ] **Step 4: Commit test update**

```bash
git add tests/test_analyzer.py
git commit -m "test: update test for list return type and new fields

- Mock now returns array (matches new prompt)
- Update assertions to access result[0] instead of result
- Add all new fields from updated schema"
```

---

## Task Group 2: Update Code (Tests Now Guide Implementation)

### Task 3: Update SYSTEM_PROMPT in analyzer.py

**Files:**
- Modify: `src/analyzer.py:6-38`

- [ ] **Step 1: Replace SYSTEM_PROMPT**

Replace lines 6-38 with:

```python
SYSTEM_PROMPT = """És um analista de inteligência estratégica. Analisa transcrições de entrevistas e identifica pessoas com substância suficiente para preencher os campos abaixo.

A nossa empresa implementa soluções de AI, ensina a usar AI e otimiza processos com AI. O objetivo é identificar oportunidades de negócio nestas entrevistas.

REGRAS IMPORTANTES:
- Exclui apresentadores/entrevistadores que apenas fazem perguntas sem partilhar opiniões.
- Identifica pessoas com nome MENCIONADO, cargo numa empresa e informação suficiente.
- Se NOME for "Não mencionado" ou vazio, EXCLUIR a pessoa.
- Se CARGO ou EMPRESA tiverem <= 2 caracteres, EXCLUIR a pessoa.
- Se mais de 3 campos obrigatórios estiverem "Não mencionado", EXCLUIR a pessoa.
- Máximo de 5 pessoas por entrevista.

Separação CARGO/EMPRESA:
- "cargo": Apenas o título/função (ex: "CEO", "CTO", "Diretor de Inovação")
- "empresa": Apenas o nome da empresa (ex: "Microsoft", "NOS", "Farfetch")

TECNOLOGIAS MENCIONADAS:
- Apenas AI/ML + tecnologias de inovação + termos de negócio relevantes
- EXCLUIR: emails, telemóveis, URLs, informações de contacto, tecnologias genéricas (email, telefone, website)
- INCLUIR: machine learning, computer vision, LLMs, cloud, data analytics, automação, transformação digital, IA generativa

OUTREACH:
- Formato: 3-5 bullet points, cada um começando com "•"
- Extrair pontos de gancho para email comercial baseados em: desafios que AI pode resolver, oportunidades de AI, menção de orçamento/parcerias, urgência de projetos, interesse em inovação

Responde APENAS com um array JSON válido, sem texto adicional. Cada elemento do array deve ter exatamente estes campos:

[
  {
    "nome": "Nome completo da pessoa",
    "cargo": "Cargo/apenas título (sem empresa)",
    "empresa": "Nome da empresa (apenas)",
    "usa_ia": "Sim/Não - informação extra sobre isto",
    "vai_usar_ia": "Sim/Não - informação extra sobre isto",
    "departamento_ai": "Sim/Não - (externo se aplicável) + o que faz resumido",
    "pessoas_departamento_ai": "Nomes e empresa exterior se aplicável, ou vazio",
    "visao_estrategica": "Estratégia e inovação de curto e longo prazo agregadas",
    "tecnologias_mencionadas": ["lista", "de", "tecnologias", "AI", "cloud", "automação"],
    "principais_desafios": "Desafios principais",
    "outreach": "• Ponto 1\n• Ponto 2\n• Ponto 3 (máximo 5 bullets)",
    "potencial_cliente": "N/10 (Quente/Morno/Frio) - justificação breve do potencial como cliente para AI"
  }
]

Cada pessoa deve ter TODOS os campos preenchidos de forma independente.
Para o potencial_cliente, avalia considerando: se já usa AI (pode querer mais), se quer usar AI (oportunidade direta), se tem desafios que AI resolve, se mencionou orçamento ou parcerias tecnológicas.

Se algum campo não puder ser determinado, usa "Não mencionado".
Responde em Português."""
```

- [ ] **Step 2: Commit**

```bash
git add src/analyzer.py
git commit -m "feat: update Gemini SYSTEM_PROMPT with new field structure"
```

---

### Task 4: Add validation function to analyzer.py

**Files:**
- Modify: `src/analyzer.py` (add after `build_prompt()` function, around line 49)

- [ ] **Step 1: Add `_is_person_valid()` function**

After line 49, add:

```python
def _is_person_valid(person: dict) -> bool:
    """Validate that a person entry meets minimum quality standards."""
    # Nome não pode ser "Não mencionado" ou vazio
    nome = person.get("nome", "").strip()
    nome_lower = nome.lower()
    if nome_lower in ["não mencionado", "nao mencionado", ""] or len(nome) < 2:
        return False

    # Cargo e Empresa devem ter mais de 2 caracteres
    if len(person.get("cargo", "").strip()) <= 2:
        return False
    if len(person.get("empresa", "").strip()) <= 2:
        return False

    # Campos obrigatórios a verificar (excluindo tecnologias e pessoas_departamento_ai que são opcionais)
    required_fields = ["nome", "cargo", "empresa", "usa_ia", "vai_usar_ia", "visao_estrategica", "principais_desafios"]
    nao_mentionados = 0
    for k in required_fields:
        v = person.get(k, "")
        if isinstance(v, str) and v.strip().lower() in ["não mencionado", "nao mencionado", ""]:
            nao_mentionados += 1

    # Máximo 3 campos obrigatórios vazios
    return nao_mentionados <= 3
```

- [ ] **Step 2: Update `analyze_transcript()` to use validation**

Find `analyze_transcript()` function (around line 51). After JSON parsing, add validation filter.

Replace section after `parsed = json.loads(response_text)` (around line 71-81) with:

```python
        # Backward compatibility: wrap single dict in a list
        if isinstance(parsed, dict):
            parsed = [parsed]

        if not isinstance(parsed, list):
            return None

        # Filter out invalid persons (quality control)
        valid_persons = [p for p in parsed if _is_person_valid(p)]

        # Cap at 5 persons maximum
        return valid_persons[:5]
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `pytest tests/test_analyzer.py tests/test_notion_db.py -v`
Expected: test_analyzer tests PASS, test_notion_db tests FAIL (notion_db code not updated yet)

- [ ] **Step 4: Commit**

```bash
git add src/analyzer.py
git commit -m "feat: add person validation and filter logic

- Add _is_person_valid() with quality checks
- Filter persons through validation in analyze_transcript()
- Cap at 5 valid persons per video"
```

---

### Task 5: Update SCHEMA in notion_db.py

**Files:**
- Modify: `src/notion_db.py:4-27`

- [ ] **Step 1: Replace SCHEMA**

Replace lines 4-27 with:

```python
SCHEMA = {
    "Nome": {"title": {}},
    "Cargo": {"rich_text": {}},
    "Link da Entrevista": {"url": {}},
    "Data": {"date": {}},
    "Potencial Cliente": {"rich_text": {}},
    "Usa IA": {"rich_text": {}},
    "Vai Usar IA": {"rich_text": {}},
    "Visão Estratégica": {"rich_text": {}},
    "Tecnologias Mencionadas": {"multi_select": {"options": []}},
    "Principais Desafios": {"rich_text": {}},
    "Tem Departamento AI": {"rich_text": {}},
    "Pessoas Departamento AI": {"rich_text": {}},
    "Outreach": {"rich_text": {}},
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
    "Nome da Empresa": {"rich_text": {}},
}
```

- [ ] **Step 2: Commit**

```bash
git add src/notion_db.py
git commit -m "feat: update Notion SCHEMA for new field structure"
```

---

### Task 6: Update add_row() mapping in notion_db.py

**Files:**
- Modify: `src/notion_db.py:92-110`

- [ ] **Step 1: Replace field mapping in add_row()**

Find the `if analysis:` block (around line 92). Replace property assignments with:

```python
    if analysis:
        properties["Nome"] = {
            "title": [{"type": "text", "text": {"content": analysis.get("nome", "Desconhecido")}}]
        }
        properties["Cargo"] = _rich_text(analysis.get("cargo", ""))
        properties["Nome da Empresa"] = _rich_text(analysis.get("empresa") or "Não mencionado")
        properties["Usa IA"] = _rich_text(analysis.get("usa_ia", ""))
        properties["Vai Usar IA"] = _rich_text(analysis.get("vai_usar_ia", ""))
        properties["Visão Estratégica"] = _rich_text(analysis.get("visao_estrategica") or "Não mencionado")
        properties["Principais Desafios"] = _rich_text(analysis.get("principais_desafios", ""))
        properties["Potencial Cliente"] = _rich_text(analysis.get("potencial_cliente", ""))
        properties["Tem Departamento AI"] = _rich_text(analysis.get("departamento_ai") or "Não mencionado")
        properties["Pessoas Departamento AI"] = _rich_text(analysis.get("pessoas_departamento_ai") or "")
        properties["Outreach"] = _rich_text(analysis.get("outreach") or "")

        techs = analysis.get("tecnologias_mencionadas", [])
        if isinstance(techs, list):
            properties["Tecnologias Mencionadas"] = {
                "multi_select": [{"name": t.replace(",", " e")[:100]} for t in techs if isinstance(t, str)]
            }
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/notion_db.py
git commit -m "feat: update add_row() mapping for new fields

- Map new fields: Nome da Empresa, Visão Estratégica, Tem Departamento AI, etc.
- Remove old fields: estrategia_digital, inovacao, resumo_estrategico
- Use appropriate defaults for required vs optional fields"
```

---

## Task Group 3: Add New Test Cases

### Task 7: Add remaining test cases to test_analyzer.py

**Files:**
- Modify: `tests/test_analyzer.py` (add at end)

- [ ] **Step 1: Add all new test cases**

Add at end of file:

```python
def test_excludes_person_without_name():
    """Person with 'Não mencionado' or empty name should be excluded."""
    mock_response = MagicMock()
    mock_response.text = json.dumps([{
        "nome": "Não mencionado",
        "cargo": "CEO",
        "empresa": "TechCorp",
        "usa_ia": "Sim", "vai_usar_ia": "Não",
        "departamento_ai": "Não", "pessoas_departamento_ai": "",
        "visao_estrategica": "Visão", "tecnologias_mencionadas": ["AI"],
        "principais_desafios": "Desafios", "outreach": "• Ponto", "potencial_cliente": "5/10"
    }])
    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        result = analyze_transcript(transcript="text", metadata={"title": "t"}, api_key="test-key")
    assert len(result) == 0


def test_excludes_person_with_too_many_empty_fields():
    """Person with >3 required fields as 'Não mencionado' should be excluded."""
    mock_response = MagicMock()
    mock_response.text = json.dumps([{
        "nome": "John Doe", "cargo": "CTO", "empresa": "Acme",
        "usa_ia": "Não mencionado", "vai_usar_ia": "Não mencionado",
        "departamento_ai": "Não mencionado", "pessoas_departamento_ai": "",
        "visao_estrategica": "Não mencionado", "tecnologias_mencionadas": [],
        "principais_desafios": "Não mencionado", "outreach": "", "potencial_cliente": "3/10"
    }])
    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        result = analyze_transcript(transcript="text", metadata={"title": "t"}, api_key="test-key")
    assert len(result) == 0


def test_excludes_person_with_short_cargo_empresa():
    """Person with cargo or empresa <= 2 chars should be excluded."""
    mock_response = MagicMock()
    mock_response.text = json.dumps([{
        "nome": "Jane Doe", "cargo": "CO", "empresa": "XY",
        "usa_ia": "Sim", "vai_usar_ia": "Sim",
        "departamento_ai": "Não", "pessoas_departamento_ai": "",
        "visao_estrategica": "Visão", "tecnologias_mencionadas": ["AI"],
        "principais_desafios": "Desafios", "outreach": "• Ponto", "potencial_cliente": "6/10"
    }])
    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        result = analyze_transcript(transcript="text", metadata={"title": "t"}, api_key="test-key")
    assert len(result) == 0


def test_includes_valid_person():
    """Person with all valid fields should be included."""
    mock_response = MagicMock()
    mock_response.text = json.dumps([{
        "nome": "Alice Johnson", "cargo": "CPO", "empresa": "InnovateTech",
        "usa_ia": "Sim", "vai_usar_ia": "Não mencionado",
        "departamento_ai": "Sim - 5 pessoas", "pessoas_departamento_ai": "Carlos Silva (DataTeam AI)",
        "visao_estrategica": "Focus em inovação", "tecnologias_mencionadas": ["Python", "TensorFlow"],
        "principais_desafios": "Escala", "outreach": "• Desafio\n• Oportunidade", "potencial_cliente": "8/10"
    }])
    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        result = analyze_transcript(transcript="text", metadata={"title": "t"}, api_key="test-key")
    assert len(result) > 0
    assert result[0]["cargo"] == "CPO"
    assert result[0]["empresa"] == "InnovateTech"


def test_max_5_persons_returned():
    """Should return maximum 5 persons even if Gemini returns more."""
    persons = [{
        "nome": f"Person {i}", "cargo": "CEO", "empresa": f"Company {i}",
        "usa_ia": "Sim", "vai_usar_ia": "Não", "departamento_ai": "Não",
        "pessoas_departamento_ai": "", "visao_estrategica": "Strategy",
        "tecnologias_mencionadas": ["AI"], "principais_desafios": "Challenges",
        "outreach": "• Point", "potencial_cliente": "5/10"
    } for i in range(7)]
    mock_response = MagicMock()
    mock_response.text = json.dumps(persons)
    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        result = analyze_transcript(transcript="text", metadata={"title": "t"}, api_key="test-key")
    assert len(result) == 5


def test_outreach_format():
    """Outreach field should contain 3-5 bullet points starting with •"""
    mock_response = MagicMock()
    mock_response.text = json.dumps([{
        "nome": "Bob Smith", "cargo": "CEO", "empresa": "TechCorp",
        "usa_ia": "Sim", "vai_usar_ia": "Sim", "departamento_ai": "Não",
        "pessoas_departamento_ai": "", "visao_estrategica": "Strategy",
        "tecnologias_mencionadas": ["AI"], "principais_desafios": "Challenges",
        "outreach": "• Challenge with data\n• Interest in AI\n• Planning expansion",
        "potencial_cliente": "7/10"
    }])
    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        result = analyze_transcript(transcript="text", metadata={"title": "t"}, api_key="test-key")
    assert len(result) > 0
    outreach = result[0]["outreach"]
    lines = outreach.split('\n')
    assert len(lines) >= 3
    assert all('•' in line for line in lines)


def test_cargo_empresa_separated():
    """Cargo and empresa should be separate fields in the result."""
    mock_response = MagicMock()
    mock_response.text = json.dumps([{
        "nome": "Carol White", "cargo": "VP of Engineering", "empresa": "StartupXYZ",
        "usa_ia": "Não mencionado", "vai_usar_ia": "Não mencionado",
        "departamento_ai": "Não", "pessoas_departamento_ai": "",
        "visao_estrategica": "Strategy", "tecnologias_mencionadas": ["Cloud"],
        "principais_desafios": "Hiring", "outreach": "• Point", "potencial_cliente": "4/10"
    }])
    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        result = analyze_transcript(transcript="text", metadata={"title": "t"}, api_key="test-key")
    assert len(result) > 0
    assert result[0]["cargo"] == "VP of Engineering"
    assert result[0]["empresa"] == "StartupXYZ"
    assert "StartupXYZ" not in result[0]["cargo"]


def test_analyze_transcript_handles_single_dict_response():
    """Backward compatibility: single dict response should be wrapped in list."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({  # Single dict, not array
        "nome": "Single Person", "cargo": "CEO", "empresa": "SoloCorp",
        "usa_ia": "Sim", "vai_usar_ia": "Não", "departamento_ai": "Não",
        "pessoas_departamento_ai": "", "visao_estrategica": "Strategy",
        "tecnologias_mencionadas": ["AI"], "principais_desafios": "Challenges",
        "outreach": "• Point", "potencial_cliente": "5/10"
    })
    with patch("src.analyzer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        result = analyze_transcript(transcript="text", metadata={"title": "t"}, api_key="test-key")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["nome"] == "Single Person"
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/test_analyzer.py -v`
Expected: All 13 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_analyzer.py
git commit -m "test: add 8 new test cases for validation and new fields

- Test exclusion of persons without name
- Test exclusion of persons with too many empty fields
- Test exclusion of persons with short cargo/empresa
- Test inclusion of valid persons
- Test max 5 persons cap
- Test outreach bullet format
- Test cargo/empresa separation
- Test backward compatibility for single dict response"
```

---

## Task Group 4: Final Verification & Documentation

### Task 8: Final test verification

**Files:**
- Test: All tests

- [ ] **Step 1: Run all project tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run with coverage (optional)**

Run: `pytest tests/ --cov=src --cov-report=term-missing`
Expected: High coverage on modified files

- [ ] **Step 3: Commit if any fixes needed**

```bash
git add tests/ src/
git commit -m "fix: resolve test failures found in final verification"
```

---

### Task 9: Manual integration test

**Files:**
- Manual test via Streamlit

- [ ] **Step 1: Create Notion columns manually**

Before running the app, create these columns in your existing Notion database:
- Nome da Empresa (rich_text)
- Tem Departamento AI (rich_text)
- Pessoas Departamento AI (rich_text)
- Visão Estratégica (rich_text)
- Outreach (rich_text)

- [ ] **Step 2: Run Streamlit app**

Run: `streamlit run streamlit_app.py`
Process a known video with a clear CEO interview.

- [ ] **Step 3: Verify results in Notion**

Check that:
- New row has cargo separated from empresa
- Visão Estratégica combines the old 3 fields
- Outreach has bullet points
- Persons with low quality are excluded
- Maximum 5 persons per video

- [ ] **Step 4: Document any issues found**

If issues found, create bug fix tasks.

---

### Task 10: Update README with Notion setup instructions

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Notion setup section**

Add after environment variables section:

```markdown
## Notion Database Setup

Before running the app, ensure your Notion database has these columns:

### Required Columns (create manually if using existing database):

1. **Nome** (title)
2. **Cargo** (rich_text)
3. **Nome da Empresa** (rich_text) - NEW
4. **Usa IA** (rich_text)
5. **Vai Usar IA** (rich_text)
6. **Tem Departamento AI** (rich_text) - NEW
7. **Pessoas Departamento AI** (rich_text) - NEW
8. **Visão Estratégica** (rich_text) - NEW (replaces Estratégia Digital, Inovação, Resumo Estratégico)
9. **Tecnologias Mencionadas** (multi_select)
10. **Principais Desafios** (rich_text)
11. **Outreach** (rich_text) - NEW
12. **Potencial Cliente** (rich_text)
13. **Link da Entrevista** (url)
14. **Data** (date)
15. **Status** (select: A Processar, Concluído, Erro)

### Optional: Remove Old Columns

If migrating from an older version, you may remove:
- Estratégia Digital
- Inovação
- Resumo Estratégico

### Note

New databases created via `create_database()` will have the correct schema automatically. For existing databases, create the new columns manually in Notion.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add Notion database setup instructions"
```

---

### Task 11: Create summary commit (optional)

- [ ] **Step 1: Create summary commit**

```bash
git commit --allow-empty -m "feat: complete Gemini prompt improvements implementation

Summary of changes:
- Updated Gemini SYSTEM_PROMPT with new field structure (cargo/empresa separated)
- Added person validation to filter low-quality entries
- Updated Notion SCHEMA and add_row() mapping
- Added 8 new test cases for validation and new fields
- Updated README with Notion setup instructions

No data migration - existing Notion entries keep old structure.
Only new videos use the new schema.

Related: docs/superpowers/specs/2026-03-17-gemini-prompt-improvements-design.md"
```

---

## Summary

This implementation plan:

1. **Updates tests first** (TDD approach) - prevents breaking changes
2. **Updates Gemini prompt** with new field structure
3. **Adds validation** to filter low-quality person entries
4. **Updates Notion schema** for new databases
5. **Updates Notion mapping** to write new fields
6. **Adds 8 new test cases** for validation and edge cases
7. **Documents** Notion setup requirements

**Total tasks:** 11 (consolidated from 15)
**Total commits:** ~7 (consolidated from 15)
**Estimated time:** 2-3 hours

**Key improvements from original plan:**
- Tests updated first (TDD) - prevents intermediate failures
- Consolidated commits - cleaner git history
- Added backward compatibility test - prevents regression
- All test_notion_db.py tests updated - no orphaned tests
