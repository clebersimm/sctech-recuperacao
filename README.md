# Esteira analítica de compras públicas (PNCP 2025) para a Controladoria

## Auditoria dos dados

Antes de corrigir qualquer coisa, os 3 arquivos brutos de `data/raw/` foram auditados, ou seja, cada problema foi **contado**: quantos registros ele afeta.
As contagens são feitas pelo script [`src/auditoria.py`](src/auditoria.py), que lê os arquivos sem mudar nada e mostra as tabelas abaixo:

```bash
python -m src.auditoria
```

> Um mesmo registro pode ter mais de um problema (por exemplo, `R$ 1.234,56` tem `R$` **e** milhar no padrão brasileiro). Por isso as colunas de uma tabela não devem ser somadas.

### Documentos (CNPJ/CPF)

| Problema | `compras.cnpj_orgao` | `resultados.ni_fornecedor` |
|---|---|---|
| Total de registros | 2.042 | 15.896 |
| Vazio ou nulo disfarçado (N/A, -, ...) | 0 | 0 |
| Com máscara (pontos, barra, traço) | 176 | 1.633 |
| Com espaços sobrando nas pontas | 131 | 990 |
| CNPJ com zeros perdidos no começo (PJ) | 77 | 194 |
| CPF com zeros perdidos no começo (PF) | 0 | 159 |
| Com dígitos demais | 0 | 0 |
| PJ com 11 dígitos (tamanho de CPF) | 3 | 1 |
| Estrangeiros (PE), não recebem zeros | 0 | 21 |
| Mesmo documento com tipos de pessoa diferentes | 0 | 0 |
| Documentos distintos antes de limpar | 539 | 11.418 |
| Documentos distintos depois de limpar | 370 | 10.299 |

O que esses números mostram:

- **Zeros perdidos:** acontece quando o arquivo passou por uma planilha e o CNPJ virou número (`01222333000181` → `1222333000181`). O tamanho certo depende do tipo de pessoa: **PJ = 14 dígitos (CNPJ)** e **PF = 11 dígitos (CPF)**.
- **PJ com 11 dígitos:** parecem CPF, mas são CNPJs que perderam 3 zeros. No órgão isso é certo, porque quem compra é sempre um órgão. No fornecedor, o tipo de pessoa (PJ) confirma.
- **Estrangeiros (PE):** o identificador deles (ex.: `ESTRANG0002421`) não é CNPJ nem CPF, então não recebe zeros à esquerda.
- **Mistura de tipos de pessoa:** nenhum documento aparece como PJ em um registro e como PF em outro.
- **Impacto:** sem a limpeza, o mesmo órgão ou fornecedor seria contado várias vezes. Os órgãos cairiam de 539 para 370 documentos diferentes e os fornecedores de 11.418 para 10.299.

### Dinheiro e números

Formato do número (cada registro cai em **um só** formato; somando esses formatos se chega ao total):

| Coluna | Total | Ponto decimal (`1234.56`) | Só vírgula decimal (`12,5`) | BR com milhar (`1.234,56`) | US com milhar (`1,234.56`) | Milhar sem decimal (`1.234.567`) |
|---|---|---|---|---|---|---|
| compras.valor_total_estimado | 2.042 | 1.533 | 42 | 403 | 64 | 0 |
| compras.valor_total_homologado | 2.042 | 1.523 | 36 | 406 | 77 | 0 |
| itens.quantidade | 7.077 | 5.596 | 1.262 | 185 | 34 | 0 |
| itens.valor_unitario_estimado | 7.077 | 5.475 | 953 | 536 | 113 | 5 |
| itens.valor_total_estimado | 7.077 | 5.415 | 359 | 1.103 | 200 | 3 |
| resultados.quantidade_homologada | 15.896 | 12.472 | 2.245 | 974 | 205 | 0 |
| resultados.valor_unitario_homologado | 15.896 | 12.282 | 2.077 | 1.279 | 258 | 6 |
| resultados.valor_total_homologado | 15.896 | 12.064 | 690 | 2.625 | 517 | 49 |

Outros problemas nas mesmas colunas:

| Coluna | Com `R$` | Espaços sobrando | Ambíguo (`1.500`) | Negativo | Zero | Vazio ou nulo disfarçado | Fora do padrão |
|---|---|---|---|---|---|---|---|
| compras.valor_total_estimado | 344 | 172 | 0 | 0 | 92 | 0 | 0 |
| compras.valor_total_homologado | 346 | 153 | 0 | 0 | 0 | 0 | 0 |
| itens.quantidade | 1.148 | 551 | 0 | 0 | 16 | 0 | 0 |
| itens.valor_unitario_estimado | 1.188 | 561 | 31 | 0 | 79 | 0 | 0 |
| itens.valor_total_estimado | 1.171 | 588 | 9 | 0 | 95 | 0 | 0 |
| resultados.quantidade_homologada | 2.561 | 1.267 | 0 | 0 | 177 | 0 | 0 |
| resultados.valor_unitario_homologado | 2.650 | 1.352 | 80 | 0 | 92 | 0 | 0 |
| resultados.valor_total_homologado | 2.647 | 1.332 | 17 | 0 | 217 | 0 | 0 |

