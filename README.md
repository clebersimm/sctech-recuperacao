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

## Conferência com a prova real

Todos os números do anexo 8 do enunciado (prova real) foram comparados com o resultado do projeto, e **todos bateram**.

### Números que saem das consultas de `sql/02_perguntas.sql`

Para conferir no pgAdmin, rode a consulta indicada na coluna "Consulta" e compare com o valor do anexo.

| Conferência do anexo 8 | Anexo 8 | Resultado | Consulta | Confere |
|---|---|---|---|---|
| Itens na fato | 6.126 | 6.126 | 1.1 | ✔ |
| Itens na base comparável | 5.457 | 5.457 | 1.1 | ✔ |
| Estimado da base comparável | R$ 6.867.663.469,91 | R$ 6.867.663.469,91 | 1.1 | ✔ |
| Economia nominal | R$ 992.861.686,95 | R$ 992.861.686,95 | 1.1 | ✔ |
| Economia % | 14,46% | 14,46% | 1.1 | ✔ |
| Itens com sobrepreço | 27 | 27 | 1.1 | ✔ |
| Volume homologado total | R$ 8.044.498.805,74 | R$ 8.044.498.805,74 | 2.1 | ✔ |
| Itens com fornecedor ME/EPP | 3.853 | 3.853 | 2.1 | ✔ |
| Volume com ME/EPP | R$ 1.603.610.879,06 (19,93%) | R$ 1.603.610.879,06 (19,93%) | 2.1 | ✔ |
| Itens de contratação direta | 1.890 | 1.890 | 3.1 | ✔ |
| Volume de contratação direta | R$ 253.252.588,63 (3,15%) | R$ 253.252.588,63 (3,15%) | 3.1 | ✔ |
| Itens por grupo de modalidade | Pregão 3.051 · Contratação direta 1.890 · Credenciamento 601 · Concorrência 584 | iguais | 3.3 | ✔ |
| Itens com ciclo | 5.896 | 5.896 | 4.3 | ✔ |
| Ciclo médio / máximo | 48,1 / 611 dias | 48,1 / 611 dias | 4.3 | ✔ |
| Itens com ciclo longo | 830 (14,1%) | 830 (14,08%) | 4.3 | ✔ |
| Perfil do gasto (% do volume) | Obras 60,8% · Serviços 36,6% · Bens 2,6% | 60,82% · 36,56% · 2,63% | 6.1 | ✔ |
| Perfil do gasto (itens) | 967 · 1.849 · 3.310 | iguais | 6.1 | ✔ |

O anexo mostra alguns percentuais com 1 casa decimal (14,1 e 60,8), e as consultas mostram 2 casas (14,08 e 60,82). É o mesmo valor arredondado.

### Números conferidos direto no banco

São números do anexo 8 que não fazem parte das 6 perguntas:

| Conferência do anexo 8 | Anexo 8 | No banco | Confere |
|---|---|---|---|
| Contratações distintas na fato | 1.962 | 1.962 | ✔ |
| Fornecedores distintos | 2.652 | 2.652 | ✔ |
| Unidades compradoras (CNPJ de órgão distintos) | 363 | 363 | ✔ |
| Soma do estimado de todos os itens | R$ 32.629.639.732,13 | R$ 32.629.639.732,13 | ✔ |
| Itens sem ciclo | 230 | 230 | ✔ |
| Fornecedores por porte | Microempresa 1.489 · Demais 908 · Não informado 250 · Empresa de Pequeno Porte 5 | iguais | ✔ |
| Contratação direta por modalidade | Dispensa 1.387 · Inexigibilidade 503 | iguais | ✔ |

### Números conferidos na montagem das tabelas

Estes números não ficam guardados no banco. São conferidos pelo `python -m src.montar_tabelas`, que mostra cada um na tela:

| Conferência do anexo 8 | Anexo 8 | Resultado | Confere |
|---|---|---|---|
| Linhas de compras.csv / itens.csv / resultados.csv | 2.042 / 7.077 / 15.896 | 2.042 / 7.077 / 15.896 | ✔ |
| Itens sem resultado homologado | 852 | 852 (6.225 itens com resultado) | ✔ |
| Itens rejeitados | 99 | 99 | ✔ |

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

