# Arquivo de aulas do Fundamentos

Este repositório mantém um arquivo local das aulas do [Fundamentos](https://fundamentos.me), organizado por ciclo e por aula. Cada aula contém a transcrição em PDF e um `README.md` com os links para os materiais disponíveis, como vídeos, podcasts e a fonte original da transcrição.

## Organização

O acervo segue esta estrutura:

```text
<número> - <título do ciclo>/
  <número global> - <título da aula>/
    README.md
    <número global> - <título da aula>.pdf
```

O arquivo `fundamentos-links.json` é o catálogo local normalizado que relaciona ciclos, aulas e materiais. A numeração das aulas é global e os títulos originais são preservados no catálogo e nos arquivos Markdown.

## Reconstruir o acervo

Para recriar os diretórios e baixar transcrições ausentes ou inválidas:

```bash
python3 scripts/build_lesson_archive.py
```

O processo é idempotente: mantém PDFs válidos já existentes, reescreve os índices gerados e usa arquivos temporários durante downloads.

## Gerar um ZIP dos PDFs

Para reunir recursivamente todas as transcrições em um único pacote:

```bash
./scripts/zip_lesson_pdfs.sh
```

O arquivo `fundamentos-pdfs.zip` será criado na raiz do repositório. Dentro dele, todos os PDFs ficam diretamente na raiz, sem pastas intermediárias, facilitando o envio ao NotebookLM. ZIPs são ignorados pelo Git.

Também é possível informar outro caminho de saída:

```bash
./scripts/zip_lesson_pdfs.sh /caminho/para/meu-arquivo.zip
```

## Gerar a fonte única para o NotebookLM

Instale as dependências Python:

```bash
python3 -m pip install -r requirements.txt
```

Depois, gere um único PDF com o conteúdo textual de todas as aulas:

```bash
python3 scripts/build_notebooklm_source.py
```

O resultado é `NotebookLMSource.pdf`, com uma seção por aula no formato `Ciclo - Lição`. O documento preserva parágrafos, títulos e citações bíblicas, mas não replica o layout das transcrições originais. Isso reduz o peso visual e permite carregar todo o acervo como uma única fonte no NotebookLM.

## Validar o acervo

```bash
jq empty fundamentos-links.json
python3 -m py_compile scripts/build_lesson_archive.py
find . -type f -name README.md | wc -l
find . -type f -name '*.pdf' | wc -l
find . -type f -name '*.part' | wc -l
```

No catálogo capturado em 15 de julho de 2026 há 15 ciclos e 139 aulas. O ciclo 15 está presente, mas inativo e sem aulas nesse retrato.
