# Esteira analítica de compras públicas (PNCP 2025) para a Controladoria

## Auditoria dos dados

Antes de corrigir qualquer coisa, os 3 arquivos brutos de `data/raw/` foram auditados, ou seja, cada problema foi **contado**: quantos registros ele afeta.
As contagens são feitas pelo script [`src/auditoria.py`](src/auditoria.py), que lê os arquivos sem mudar nada e mostra as tabelas abaixo:

```bash
python -m src.auditoria
```

> Um mesmo registro pode ter mais de um problema (por exemplo, `R$ 1.234,56` tem `R$` **e** milhar no padrão brasileiro). Por isso as colunas de uma tabela não devem ser somadas.

### Resumo dos problemas

Lista de todos os problemas encontrados, com quantos registros cada um afeta. A coluna "Desafio" segue a numeração da seção 4.2 do enunciado: 1 documentos, 2 dinheiro, 3 datas, 4 vazios disfarçados, 5 texto. Os detalhes de cada problema estão nas seções abaixo.

| Desafio | Problema | Onde aparece | Registros afetados | Tratado em |
|---|---|---|---|---|
| 1 | CNPJ/CPF com máscara (pontos, barra, traço) | `cnpj_orgao`, `ni_fornecedor` | 1.809 | Sprint 2 |
| 1 | CNPJ/CPF com espaços sobrando | `cnpj_orgao`, `ni_fornecedor` | 1.121 | Sprint 2 |
| 1 | CNPJ/CPF com zeros perdidos no começo | `cnpj_orgao`, `ni_fornecedor` | 430 | Sprint 2 |
| 2 | Dinheiro e quantidade com `R$` | 8 colunas de valor e quantidade | 12.055 | Sprint 2 |
| 2 | Dinheiro e quantidade com espaços sobrando (inclui NBSP) | 8 colunas de valor e quantidade | 5.976 | Sprint 2 |
| 2 | Número fora do padrão ponto decimal (vírgula decimal, BR com milhar, US com milhar, milhar repetido) | 8 colunas de valor e quantidade | 16.706 | Sprint 2 |
| 2 | Número ambíguo (`1.500`, vale 1,5 pela regra) | valores unitários e totais | 137 | Sprint 2 |
| 2 | Valor negativo (entre parênteses ou com sinal) | 8 colunas de valor e quantidade | 0 | não ocorre |
| 3 | Data fora do formato ISO (`aaaa-mm-dd`) | `data_publicacao`, `data_resultado` | 6.318 | Sprint 2 |
| 3 | Homologação antes da publicação do edital | `data_resultado` × `data_publicacao` | 234 | Sprint 3 (regra 7) |
| 3 | Ano absurdo (2035 a 9999, Credenciamento) | `data_encerramento_proposta` | 65 | não vai para a fato |
| 4 | Vazio disfarçado (N/A, NULL, -, 0, Não se aplica, Não Informado…) | 6 colunas de texto | 15.117 | Sprint 2 |
| 5 | Acento quebrado (`Ã§`, `Ã£`) | 5 colunas de texto | 202 | Sprint 2 |
| 5 | Caractere invisível (NBSP, TAB, quebra de linha, largura zero) | colunas de texto | 1.164 | Sprint 2 |
| 5 | Órgão com o nome escrito de jeitos diferentes (CNPJ) | `razao_social_orgao` | 67 | Sprint 2 |
| 5 | Fornecedor com o nome escrito de jeitos diferentes (CNPJ/CPF) | `nome_fornecedor` | 490 | Sprint 2 e 3 |
| 5 | Mesmo nome de órgão com vários CNPJ (unidades) | `razao_social_orgao` | 5 | Sprint 5 (agrupar pelo nome) |

Como ler a tabela:

- **Registros afetados** soma todas as colunas onde o problema aparece. Se um registro tem o mesmo problema em 2 colunas, ele conta 2 vezes. Nas três últimas linhas, a contagem é de **documentos** (CNPJ/CPF), e não de registros.
- **Sprint 2** é onde o `src/limpeza.py` corrige o problema. **Sprint 3** é onde as regras de negócio decidem o que fazer com o registro.
- **Não ocorre / não vai para a fato:** o problema foi procurado e não existe, ou fica numa coluna que não é usada nas tabelas finais.

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

## Itens rejeitados