### Pergunta 3 – Eficácia por modalidade e contratação direta

| Indicador | Resultado |
|---|---|
| Itens contratados sem licitação (Dispensa e Inexigibilidade) | 1.890 |
| Volume contratado sem licitação | R$ 253.252.588,63 (**3,15%** do volume) |

Ciclo da contratação direta comparado ao das demais modalidades (o % de ciclo longo é calculado sobre os itens **com** ciclo):

| Tipo | Itens com ciclo | Ciclo médio | % ciclo longo |
|---|---|---|---|
| Contratação direta | 1.661 | 9,1 dias | 0,48% |
| Demais modalidades | 4.235 | 63,4 dias | 19,41% |

Comparação entre os grupos de modalidade:

| Grupo | Itens | Volume | % do volume | Economia % | Ciclo médio |
|---|---|---|---|---|---|
| Concorrência | 584 | R$ 5.145.245.880,16 | 63,96% | 13,67% | 101,2 dias |
| Credenciamento | 601 | R$ 2.141.301.557,16 | 26,62% | — | 62,7 dias |
| Pregão | 3.051 | R$ 504.698.779,79 | 6,27% | 23,93% | 56,3 dias |
| Contratação direta | 1.890 | R$ 253.252.588,63 | 3,15% | 8,04% | 9,1 dias |

No Credenciamento a economia % fica vazia (—), porque nenhum item dessa modalidade é comparável (regra 6). Isso é o esperado, e não um erro.

**Conclusão:** a contratação sem licitação é pequena em dinheiro (3,15% do volume) e muito mais rápida: 9,1 dias contra 63,4 dias das demais. Em troca, ela dá pouco desconto (8,04%). O **Pregão** tem o melhor desconto (23,93%) e é a modalidade com mais itens. A **Concorrência** concentra a maior parte do dinheiro (63,96%) e é a mais lenta, passando de 100 dias em média.

### Pergunta 4 – Tempo do ciclo de compras

No total, 5.896 itens têm ciclo (dias entre a publicação do edital e a homologação). A **duração média é de 48,1 dias**, o máximo é de 611 dias, e 830 itens (14,08%) passaram de 90 dias.

Os 10 órgãos com maior proporção de ciclo longo. Os órgãos foram agrupados pelo nome padronizado e entram só os que têm 5 ou mais itens com ciclo, num total de 142 órgãos:

| # | Órgão | Itens com ciclo | Com ciclo longo | % ciclo longo | Ciclo médio |
|---|---|---|---|---|---|
| 1 | CONSELHO FEDERAL DE ENGENHARIA E AGRONOMIA | 20 | 20 | 100,00% | 223,0 dias |
| 2 | INSTITUTO FEDERAL DE EDUCACAO,CIENCIA E TECNOLOGIA DE RONDONIA | 9 | 9 | 100,00% | 125,0 dias |
| 3 | UNIVERSIDADE FEDERAL DE CAMPINA GRANDE | 16 | 14 | 87,50% | 266,3 dias |
| 4 | DNIT - DEPARTAMENTO NACIONAL DE INFRAEST DE TRANSPORTES | 62 | 52 | 83,87% | 156,2 dias |
| 5 | CONSELHO REGIONAL DE MEDICINA DO ESTADO DE MINAS GERAIS | 6 | 5 | 83,33% | 100,3 dias |
| 6 | UNIVERSIDADE FEDERAL DO ESTADO DO RIO DE JANEIRO | 26 | 20 | 76,92% | 135,4 dias |
| 7 | INSTITUTO FEDERAL DE EDUCACAO, CIENCIA E TECNOLOGIA DE SERGIPE | 31 | 21 | 67,74% | 74,9 dias |
| 8 | INSTITUTO FEDERAL DE EDUCACAO, CIENCIA E TECNOLOGIA DO PARANA | 30 | 20 | 66,67% | 107,8 dias |
| 9 | DEFENSORIA PUBLICA DA UNIAO | 11 | 7 | 63,64% | 100,0 dias |
| 10 | CONSELHO REGIONAL DE ENGENHARIA E AGRONOMIA DO RS | 38 | 24 | 63,16% | 80,5 dias |

