# SAFEBOAT · Panorama do Registro Náutico Brasileiro

Dossiê de inteligência de mercado sobre embarcações inscritas na Marinha do Brasil,
construído a partir dos arquivos oficiais da Diretoria de Portos e Costas (DPC).

Publicado em https://marcelocesarreis.github.io/safeboat-mercado

## Conteúdo

| Caminho | O que é |
|---|---|
| `index.html` | O dossiê. Abra no navegador; o botão "Salvar em PDF" gera a versão para circular. |
| `dados/embarcacoes-por-uf.csv` | 27 unidades federativas × 13 anos de referência |
| `dados/embarcacoes-por-tipo.csv` | 24 maiores tipos de casco, anos selecionados |
| `dados/README.md` | Proveniência, ressalvas de leitura e como reproduzir a extração |

## Número principal

**1.140.059 embarcações inscritas** no arquivo mais recente da DPC — estoque acumulado
no cadastro das Capitanias, Delegacias e Agências, universo de Arqueação Bruta ≤ 100.

Série de 2012 a 2025. O total de 2019 fecha em 936.375.

## Ler antes de citar qualquer número

1. **É estoque acumulado, não frota ativa.** Sem desconto de embarcações baixadas ou sucateadas.
2. **A base congela entre 2021 e 2023** (+31 embarcações em dois anos) — falha de extração na
   fonte, não mercado parado.
3. **Não existe arquivo de 2024**, e o rotulado "2025" provavelmente reflete meados de 2024.

O detalhamento completo dessas ressalvas está em `dados/README.md`.

## Rodar localmente

```
npx http-server . -p 8125 -c-1
```

Ou simplesmente abrir `index.html` no navegador.

## Licença dos dados

Os dados derivam do conjunto "Embarcações" da Marinha do Brasil, publicado no portal de dados
abertos federal sob **Open Data Commons Open Database License (ODbL)** — licença que exige
atribuição e impõe *share-alike* sobre bases derivadas.

> Fonte: Marinha do Brasil / Diretoria de Portos e Costas — conjunto "Embarcações",
> https://dados.gov.br/dados/conjuntos-dados/embarcacoes

**Pendência:** validar com o jurídico o alcance do *share-alike* antes de embutir estes dados
em produto ou material comercial da SAFEBOAT.
