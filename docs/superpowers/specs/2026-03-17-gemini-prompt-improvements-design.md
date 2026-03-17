# Design: Melhoria da Prompt do Gemini para Análise Estratégica

> Data: 2026-03-17
> Objetivo: Melhorar a qualidade da extração de informações da transcrição, focando em potenciais clientes para serviços de AI

## Contexto

O sistema atual analisa transcrições de vídeos de CEOs usando Gemini e cria linhas no Notion para cada pessoa identificada. O objetivo é encontrar potenciais clientes para a empresa que implementa AI ("We design AI strategy and build end-to-end solutions that scale your company").

## Problemas Identificados

1. **Pessoas sem relevância**: São adicionadas linhas onde o nome é "Não mencionado" ou com pouca informação
2. **Cargo duplica informação**: O campo "Cargo" contém tanto o cargo como a empresa
3. **Colunas redundantes**: "Estratégia Digital", "Inovação" e "Resumo Estratégico" têm conteúdo repetido
4. **Tecnologias irrelevantes**: A coluna inclui emails, telemóveis e outras informações não técnicas
5. **Falta informação AI**: Não há campos específicos sobre departamentos AI existentes
6. **Sem apoio comercial**: Não há pontos preparados para outreach/vendas

## Solução Proposta

### Nova Estrutura de Dados

**Campos retornados pelo Gemini (JSON):**

```json
[
  {
    "nome": "Nome completo",
    "cargo": "Cargo (sem empresa)",
    "empresa": "Nome da empresa",
    "usa_ia": "Sim/Não - informação extra",
    "vai_usar_ia": "Sim/Não - informação extra",
    "departamento_ai": "Sim/Não - (externo se aplicável) + o que faz resumido",
    "pessoas_departamento_ai": "Nomes e empresa exterior (se aplicável)",
    "visao_estrategica": "Estratégia/inovação curto e longo prazo agregadas",
    "tecnologias_mencionadas": ["AI", "cloud", "automação", "transformação digital", ...],
    "principais_desafios": "Desafios principais",
    "outreach": "Pontos-chave para abordagem comercial - desafios, oportunidades, mencionou orçamento/parcerias",
    "potencial_cliente": "N/10 (Quente/Morno/Frio) - justificação"
  }
]
```

**Especificações dos campos:**
- **Obrigatórios**: nome, cargo, empresa, visao_estrategica, principais_desafios
- **Opcionais**: departamento_ai, pessoas_departamento_ai, outreach
- **Tipo tecnologias_mencionadas**: Array de strings (max 10)
- **Limite caracteres**: campos texto até 2000 chars (Notion rich_text limit)

### Regras do Gemini

**Novos filtros de inclusão:**
- Nome **não** pode ser "Não mencionado"
- `cargo` e `empresa` devem ter mais de 2 caracteres e não serem "Não mencionado"
- Se mais de 3 campos estiverem "Não mencionado" → **excluir** a pessoa
- Excluir apresentadores/entrevistadores que apenas fazem perguntas
- Máximo 5 pessoas por vídeo

**Separação Cargo/Empresa:**
- `cargo`: Apenas o título/função (ex: "CEO", "CTO", "Diretor de Inovação")
- `empresa`: Nome da empresa (ex: "Microsoft", "NOS", "Farfetch")

**Visão Estratégica:**
- Combinar conteúdo de "Estratégia Digital" + "Inovação" + "Resumo Estratégico"
- Incluir visão de curto e longo prazo
- Focar em decisões, iniciativas e direção estratégica

**Tecnologias Mencionadas:**
- Responsabilidade: **Gemini deve filtrar** na resposta (não é validação Python)
- Apenas AI/ML + tecnologias de inovação + termos de negócio relevantes
- **Excluir**: emails, telemóveis, URLs, informações de contacto
- **Excluir**: tecnologias genéricas sem contexto (ex: "email", "telefone", "website")
- **Incluir**: machine learning, computer vision, LLMs, cloud, data analytics, automação, transformação digital, IA generativa, etc.

