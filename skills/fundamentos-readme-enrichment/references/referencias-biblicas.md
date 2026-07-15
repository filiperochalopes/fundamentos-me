# Normalização de referências bíblicas

## Convenções

- Usar abreviações portuguesas compactas: `Gn`, `Ex`, `Sl`, `Is`, `Mt`, `Mc`, `Lc`, `Jo`, `At`, `Rm`, `1Co`, `2Co`, `Gl`, `Ef`, `Fp`, `Cl`, `1Ts`, `2Ts`, `1Tm`, `2Tm`, `Tt`, `Fm`, `Hb`, `Tg`, `1Pe`, `2Pe`, `1Jo`, `2Jo`, `3Jo`, `Jd`, `Ap`.
- Escrever capítulo e versículo como `Jo 8:28`.
- Usar `Jo 8:28,58-59` para mais de um trecho no mesmo capítulo.
- Usar `Mt 8:1-3; 15:24-25; 20:20` quando o livro é o mesmo e os capítulos mudam.
- Separar blocos independentes com ` | `.
- Remover espaços entre o ordinal e o livro: `1 Jo` vira `1Jo`.
- Converter travessões usados como intervalo para hífen ASCII.

## Revisão de candidatos

Descartar números de lição, horários, datas, páginas e enumerações que coincidam com o padrão capítulo-versículo. Conferir referências quebradas por mudança de linha e referências cujo livro aparece uma vez seguido por vários capítulos. A lista extraída pelo script é candidata, não resultado editorial final.

O link de leitura recebe uma única consulta com todas as referências, na ordem de primeira aparição, separadas por `;`. Exemplo:

```text
Is 9:6;Jo 1:1-3;Gn 1:26
```

O site aceita a consulta compartilhável em `/?q=...`. Para validação automatizada, usar `GET /api/v1/biblia/verse` com os parâmetros `q` e `versao=ARA`.