O que esses números mostram:

- **Formatos misturados na mesma coluna:** o padrão brasileiro (`1.234,56`) e o americano (`1,234.56`) aparecem juntos. Se a conversão tratar todos do mesmo jeito, os valores ficam 100 ou 1.000 vezes maiores ou menores.
- **`R$` até nas quantidades:** `itens.quantidade` e `resultados.quantidade_homologada` também vêm com `R$`. A limpeza tem que tratar as quantidades igual ao dinheiro.
- **Espaços sobrando:** incluem o espaço "invisível" (NBSP, `\xa0`), como em `R$\xa03,00\xa0`.
- **Ambíguo (`1.500`):** poderia ser mil e quinhentos ou um e meio. Pela regra do enunciado, ponto ou vírgula **sozinho** é sempre decimal, então vale **1,5**. Esses registros já estão contados na tabela de formatos.
- **Negativos: nenhum.** Não aparece valor entre parênteses `(1.500,00)` nem com sinal de menos. A limpeza continua preparada para esse caso, mas ele não ocorre nesta base.
- **Zero:** o `0` em coluna de número é um valor de verdade, não um vazio. Os itens com valor zero são tratados depois, na regra de itens rejeitados (Sprint 3).
- **Fora do padrão: nenhum.** Todo valor se encaixa em um dos formatos acima.

### Datas em formatos diferentes

| Formato / problema | `compras.data_publicacao` | `compras.data_abertura_proposta` | `compras.data_encerramento_proposta` | `resultados.data_resultado` | `resultados.data_cancelamento` |
|---|---|---|---|---|---|
| Total | 2.042 | 2.042 | 2.042 | 15.896 | 15.896 |
| Vazio | 0 | 617 | 617 | 0 | 15.834 |
| ISO com hora (`2025-01-06T11:51:06`) | 1.319 | 912 | 926 | 0 | 62 |
| ISO (`2025-10-31`) | 0 | 0 | 0 | 10.301 | 0 |
| BR com hora (`02/01/2025 09:03`) | 126 | 86 | 101 | 934 | 0 |
| BR (`03/01/2025`) | 117 | 78 | 78 | 929 | 0 |
| Com pontos (`02.01.2025`) | 120 | 83 | 84 | 937 | 0 |
| Com traços (`02-01-2025`) | 138 | 85 | 75 | 912 | 0 |
| Ano primeiro com barras (`2025/01/08`) | 116 | 86 | 78 | 960 | 0 |
| Compacto (`20250103`) | 106 | 95 | 83 | 923 | 0 |
| Data impossível (ex.: 31/02) | 0 | 0 | 0 | 0 | 0 |
| Ano fora de 2000-2030 | 0 | 0 | 65 | 0 | 0 |
| Fora do padrão | 0 | 0 | 0 | 0 | 0 |
| Data mais antiga | 02/01/2025 | 03/05/2023 | 03/05/2023 | 17/12/2024 | 28/03/2025 |
| Data mais nova | 31/12/2025 | 02/09/2026 | 31/12/9999 | 05/10/2026 | 21/07/2026 |

O que esses números mostram:

- **8 formatos na mesma coluna:** a data de publicação e a data de homologação (`data_resultado`) misturam 7 formatos cada, em proporções parecidas. Quando o dia vem antes do mês, a data é lida no padrão brasileiro: `02/01/2025` é 2 de janeiro, e não 1º de fevereiro.
- **Nenhuma data impossível** e **nenhuma fora dos formatos conhecidos**. A hora é descartada, porque só o dia importa.
- **Período certo:** as publicações vão de 02/01/2025 a 31/12/2025, os 12 meses do recorte. Homologações em 2026 são esperadas, porque o edital sai em 2025 e o resultado vem depois.
- **Vazios de verdade:** `data_abertura_proposta` e `data_encerramento_proposta` estão vazias em 617 contratações. `data_cancelamento` só vem preenchida nos 62 resultados cancelados, e nesse caso o vazio quer dizer "não cancelado".
- **Anos absurdos (65):** aparecem só em `data_encerramento_proposta` e todos são de **Credenciamento**, com prazos como 2035, 2099 e até 31/12/9999 ("sem prazo para terminar"). Essa coluna não vai para a fato, então esses valores não afetam o resultado.

### Homologação antes da publicação do edital