Depois de escolher o vencedor de cada item, sobram **6.225 itens com resultado**. Os 852 itens sem resultado já ficaram de fora antes e não contam como rejeitados. Antes de rejeitar, o valor total de cada item é calculado: valor unitário × quantidade homologada. Se a quantidade homologada vier vazia ou zero, usa-se a quantidade do item, o que aconteceu em 8 itens.

Depois, os itens com dados impossíveis são **rejeitados**: não entram na fato nem no banco. Isso é feito pela etapa 5 do [`src/montar_tabelas.py`](src/montar_tabelas.py), seguindo a regra 4 do enunciado. Foram **99 itens rejeitados** (prova real: 99), e sobraram **6.126 itens na fato**.

Quando um item cai em mais de um caso, ele é contado só no **primeiro motivo**, na ordem do enunciado:

| Ordem | Motivo | Itens (primeiro motivo) | Itens (qualquer motivo) |
|---|---|---|---|
| 1 | Quantidade vazia ou ≤ 0 | 1 | 1 |
| 2 | Valor unitário estimado vazio ou ≤ 0 | 23 | 23 |
| 3 | Valor unitário homologado vazio ou ≤ 0 | 6 | 6 |
| 4 | Orçamento sigiloso | 0 | 0 |
| 5 | Valor total estimado menor que R$ 1 | 59 | 85 |
| 6 | Valor total homologado mais de 1.000× o estimado | 7 | 60 |
| 7 | Valor total acima de R$ 1 trilhão | 3 | 3 |
| | **Total** | **99** | |

Como ler a tabela:

- **Primeiro motivo:** cada item é contado uma vez só, por isso esta coluna soma 99.
- **Qualquer motivo:** um mesmo item pode cair em vários casos, por isso esta coluna não deve ser somada. Exemplo: um item com estimado de R$ 0,50 e homologado de R$ 900 cai nos casos 5 e 6.
- **Valor acima de R$ 1 trilhão:** um número desse tamanho não cabe na coluna de dinheiro do banco. O banco seria a segunda barreira, mas o item já é rejeitado aqui.

## Perfil do gasto (Bens, Serviços ou Obras)

Cada item da fato foi classificado em **Bens**, **Serviços** ou **Obras e engenharia**, seguindo a regra 8 do enunciado. A classificação é feita na etapa 8 do [`src/montar_tabelas.py`](src/montar_tabelas.py), assim:

1. Primeiro, procura-se uma **palavra de obra** na descrição do item junto com o objeto da compra. Se ela aparecer, o item é **Obras e engenharia**, mesmo que seja Material ou Serviço.
2. Nos demais itens, usa-se a coluna `material_ou_servico`: **Material** vira **Bens** e **Serviço** vira **Serviços**. A coluna `categoria_item` não foi usada porque vem toda como "Não se aplica".

### Palavras de obra escolhidas

Foram usadas as 4 palavras da referência do enunciado, que já vêm no kit. Assim o resultado bate com a prova real.

| Palavra procurada | Itens em que aparece |
|---|---|
| OBRA | 344 |
| OBRAS | 376 |
| CONSTRUÇÃO (ou CONSTRUCAO, sem acento) | 352 |
| REFORMA | 222 |
| ENGENHARIA | 393 |

- A busca é feita pela **palavra inteira**, e não por um pedaço dela. Por isso "cobrança" e "dobradiça" **não** viram obra.
- Um item pode ter mais de uma dessas palavras, por isso a tabela acima não deve ser somada. No total, **967 itens** viraram Obras e engenharia: 803 eram Serviço e 164 eram Material.

### Resultado

| Perfil | Itens | Volume homologado | % do volume |
|---|---|---|---|
| Bens | 3.310 | R$ 211.185.187,86 | 2,6% |
| Serviços | 1.849 | R$ 2.940.950.885,18 | 36,6% |
| Obras e engenharia | 967 | R$ 4.892.362.732,70 | 60,8% |
| **Total** | **6.126** | **R$ 8.044.498.805,74** | **100%** |

Os percentuais batem com a prova real (Obras 60,8% · Serviços 36,6% · Bens 2,6%). Bens são mais da metade dos itens, mas quase todo o dinheiro vai para obras e serviços.

## Respostas das perguntas da Controladoria