Por modalidade:

| Modalidade | Itens com ciclo | Com ciclo longo | % ciclo longo | Ciclo médio |
|---|---|---|---|---|
| Concorrência - Presencial | 63 | 59 | 93,65% | 187,5 dias |
| Concorrência - Eletrônica | 520 | 167 | 32,12% | 90,7 dias |
| Credenciamento | 601 | 127 | 21,13% | 62,7 dias |
| Pregão - Eletrônico | 3.046 | 469 | 15,40% | 56,4 dias |
| Dispensa | 1.275 | 7 | 0,55% | 11,6 dias |
| Inexigibilidade | 386 | 1 | 0,26% | 0,6 dia |
| Pregão - Presencial | 5 | 0 | 0,00% | 22,2 dias |

**Conclusão:** a compra média leva 48,1 dias do edital à homologação, mas a modalidade muda muito esse tempo. A **Concorrência Presencial** é a mais lenta: 93,65% dos itens passam de 90 dias e a média é de 187,5 dias. Já a Dispensa e a Inexigibilidade quase nunca passam de 90 dias. Entre os órgãos, o **DNIT** chama atenção por juntar volume e demora: 52 dos seus 62 itens tiveram ciclo longo. Nos órgãos com poucos itens (por exemplo, 6 ou 9), uma única compra demorada já muda bastante o percentual.

### Pergunta 5 – Distribuição regional

O número de itens aparece ao lado de cada percentual. Numa UF com poucos itens, uma única compra muda bastante o resultado.

Por região:

| Região | Itens | Volume | % do volume | Itens comparáveis | Economia % | Itens de contratação direta | % do volume em contratação direta |
|---|---|---|---|---|---|---|---|
| Centro-Oeste | 940 | R$ 3.559.879.991,73 | 44,25% | 757 | 17,02% | 235 | 0,48% |
| Nordeste | 1.155 | R$ 1.850.420.285,02 | 23,00% | 1.006 | 14,18% | 318 | 3,95% |
| Sudeste | 2.072 | R$ 1.083.309.811,49 | 13,47% | 1.925 | 11,62% | 764 | 11,85% |
| Sul | 1.325 | R$ 1.021.624.955,41 | 12,70% | 1.203 | 7,96% | 345 | 3,03% |
| Norte | 634 | R$ 529.263.762,09 | 6,58% | 566 | 21,43% | 228 | 0,68% |

Por UF (as 27, da maior para a menor despesa):

