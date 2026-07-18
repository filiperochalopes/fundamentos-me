---
name: fundamentos-readme-enrichment
description: Ingerir lições Fundamentos a partir de PDF ou vídeo público do YouTube, transcrever áudio com MLX Whisper e enriquecer cada README com resumo, referências e textos bíblicos agrupados por tema. Criar TMP.md provisório quando o PDF oficial ainda não existe e manter a fonte consolidada do NotebookLM completa. Usar ao criar, atualizar, revisar ou auditar lições e suas seções editoriais no acervo Fundamentos.
---

# Ingerir e enriquecer lições

Ler `AGENTS.md` e o `SKILL.md` da raiz antes de alterar o acervo. Tratar o PDF local como fonte canônica quando existir. Se a lição ainda não tiver PDF, usar o vídeo público informado pelo usuário como fonte provisória, preservar essa condição no catálogo e no README e criar `TMP.md`.

## Extrair o conteúdo

Executar:

```bash
python3 skills/fundamentos-readme-enrichment/scripts/extract_lesson.py \
  "<caminho-da-licao.pdf>" --output-dir /tmp/fundamentos-extract
```

O comando gera texto por página, uma lista JSON de referências candidatas na ordem da primeira ocorrência e um rascunho Markdown. Usar o Python empacotado pelo Codex quando `pypdf` não estiver disponível no Python do sistema. Consultar [referencias-biblicas.md](references/referencias-biblicas.md) quando a extração tiver abreviações incomuns ou falsos positivos.

Não confiar cegamente na expressão regular. Conferir cada referência no texto extraído e, quando a página estiver ilegível, renderizar e inspecionar visualmente o PDF. Não inventar referências nem completar versículos por memória.

## Ingerir uma lição do YouTube

Usar o script reutilizável, que baixa somente o áudio com `yt-dlp` e o transcreve localmente:

```bash
python3 skills/fundamentos-readme-enrichment/scripts/ingest_youtube.py \
  "https://www.youtube.com/watch?v=<id>" \
  --output-dir /tmp/fundamentos-youtube-ingest
```

O script usa o `yt-dlp` instalado no ambiente ou, como compatibilidade local, o executável do projeto irmão `youtube-downloader-mcp-server`. Ele ativa o cliente Android e um runtime Node local, combinação necessária para evitar respostas 403 observadas em alguns formatos do YouTube. Não habilitar componentes remotos nem execução de código baixado pelo extrator.

A transcrição padrão equivale a:

```bash
mlx_whisper \
  "<audio.m4a>" \
  --model mlx-community/whisper-large-v3-mlx \
  --language pt \
  --condition-on-previous-text False \
  --word-timestamps True \
  --hallucination-silence-threshold 2 \
  --output-format txt
```

Manter o áudio fora do acervo, em diretório temporário. Nas lições provisórias, arquivar a transcrição automática como `ytvideo_transcription.txt` usando o utilitário:

```bash
python3 skills/fundamentos-readme-enrichment/scripts/archive_transcript.py \
  /tmp/fundamentos-youtube-ingest/<id>.txt \
  "<pasta-da-lição>/ytvideo_transcription.txt" \
  --title "<título>" \
  --youtube-url "https://www.youtube.com/watch?v=<id>" \
  --method "MLX Whisper"
```

O utilitário também aceita uma legenda `json3` original do YouTube como fonte de recuperação ou conferência. Conferir especialmente nomes próprios, referências bíblicas, números e os minutos iniciais e finais, nos quais o apresentador pode declarar a posição da lição em uma sequência.

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

## Criar o TMP.md provisório

Quando `transcript_pdf` estiver ausente, criar `TMP.md` na pasta da lição com esta arquitetura simplificada:

```markdown
# Lição <número> - <título>

> Material provisório elaborado a partir do vídeo público; será substituído pelo PDF oficial quando disponível.

## Introdução
...

## <divisões reais do argumento>
...

## Referências e textos bíblicos
...

## Aplicações e perguntas
...

## Conclusão
...
```

O `TMP.md` é uma síntese editorial, não uma transcrição literal. Preservar a ordem do ensino, registrar sua tese, argumentos, aplicações e referências verificadas na fala. Não atribuir ao professor conclusões que sejam apenas inferências editoriais. Manter `ytvideo_transcription.txt` ao lado dele como registro documental da transcrição automática. O gerador `scripts/build_notebooklm_source.py` deve preferir o PDF e usar o `TMP.md` somente na ausência dele; não incluir a transcrição bruta como uma segunda cópia da mesma lição.

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
python3 -m py_compile skills/fundamentos-readme-enrichment/scripts/ingest_youtube.py
python3 -m py_compile skills/fundamentos-readme-enrichment/scripts/archive_transcript.py
python3 /Users/filipelopes/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/fundamentos-readme-enrichment
find . -type f -name README.md | wc -l
find . -type f -name '*.pdf' | wc -l
find . -type f -name '*.part' | wc -l
```
