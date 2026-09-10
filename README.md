# SAFEBOAT · Panorama do Registro Náutico Brasileiro

Dossiê de inteligência de mercado sobre embarcações inscritas na Marinha do Brasil,
construído a partir dos arquivos oficiais da Diretoria de Portos e Costas (DPC).

Publicado em https://marcelocesarreis.github.io/safeboat-mercado

## Conteúdo

| Caminho | O que é |
|---|---|
| `index.html` | O dossiê nacional. Abra no navegador; o botão "Salvar em PDF" gera a versão para circular. |
| `sc.html` | Recorte de Santa Catarina — por Capitania, por tipo e por atividade |
| `dados/santa-catarina.csv` | Dados do recorte catarinense |
| `dados/brutos/` | Arquivo CSV original da DPC, sem alteração |
| `dados/embarcacoes-por-uf.csv` | 27 unidades federativas × 13 anos de referência |
| `dados/embarcacoes-por-tipo.csv` | 24 maiores tipos de casco, anos selecionados |
| `dados/embarcacoes-por-atividade.csv` | 69 tipos agrupados em 11 categorias de atividade |
| `dados/embarcacoes-por-porte-inferido.csv` | Faixas de porte deduzidas do tipo — aproximação |
| `dados/README.md` | Proveniência, ressalvas de leitura e como reproduzir a extração |
| `folder-br-marinas/` | Folder de apresentação do SAFEBOAT para a BR Marinas — `index.html` (8 páginas A4, botão "Salvar em PDF") e `safeboat-br-marinas.pdf` já gerado. Imagens e textos vêm do site safeboat.tech |

## Número principal

**1.140.059 embarcações registradas** no arquivo mais recente da DPC — estoque acumulado no
cadastro das Capitanias, Delegacias e Agências.

É o **cadastro completo**, não apenas esporte e recreio: a base contém pesqueiro, rebocador,
balsa, petroleiro, porta-contentor e até FPSO e plataforma de perfuração. A descrição do
conjunto no portal de dados abertos, que fala em "Esporte e Recreio", está errada.

Série de 2012 a 2025. O total de 2019 fecha em 936.375.

## Quebra por atividade

| Atividade | Embarcações | % |
|---|---:|---:|
| Esporte e recreio | 454.236 | 39,8% |
| Ambíguo — bote e canoa | 393.728 | 34,5% |
| Não classificado na fonte | 136.406 | 12,0% |
| Pesca | 57.524 | 5,0% |
| Transporte de carga | 55.797 | 4,9% |
| Transporte de passageiros | 20.891 | 1,8% |
| Serviço portuário e obras | 19.294 | 1,7% |
| Apoio marítimo e offshore | 1.107 | 0,1% |
| Granéis líquidos | 736 | 0,1% |
| Exploração de petróleo | 170 | 0,0% |
| Pesquisa e especiais | 170 | 0,0% |

**A classificação por atividade é da SAFEBOAT, não da Marinha** — a fonte publica apenas
rótulos de tipo de casco. Os 69 tipos estão alocados, sem órfãos, e a soma fecha no total.

Note que **46,5% do cadastro não tem atividade determinável** (o balde ambíguo mais o
"Outros"). Ao citar participação de lazer, prefira a faixa 39,8%–74,4% a um ponto único.

## Porte

**Não é possível a partir desta fonte.** O arquivo não tem arqueação bruta, comprimento nem
ano de fabricação. O CSV de porte inferido é aproximação deduzida do tipo de casco, rotulada
com nível de confiança. Porte real está no Tribunal Marítimo (acima de 100 AB), na ANTAQ
(navegação interior e cabotagem) ou via pedido LAI ao SISGEMB.

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