| UF | Região | Itens | Volume | % do volume | Itens comparáveis | Economia % | Itens de contratação direta | % do volume em contratação direta |
|---|---|---|---|---|---|---|---|---|
| DF | Centro-Oeste | 585 | R$ 3.135.638.456,35 | 38,98% | 489 | 15,90% | 136 | 0,32% |
| RS | Sul | 845 | R$ 820.584.056,64 | 10,20% | 798 | 7,18% | 213 | 0,51% |
| RJ | Sudeste | 933 | R$ 461.925.602,27 | 5,74% | 891 | 11,57% | 292 | 6,93% |
| PI | Nordeste | 70 | R$ 408.389.525,89 | 5,08% | 62 | 5,98% | 27 | 3,82% |
| SP | Sudeste | 517 | R$ 393.783.392,48 | 4,90% | 465 | 9,22% | 229 | 23,64% |
| PE | Nordeste | 170 | R$ 277.610.822,64 | 3,45% | 145 | 18,75% | 65 | 1,51% |
| CE | Nordeste | 160 | R$ 273.063.635,47 | 3,39% | 127 | 7,88% | 76 | 1,89% |
| BA | Nordeste | 222 | R$ 243.705.954,94 | 3,03% | 209 | 25,01% | 56 | 1,36% |
| MT | Centro-Oeste | 77 | R$ 240.920.586,26 | 2,99% | 50 | 25,84% | 16 | 0,08% |
| AC | Norte | 40 | R$ 207.336.488,34 | 2,58% | 39 | 26,71% | 11 | 0,25% |
| AL | Nordeste | 51 | R$ 200.475.716,34 | 2,49% | 28 | 16,43% | 1 | 0,01% |
| MG | Sudeste | 496 | R$ 198.701.363,92 | 2,47% | 450 | 14,34% | 154 | 1,27% |
| RN | Nordeste | 225 | R$ 193.722.442,76 | 2,41% | 196 | 16,42% | 28 | 0,94% |
| MS | Centro-Oeste | 170 | R$ 151.844.486,73 | 1,89% | 126 | 12,13% | 53 | 2,10% |
| AM | Norte | 208 | R$ 150.043.153,77 | 1,87% | 202 | 14,92% | 60 | 1,05% |
| PR | Sul | 327 | R$ 124.166.989,28 | 1,54% | 277 | 12,17% | 91 | 20,04% |
| MA | Nordeste | 59 | R$ 107.784.353,34 | 1,34% | 56 | 22,17% | 29 | 0,27% |
| PA | Norte | 192 | R$ 82.949.670,30 | 1,03% | 169 | 19,11% | 78 | 1,15% |
| PB | Nordeste | 113 | R$ 78.243.676,65 | 0,97% | 104 | 16,88% | 15 | 1,90% |
| SC | Sul | 153 | R$ 76.873.909,49 | 0,96% | 128 | 11,59% | 41 | 2,50% |
| SE | Nordeste | 85 | R$ 67.424.156,99 | 0,84% | 79 | 6,47% | 21 | 61,15% |
| RR | Norte | 26 | R$ 47.718.188,56 | 0,59% | 22 | 19,81% | 15 | 0,06% |
| GO | Centro-Oeste | 108 | R$ 31.476.462,39 | 0,39% | 92 | 12,64% | 30 | 12,12% |
| ES | Sudeste | 126 | R$ 28.899.452,82 | 0,36% | 119 | 22,64% | 89 | 2,49% |
| RO | Norte | 113 | R$ 25.255.010,96 | 0,31% | 88 | 21,36% | 27 | 0,38% |
| AP | Norte | 31 | R$ 8.075.852,27 | 0,10% | 26 | 22,65% | 23 | 1,26% |
| TO | Norte | 24 | R$ 7.885.397,89 | 0,10% | 20 | 17,80% | 14 | 4,17% |

**Conclusão:**

- **Maiores despesas:** o **Centro-Oeste** concentra 44,25% do volume, quase todo no **DF** (38,98%). Depois vêm o RS (10,20%) e o RJ (5,74%).
- **Melhores descontos:** entre as regiões, o **Norte** (21,43%). Entre as UFs, o AC (26,71%), o MT (25,84%) e a BA (25,01%). O desconto do AC e do MT vem de poucos itens comparáveis (39 e 50), então é um resultado mais frágil que o da BA (209). O **Sul** tem o menor desconto entre as regiões (7,96%).
- **Contratação direta:** entre as regiões, o **Sudeste** tem o maior volume relativo (11,85%). Entre as UFs, **SE** se destaca muito: 61,15% do seu volume é contratado sem licitação. Depois vêm SP (23,64%) e PR (20,04%).

### Pergunta 6 – Perfil dos gastos

| Perfil | Itens | Volume | % do volume |
|---|---|---|---|
| Obras e engenharia | 967 | R$ 4.892.362.732,70 | 60,82% |
| Serviços | 1.849 | R$ 2.940.950.885,18 | 36,56% |
| Bens | 3.310 | R$ 211.185.187,86 | 2,63% |

**Conclusão:** a maior parte do dinheiro vai para **obras e engenharia** (60,82%), seguida de **serviços** (36,56%). **Bens** são a maioria dos itens (3.310), mas ficam com só 2,63% do volume. São muitas compras pequenas, enquanto as obras são poucas compras de valor alto.
