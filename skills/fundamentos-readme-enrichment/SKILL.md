---
name: fundamentos-readme-enrichment
description: Extrair conteúdo de PDFs das lições Fundamentos e enriquecer cada README com um resumo de um parágrafo, referências e textos bíblicos agrupados por tema e um link de leitura compatível com biblia.filipelopes.me. Usar ao criar, atualizar, revisar ou auditar as seções Resumo e Referências e Textos Bíblicos do acervo Fundamentos.
---

# Enriquecer READMEs das lições

Ler `AGENTS.md` e o `SKILL.md` da raiz antes de alterar o acervo. Tratar o PDF local de cada lição como fonte canônica do resumo, dos temas e das referências.

## Extrair o conteúdo

Executar:

```bash
python3 skills/fundamentos-readme-enrichment/scripts/extract_lesson.py \
  "<caminho-da-licao.pdf>" --output-dir /tmp/fundamentos-extract
```

O comando gera texto por página, uma lista JSON de referências candidatas na ordem da primeira ocorrência e um rascunho Markdown. Usar o Python empacotado pelo Codex quando `pypdf` não estiver disponível no Python do sistema. Consultar [referencias-biblicas.md](references/referencias-biblicas.md) quando a extração tiver abreviações incomuns ou falsos positivos.

Não confiar cegamente na expressão regular. Conferir cada referência no texto extraído e, quando a página estiver ilegível, renderizar e inspecionar visualmente o PDF. Não inventar referências nem completar versículos por memória.

## Redigir o README

Inserir imediatamente depois do título:

```markdown
# <número> - <título>

<resumo em um único parágrafo>

## Referências e Textos Bíblicos

**👉🏼  <afirmação ou tema presente na lição>**
<referências relacionadas, separadas por ` | `>

[Link para leitura](https://biblia.filipelopes.me/?q=<consulta>)

## Materiais
```

Redigir o resumo com 3 a 6 frases em um único parágrafo, cobrindo a tese e o desenvolvimento central da lição sem mencionar o PDF ou o processo de extração.

Agrupar as referências conforme as divisões argumentativas reais da lição. Escrever cada tema em negrito, iniciando por `👉🏼` e mantendo a ordem em que os temas aparecem no PDF. Dentro de cada tema, manter a ordem de primeira aparição. Remover duplicatas exatas, mas preservar referências repetidas quando o PDF as usa deliberadamente em argumentos diferentes.

Usar abreviações sem espaço em livros numerados (`1Jo`, `2Pe`, `1Co`). Usar vírgula para versículos não contíguos, hífen para intervalos, ponto e vírgula para referências diferentes do mesmo livro e ` | ` entre livros ou blocos apresentados separadamente. Preservar referências introdutórias ou textos-chave no link mesmo quando não couberem naturalmente em um agrupamento temático.

## Gerar o link

Gerar a consulta a partir da sequência completa e deduplicada de referências:

```bash
python3 skills/fundamentos-readme-enrichment/scripts/extract_lesson.py \
  --link 'Is 9:6' 'Jo 1:1-3' 'Gn 1:26'
```

O link deve usar `https://biblia.filipelopes.me/?q=` e codificar a consulta formada por referências separadas por ponto e vírgula. O site consulta `GET /api/v1/biblia/verse?q=<consulta>&versao=ARA`; usar esse endpoint apenas para validar que a consulta produz o texto esperado quando houver acesso à rede, nunca para inventar ou corrigir conteúdo ausente do PDF.

## Atualizar com segurança

Preservar integralmente `## Materiais`, `## Podcasts` e links existentes. Se o README já tiver as seções novas, substituí-las sem duplicá-las. Nunca reescrever os 139 READMEs com conteúdo genérico ou com o mesmo resumo.

Para processar todo o acervo, primeiro gerar o relatório sem escrita e revisar amostras; depois repetir com `--write`:

```bash
python3 skills/fundamentos-readme-enrichment/scripts/enrich_archive.py
python3 skills/fundamentos-readme-enrichment/scripts/enrich_archive.py --write
```

Revisar um README representativo e validar ao final:

```bash
python3 -m py_compile skills/fundamentos-readme-enrichment/scripts/extract_lesson.py
python3 /Users/filipelopes/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/fundamentos-readme-enrichment
find . -type f -name README.md | wc -l
find . -type f -name '*.pdf' | wc -l
find . -type f -name '*.part' | wc -l
```