Uma homologação (`resultados.data_resultado`) não pode vir antes da publicação do edital (`compras.data_publicacao`). A comparação usa só o dia, sem a hora.

| Situação | Registros | De um total de |
|---|---|---|
| Resultados com homologação antes da publicação | 234 | 15.896 |
| ... entre os resultados não cancelados | 234 | 15.834 |
| Itens com pelo menos 1 resultado invertido | 234 | 7.077 |
| Contratações com pelo menos 1 resultado invertido | 134 | 2.042 |
| Resultados homologados no mesmo dia da publicação (válidos, ciclo de 0 dia) | 1.239 | 15.896 |
| Resultados sem data de publicação ou de homologação para comparar | 0 | 15.896 |

O que esses números mostram:

- **234 datas invertidas**, de 1 a 324 dias antes da publicação (na metade dos casos, só 1 dia antes). Nenhuma delas está num resultado cancelado, e cada item afetado tem só 1 resultado invertido.
- **Como será tratado (regra 7):** o item **continua na fato**, mas fica **sem data de homologação e sem ciclo**. Quantos itens da fato ficam assim só se sabe na Sprint 3, depois de escolher o vencedor de cada item.
- **Mesmo dia não é erro:** os 1.239 resultados homologados no dia da publicação são válidos e têm ciclo de 0 dia.

### Vazios disfarçados

São textos que parecem preenchidos, mas querem dizer "sem valor". A comparação ignora maiúsculas e minúsculas (`NULL`, `Null` e `n/a` contam igual). As colunas de dinheiro e de data ficam de fora, porque nelas o `0` é um número de verdade.

| Coluna | Total | Vazio de verdade | Vazio disfarçado | Valores encontrados (quantidade) |
|---|---|---|---|---|
| `compras.processo` | 2.042 | 0 | 77 | `-` (16), `0` (12), `NULL` (12), `N/A` (11), `SEM INFORMAÇÃO` (10), `Null` (6), `NÃO INFORMADO` (5), `n/a` (5) |
| `compras.modo_disputa` | 2.042 | 0 | 967 | `Não se aplica` (904), `N/A` (11), `Null` (9), `NÃO INFORMADO` (9), `n/a` (9), `0` (7), `SEM INFORMAÇÃO` (6), `-` (6), `NULL` (6) |
| `itens.categoria_item` | 7.077 | 0 | 7.077 | `Não se aplica` (7077) |
| `itens.unidade_medida` | 7.077 | 9 | 0 | - |
| `itens.situacao_item` | 7.077 | 0 | 220 | `n/a` (42), `SEM INFORMAÇÃO` (31), `-` (29), `0` (25), `NULL` (25), `N/A` (25), `NÃO INFORMADO` (24), `Null` (19) |
| `itens.catalogo_codigo_item` | 7.077 | 7.068 | 0 | - |
| `itens.criterio_julgamento` | 7.077 | 0 | 1.883 | `Não se aplica` (1883) |
| `resultados.ordem_classificacao_srp` | 15.896 | 11.976 | 0 | - |
| `resultados.porte` | 15.896 | 0 | 4.893 | `Não Informado` (4415), `N/A` (72), `NULL` (64), `n/a` (60), `SEM INFORMAÇÃO` (60), `0` (57), `NÃO INFORMADO` (53), `-` (52), `Null` (51), `Não se aplica` (9) |

O que esses números mostram:

- **"Não se aplica" e "Não Informado" contam como vazio.** O enunciado (desafio 4) coloca "NÃO SE APLICA" e "NÃO INFORMADO" na lista de vazios disfarçados, e a lista do `src/limpeza.py` segue a mesma regra. Por isso `categoria_item` fica 100% vazia. O enunciado já avisa que essa coluna "não ajuda".
- **`porte`:** os 4.893 vazios (quase todos "Não Informado", de pessoas físicas) vão virar **"Não informado"** no `porte_descricao`. É o mesmo resultado que a categoria original já dava.
- **`ordem_classificacao_srp`:** os 11.976 vazios valem **1** (1º colocado), pela regra 2. Por isso o desempate pelo `sequencial_resultado` decide o vencedor na maior parte dos itens.
- Os vazios de verdade em `unidade_medida` (9) e `catalogo_codigo_item` (7.068) não afetam a fato.

### Acentos quebrados e caracteres invisíveis