As consultas estão em [`sql/02_perguntas.sql`](sql/02_perguntas.sql) e rodam no banco `pncp_controladoria`, depois da carga (`python -m src.carregar`). Os percentuais são sempre **soma ÷ soma**, e nunca uma média de percentuais. A economia conta só os **itens comparáveis** (regra 6).

### Pergunta 1 – Economia global do Poder Público

| Indicador | Resultado |
|---|---|
| Itens comparáveis | 5.457 de 6.126 |
| Valor estimado dos comparáveis | R$ 6.867.663.469,91 |
| **Economia (estimado − homologado)** | **R$ 992.861.686,95** |
| **Economia %** | **14,46%** |
| Itens homologados acima do estimado (sobrepreço) | 27 |
| Quanto o sobrepreço custou | R$ 44.440,34 |

Onde se concentram os 27 itens com sobrepreço:

| Agrupado por | Onde se concentra | Itens | Valor |
|---|---|---|---|
| Modalidade | Pregão - Eletrônico | 25 | R$ 38.551,51 |
| | Concorrência - Eletrônica | 1 | R$ 5.126,83 |
| | Dispensa | 1 | R$ 762,00 |
| Perfil do gasto | Bens | 25 | R$ 39.299,94 |
| | Serviços | 2 | R$ 5.140,40 |
| Região | Sudeste | 24 | R$ 38.537,94 |
| | Nordeste | 2 | R$ 5.888,83 |
| | Sul | 1 | R$ 13,57 |

**Conclusão:** o governo pagou 14,46% a menos do que estimou nos itens que dá para comparar, uma economia de quase R$ 1 bilhão. O sobrepreço é raro (27 itens) e pequeno (R$ 44 mil, menos de 0,005% da economia). Ele se concentra em **bens comprados por Pregão Eletrônico no Sudeste**. Obras, Centro-Oeste e Norte não tiveram nenhum item com sobrepreço.

### Pergunta 2 – Concentração de fornecedores e ME/EPP

| Indicador | Resultado |
|---|---|
| Itens ganhos por ME/EPP | 3.853 de 6.126 (62,90%) |
| Volume ganho por ME/EPP | R$ 1.603.610.879,06 (19,93% do volume) |
| Volume dos 10 maiores fornecedores | R$ 3.332.484.029,86 (**41,43%** do volume) |

Os 10 maiores fornecedores em volume (fornecedor = CNPJ/CPF, então filiais contam separado):

| # | Fornecedor | Porte | Itens | Volume | % do volume |
|---|---|---|---|---|---|
| 1 | NOW SEGUROS SA | Demais | 1 | R$ 1.060.000.000,00 | 13,18% |
| 2 | CONSTRUTORA CIDADE LIMITADA | Demais | 1 | R$ 524.935.394,97 | 6,53% |
| 3 | BANCO BRADESCO S.A. | Demais | 1 | R$ 379.194.320,07 | 4,71% |
| 4 | CONSTRUTORA NORTE BRASIL LTDA. | Microempresa | 1 | R$ 335.401.470,80 | 4,17% |
| 5 | LCM CONSTRUCAO E COMERCIO S.A | Demais | 1 | R$ 228.885.493,53 | 2,85% |
| 6 | CONSTRUTORA OTIMA LTDA | Demais | 1 | R$ 192.344.816,46 | 2,39% |
| 7 | CONPATE ENGENHARIA LTDA | Demais | 1 | R$ 166.644.303,41 | 2,07% |
| 8 | INDIGO HIVE CONSULTORIA EM TECNOLOGIA DA INFORMACAO S.A. | Demais | 1 | R$ 160.000.000,00 | 1,99% |
| 9 | CONSTRUTORA HIDROS LTDA | Demais | 1 | R$ 159.193.730,62 | 1,98% |
| 10 | ARTELESTE CONSTRUCOES LIMITADA | Demais | 1 | R$ 125.884.500,00 | 1,56% |

**Conclusão:** as micro e pequenas empresas ganham a maioria dos itens (62,90%), mas ficam com só 19,93% do dinheiro, porque vencem compras menores. Já os 10 maiores fornecedores, de um total de 2.652, ficam com 41,43% de todo o volume. Cada um deles ganhou **um único item**: a concentração vem de poucas compras muito grandes, e não de fornecedores que vencem muitas vezes. Desses 10 itens, 7 são de Obras e engenharia e 3 de Serviços, entre eles o maior de todos (NOW SEGUROS SA, R$ 1,06 bilhão).
