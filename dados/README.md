# Dataset — Embarcações inscritas na Marinha do Brasil

Extraído em **19/07/2026** dos arquivos CSV oficiais da Diretoria de Portos e Costas (DPC),
conjunto "Marinha do Brasil — Embarcações" do portal de dados abertos federal.

- Conjunto: https://dados.gov.br/dados/conjuntos-dados/embarcacoes
- Licença: **Open Data Commons Open Database License (ODbL)** — exige atribuição e *share-alike*
- Área técnica: Diretoria de Portos e Costas · dpc.webmaster@marinha.mil.br

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `embarcacoes-por-uf.csv` | Estoque acumulado de embarcações inscritas, por UF, por ano de referência |
| `embarcacoes-por-tipo.csv` | Estoque acumulado por tipo de embarcação (24 maiores de 69), anos selecionados |
| `santa-catarina.csv` | Recorte de SC: por Organização Militar, por tipo com índice, série histórica |
| `brutos/qtd_embarcaoes_om_ano_por_tipo.csv` | **Arquivo original da DPC**, sem alteração — arquivo mais recente do portal |

Delimitador `;`, codificação UTF-8.

## Série de totais nacionais

| Ano | Embarcações inscritas |
|---:|---:|
| 2012 | 725.299 |
| 2013 | 763.459 |
| 2014 | 799.642 |
| 2015 | 831.261 |
| 2016 | 858.359 |
| 2017 | 884.041 |
| 2018 | 910.259 |
| 2019 | 936.375 |
| 2020 | 971.675 |
| 2021 | 990.857 |
| 2022 | 990.878 |
| 2023 | 990.888 |
| 2025 | 1.140.059 |

## Ressalvas de leitura — importantes

1. **Estoque acumulado, não frota ativa.** Cada arquivo traz inscrições somadas *até* o ano de
   referência. Não há desconto de embarcações baixadas, afundadas ou sucateadas. O número inclui
   embarcações miúdas (canoas, jangadas, caiaques, botes).

2. **Não existe arquivo de 2024.** O recurso rotulado "2024" no portal aponta para a mesma URL do
   rotulado "2022" (`qnt_embarcacoes_om_ano.csv`). O cabeçalho do job SQL dentro do arquivo mostra
   execução em **2023-01-04** — ou seja, é a foto do fim de 2022. O arquivo rotulado "2023" foi
   gerado em **2024-01-03**.

3. **O arquivo rotulado 2025 é o mais recente, mas sua data é incerta.** O portal informa que
   nenhum arquivo mudou desde **17/09/2024**, o que sugere que este arquivo reflete a frota de
   meados de 2024, não de 2025. Não há cabeçalho de job para confirmar. Usar com o rótulo do
   portal e a ressalva junto.

4. **Estagnação aparente entre 2021 e 2023.** Os totais praticamente não se movem
   (990.857 → 990.878 → 990.888, +31 embarcações em dois anos). Isso é forte indício de problema
   na extração ou de congelamento da base, não de mercado parado. Tratar esse trecho da série com
   desconfiança.

5. **Goiás aparece do zero em 2020.** GO tem 0 até 2019 e salta para 17.345 em 2025 — criação ou
   reorganização de Organização Militar, não crescimento real de frota.

6. **Escopo — a descrição do portal está errada.** O conjunto é descrito como embarcações de
   Esporte e Recreio, mas os dados contêm pesqueiro, rebocador, draga, balsa, petroleiro,
   porta-contentor, sonda, plataforma semi-submersível e FPSO. É o **cadastro completo** das
   Capitanias, Delegacias e Agências — toda embarcação registrada no Brasil, de canoa a
   plataforma de petróleo.

   Correção de uma versão anterior deste arquivo, que afirmava cobrir apenas o universo de
   Arqueação Bruta ≤ 100: **está errado**. A presença de FPSOs e plataformas prova o contrário.
   O registro no Tribunal Marítimo, obrigatório acima de 100 AB, é um ato *adicional* de
   propriedade — não um cadastro paralelo que substitua o da Capitania.

7. **Não há campo de porte.** As seis colunas são Distrito Naval, Organização Militar, sigla, UF,
   tipo de casco e quantidade. Sem arqueação bruta, comprimento, ano de fabricação ou potência.
   O arquivo `embarcacoes-por-porte-inferido.csv` traz uma aproximação deduzida do tipo de casco —
   é inferência da SAFEBOAT, não dado da Marinha, e está rotulada com o nível de confiança.

8. **Atividade também não é campo da fonte.** O arquivo `embarcacoes-por-atividade.csv` agrupa os
   69 rótulos de tipo em 11 categorias de atividade. O agrupamento é da SAFEBOAT. Botes e canoas
   (393.728 unidades) ficam num balde explicitamente ambíguo porque o rótulo do casco não
   distingue lazer de pesca de subsistência ou transporte ribeirinho.

## Como reproduzir

Os CSVs originais estão em `www.marinha.mil.br/dpc/sites/www.marinha.mil.br.dpc/files/dados-abertos/`.
O domínio responde com verificação anti-bot da Cloudflare a requisições diretas (curl retorna 403).
É preciso abrir antes uma página HTML do domínio (ex.: `https://www.marinha.mil.br/dpc/`) num
navegador real, deixar a verificação passar, e só então buscar os CSVs na mesma origem.

Os arquivos têm formatos e codificações diferentes por safra:

- **2012–2019** — CSV separado por vírgula, sem cabeçalho, 5 colunas (OM, sigla, UF, tipo, total),
  codificação windows-1252. O tipo `Multicasco (Catamarã, Trimarã, Tetramarã, etc)` vem entre
  aspas e contém vírgulas — exige parser que respeite aspas.
- **2020** — separado por `;`, **com** cabeçalho, 6 colunas (inclui Distrito Naval).
- **2021 e 2025** — separado por `;`, sem cabeçalho, 6 colunas, UTF-8.
- **2022 e 2023** — não são CSV: são dumps de largura fixa de saída de job SQL Server, em
  **UTF-16LE**, com preâmbulo de 4 linhas e rodapé `(N rows affected)`.