**Nota:** Python não faz validação adicional da lista de tecnologias. Confiamos que o Gemini segue as instruções da prompt.

**Departamento AI:**
- Identificar se a empresa tem departamento AI
- Se sim, descrever resumidamente o que faz
- Indicar se é externo: "Sim (externo)" ou "Sim (interno)"
- Se externo, listar na coluna "Pessoas Associadas" os nomes e empresa

**Outreach:**
- Formato: **3-5 bullet points** concisos, cada um começando com "•"
- Extrair pontos de gancho para email comercial
- Baseado em:
  - Desafios mencionados que AI pode resolver
  - Oportunidades de AI identificadas
  - Menção de orçamento/parcerias tecnológicas
  - Urgência ou timeline de projetos
  - Interesse em inovação/transformação digital
- Exemplo completo: "• Desafio com processamento de dados em tempo real\n• Interesse em IA generativa para atendimento ao cliente\n• Planeando expansão para 2025\n• Aberto a parcerias tecnológicas\n• Transformação digital como prioridade estratégica"

## Alterações de Código

### `src/analyzer.py`

**Atualizar `SYSTEM_PROMPT`:**
- Nova estrutura de campos
- Novas regras de filtragem
- Instruções específicas para cada campo

**Validação no parsing:**
```python
# Após parse do JSON, validar cada pessoa:
def _is_person_valid(person: dict) -> bool:
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

**Nota:** O wrapper `if isinstance(parsed, dict): parsed = [parsed]` deve ser **mantido** para compatibilidade com respostas antigas do Gemini ou testes.

**Retorno:**
- Manter `list[dict] | None`
- Aplicar validação após o parse
- Retornar no máximo 5 pessoas válidas

### `src/notion_db.py`

**Novos campos no mapeamento `add_row()`:**
```python
# Campos obrigatórios - se Gemini não retornar, usar "Não mencionado"
properties["Nome da Empresa"] = _rich_text(analysis.get("empresa") or "Não mencionado")
properties["Visão Estratégica"] = _rich_text(analysis.get("visao_estrategica") or "Não mencionado")
properties["Tem Departamento AI"] = _rich_text(analysis.get("departamento_ai") or "Não mencionado")