| Coluna | Total | Acento quebrado | NBSP (`\xa0`) | TAB | Quebra de linha dentro do texto | Largura zero (`​`…) | Espaços sobrando |
|---|---|---|---|---|---|---|---|
| `compras.processo` | 2.042 | 0 | 0 | 1 | 0 | 0 | 47 |
| `compras.objeto_compra` | 2.042 | 43 | 64 | 5 | 128 | 1 | 415 |
| `compras.cnpj_orgao` | 2.042 | 0 | 131 | 0 | 0 | 0 | 131 |
| `compras.razao_social_orgao` | 2.042 | 0 | 53 | 0 | 0 | 0 | 58 |
| `compras.municipio` | 2.042 | 28 | 55 | 0 | 0 | 0 | 55 |
| `compras.nome_unidade` | 2.042 | 14 | 49 | 0 | 0 | 0 | 63 |
| `itens.descricao` | 7.077 | 116 | 196 | 40 | 196 | 0 | 448 |
| `itens.unidade_medida` | 7.077 | 0 | 0 | 0 | 0 | 0 | 935 |
| `resultados.ni_fornecedor` | 15.896 | 0 | 990 | 0 | 0 | 0 | 990 |
| `resultados.nome_fornecedor` | 15.896 | 1 | 424 | 0 | 0 | 0 | 501 |

Exemplos de acento quebrado e como ficam depois de consertados:

| Coluna | Como está | Depois de consertar |
|---|---|---|
| `compras.objeto_compra` | `ContrataÃ§Ã£o` | `Contratação` |
| `compras.municipio` | `SÃ£o` | `São` |
| `compras.nome_unidade` | `GOIÃS` | `GOIÁS` |
| `itens.descricao` | `DESMONTÃVEL` | `DESMONTÁVEL` |
| `resultados.nome_fornecedor` | `AÃ©ronav` | `Aéronav` |

O que esses números mostram:

- **Acento quebrado (202 registros em 5 colunas):** o texto foi gravado num padrão de letras (UTF-8) e lido em outro (Latin-1), então `ç` virou `Ã§` e `ã` virou `Ã£`. Dá para desfazer sem perder nada.
- **Caracteres invisíveis:** o NBSP é um espaço que não aparece diferente na tela, mas faz `"COMANDO DA AERONAUTICA"` e `"COMANDO DA AERONAUTICA\xa0"` virarem nomes diferentes. Também há TAB, quebras de linha dentro do texto e 1 caractere de largura zero.
- **Espaços sobrando:** espaços nas pontas ou repetidos no meio, como em `"  COMANDO  DA AERONAUTICA"`.

### Mesmo órgão ou fornecedor escrito de jeitos diferentes

Para cada documento (CNPJ/CPF já limpo, como no item 1.1), foram contadas as grafias do nome **como vieram** e **depois de padronizar**. Padronizar quer dizer consertar o acento, tirar os invisíveis e os espaços sobrando, colocar em MAIÚSCULAS e pôr espaço dos dois lados do hífen, como faz o `padronizar_nome` do `src/limpeza.py`.

| Caso | Documentos distintos | Com mais de 1 grafia (como veio) | Com mais de 1 grafia (depois de padronizar) | Nomes distintos (como veio) | Nomes distintos (depois de padronizar) |
|---|---|---|---|---|---|
| Órgão (`razao_social_orgao` por CNPJ) | 370 | 67 | 0 | 440 | 352 |
| Unidade (`nome_unidade` por CNPJ) | 370 | 100 | 62 | 1.046 | 941 |
| Fornecedor (`nome_fornecedor` por CNPJ/CPF) | 10.299 | 490 | 16 | 10.707 | 10.165 |

O que esses números mostram:

- **Órgão:** a padronização resolve tudo. Exemplos: `COMANDO DA AERONAUTICA`, `Comando Da Aeronautica`, `  COMANDO  DA AERONAUTICA\xa0` e `comando da aeronautica` viram um nome só, e cada CNPJ fica com 1 nome.
- **Fornecedor:** sobram 16 documentos com mais de um nome, mas são **nomes diferentes de verdade**, e não erros de digitação. Exemplos: `ALELO S.A.` e `ALELO INSTITUICAO DE PAGAMENTO SA`, ou `ATIVE COMUNICACAO` e `ATIVE COMUNICAÇÃO` (com e sem acento). A dimensão guarda um nome só por documento, então isso não duplica fornecedores.
- **Unidade:** os 62 CNPJs que continuam com vários nomes são **unidades diferentes** do mesmo CNPJ (ex.: `BANCO CENTRAL DO BRASIL - BRASÍLIA` e `BANCO CENTRAL DO BRASIL - SALVADOR`). Não é erro de digitação, e `nome_unidade` não vai para a dimensão.
- **O contrário também acontece:** 5 órgãos têm **o mesmo nome com vários CNPJ** (unidades). O maior é o `DNIT - DEPARTAMENTO NACIONAL DE INFRAEST DE TRANSPORTES`, com 12 CNPJ, seguido do `COMANDO DA AERONAUTICA` (4) e do `COMANDO DA MARINHA` (3). Por isso, no ranking da pergunta 4, o enunciado manda agrupar pelo **nome padronizado** e não pelo CNPJ.
