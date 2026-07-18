# Arquivo de aulas do Fundamentos

Este repositório mantém um arquivo local das aulas do [Fundamentos](https://fundamentos.me), organizado por ciclo e por aula. Cada aula contém um `README.md` com seu resumo, referências bíblicas e links. A fonte textual é a transcrição oficial em PDF quando disponível; lições ainda sem PDF podem usar temporariamente um `TMP.md` produzido a partir do vídeo público.

## Organização

O acervo segue esta estrutura:

```text
<número> - <título do ciclo>/
  <número global> - <título da aula>/
    README.md
    <número global> - <título da aula>.pdf
    TMP.md                              # somente enquanto o PDF não existe
    ytvideo_transcription.txt            # transcrição automática do vídeo temporário
```

O arquivo `fundamentos-links.json` é o catálogo local normalizado que relaciona ciclos, aulas e materiais. A numeração das aulas é global e os títulos originais são preservados no catálogo e nos arquivos Markdown.

Nas lições temporárias sem PDF, `ytvideo_transcription.txt` preserva a transcrição automática do vídeo usado como fonte. Esse arquivo é documental e pode conter erros de reconhecimento; o `TMP.md` é a síntese editorial revisada, organizada em seções semelhantes às do material oficial. Quando o PDF oficial for publicado, ele volta a ser a fonte canônica, e o gerador do NotebookLM deixa de usar o `TMP.md` automaticamente.

Diretórios de ciclos conhecidos que ainda não possuem lições mantêm um arquivo `.gitkeep`, para que sua estrutura vazia seja preservada pelo Git.

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

O resultado é `NotebookLMSource.pdf`, com uma seção por aula no formato `Ciclo - Lição`. O gerador prefere o PDF oficial e usa `TMP.md` apenas quando a lição ainda não tem PDF, sem duplicar a aula. O documento preserva parágrafos, títulos e citações bíblicas, mas não replica o layout das transcrições originais. Isso reduz o peso visual e permite carregar todo o acervo como uma única fonte no NotebookLM.

## Validar o acervo

```bash
jq empty fundamentos-links.json
python3 -m py_compile scripts/build_lesson_archive.py
find . -type f -name README.md | wc -l
find . -type f -name '*.pdf' | wc -l
find . -type f -name '*.part' | wc -l
```

O catálogo local contém 19 ciclos e 145 aulas. As lições 140 a 145 vieram de vídeos públicos do YouTube e estão provisoriamente no ciclo 15; essa associação não é oficial e poderá mudar quando o planejamento definitivo for publicado. Os ciclos 16 a 19 foram criados com os títulos exibidos no aplicativo e permanecem vazios.