# Campos opcionais - podem ficar vazios se não aplicável
properties["Pessoas Departamento AI"] = _rich_text(analysis.get("pessoas_departamento_ai") or "")
properties["Outreach"] = _rich_text(analysis.get("outreach") or "")
```

**Campo atualizado:**
```python
properties["Cargo"] = _rich_text(analysis.get("cargo", ""))  # Sem empresa
```

**Campos removidos do mapeamento:**
- `estrategia_digital`
- `inovacao`
- `resumo_estrategico`
(Substituídos por `visao_estrategica`)

**SCHEMA (para referência, usado em `create_database()`):**
- `SCHEMA` em `notion_db.py` precisa ser atualizado
- Remover: `Estratégia Digital`, `Inovação`, `Resumo Estratégico`
- Adicionar: `Nome da Empresa` (rich_text), `Tem Departamento AI` (rich_text), `Pessoas Departamento AI` (rich_text), `Visão Estratégica` (rich_text), `Outreach` (rich_text)

**Nota:** Novas databases criadas com código atualizado terão o schema correto.

**AVISO CRÍTICO:** Para databases existentes, o utilizador deve **criar manualmente as novas colunas** no Notion antes de usar o código atualizado. Sem estas colunas, `add_row()` falhará.

### `streamlit_app.py` e `src/main.py`

**Sem alterações necessárias:**
- Ambos chamam `analyze_transcript()` e iteram sobre o resultado
- Não acedem diretamente aos campos, apenas passam para `add_row()`

## Colunas do Notion (Criação Manual)

O utilizador deve criar as seguintes colunas no Notion antes de usar o código atualizado:

1. **Nome** (title) - já existe
2. **Cargo** (rich_text) - já existe (vai sem empresa)
3. **Nome da Empresa** (rich_text) - **NOVA**
4. **Usa IA** (rich_text) - já existe
5. **Vai Usar IA** (rich_text) - já existe
6. **Tem Departamento AI** (rich_text) - **NOVA**
7. **Pessoas Departamento AI** (rich_text) - **NOVA**
8. **Visão Estratégica** (rich_text) - **NOVA** (substitui 3 colunas)
9. **Tecnologias Mencionadas** (multi_select) - já existe (filtro melhorado)
10. **Principais Desafios** (rich_text) - já existe
11. **Outreach** (rich_text) - **NOVA**
12. **Potencial Cliente** (rich_text) - já existe
13. **Link da Entrevista** (url) - já existe
14. **Data** (date) - já existe
15. **Status** (select) - já existe

**Colunas a remover manualmente (opcional):**
- Estratégia Digital
- Inovação
- Resumo Estratégico

## Migração de Dados

**Abordagem:**
- Dados existentes **não são migrados**
- Apenas **novos vídeos** usam a nova estrutura
- Vídeos já processados mantêm-se inalterados

**Justificativa:**
- Separação automática de cargo/empresa é propensa a erros
- Revisão manual seria necessária para garantir qualidade
- Focus em qualidade de dados novos vs. migração imperfeita

**Coexistência:**
- Código atualizado pode processar novos vídeos com novo schema
- Dados antigos permanecem no Notion com estrutura antiga
- Não há conflito - cada linha é independente

## Testes

### Testes Unitários (`tests/test_analyzer.py`)

**Atualizar testes existentes:**
- `test_analyze_transcript_returns_structured_data`: Mudar de `result["nome"]` para `result[0]["nome"]` (acesso à lista)
- Adicionar teste com múltiplas pessoas: mock retornando array JSON

**Novos casos de teste (com assertions específicas):**
1. `test_excludes_person_without_name`: Pessoa com nome "Não mencionado" ou vazio → `assert len(result) == 0`
2. `test_excludes_person_with_too_many_empty_fields`: Pessoa com >3 campos "Não mencionado" → `assert len(result) == 0`
3. `test_excludes_person_with_short_cargo_empresa`: Pessoa com cargo/empresa <= 2 caracteres → `assert len(result) == 0`
4. `test_includes_valid_person`: Pessoa com todos campos válidos → `assert len(result) > 0` e `assert result[0]["cargo"]` != pessoa.cargo_original
5. `test_max_5_persons_returned`: Gemini retorna 7 pessoas → `assert len(result) == 5`
6. `test_outreach_format`: `assert len(outreach.split('\n')) >= 3` e `assert all('•' in line or '-' in line for line in outreach.split('\n'))`
7. `test_cargo_empresa_separated`: `assert "cargo" in result[0]` e `assert "empresa" in result[0]` são campos distintos

### Testes de Integração

**Manual (via Streamlit):**
1. Processar vídeo conhecido com 1 CEO válido
2. Processar vídeo com múltiplos entrevistados
3. Verificar que pessoas inválidas são excluídas
4. Verificar que colunas do Notion são preenchidas corretamente

## Rollback

Se necessário, é possível reverter:
- Git revert dos commits
- Restaurar `SYSTEM_PROMPT` anterior
- Restaurar mapeamento de campos em `notion_db.py`
- Dados já escritos no Notion permanecem (não são afetados)

**Aviso sobre schema do Notion:**
- Após criar as novas colunas no Notion, o código antigo não funcionará
- Se precisar de voltar ao código antigo, deve também remover as colunas novas manualmente
- Recomenda-se fazer backup do Notion antes de criar/alterar colunas

## Próximos Passos

Após aprovação deste design:
1. Criar plano de implementação detalhado (writing-plans)
2. Implementar alterações código
3. Atualizar testes
4. Testar manualmente via Streamlit
5. Documentar no README (instruções para criar colunas Notion)
