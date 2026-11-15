# Conhecendo os dados (Sprint 0 – 0.3)

Primeiro contato com os 3 arquivos brutos da pasta `data/raw/`, **antes de qualquer limpeza**.
O objetivo aqui é **ver** o que existe em cada arquivo. As contagens são uma **prévia**: a contagem oficial de cada problema é feita na Sprint 1 (auditoria) e registrada no README.

**Como foi feito:** os arquivos foram lidos com pandas, todas as colunas como texto (`dtype=str`, como pede o enunciado), sem converter nada. Cada coluna foi verificada quanto a preenchimento, valores distintos, vazios disfarçados, acentos quebrados e caracteres invisíveis. Os formatos de dinheiro, data e CNPJ/CPF foram classificados por expressões regulares.

---

## 1. Visão geral dos arquivos

Os 3 arquivos são CSV separados por vírgula, codificados em UTF-8 e com cabeçalho. Eles se ligam pelo `numero_controle_pncp` (e pelo `numero_item`):

```
compras (1) ──< itens (N) ──< resultados (N)
   numero_controle_pncp   + numero_item
```

| Arquivo | O que é cada linha | Registros | Linhas físicas | Colunas | Confere com a prova real? |
|---|---|---|---|---|---|
| `compras.csv` | uma contratação (o "edital") | **2.042** | 2.282 | 25 | ✅ 2.042 |
| `itens.csv` | um item licitado | **7.077** | 8.042 | 14 | ✅ 7.077 |
| `resultados.csv` | um fornecedor classificado em um item | **15.896** | 15.896 | 13 | ✅ 15.896 |

> **Atenção:** contar linhas com `wc -l` dá um número errado. Alguns textos têm quebra de linha dentro das aspas: 128 registros de `objeto_compra` e 196 de `descricao`. Por isso, conte sempre os registros lidos pelo pandas.

### Integridade das ligações

| Verificação | Resultado |
|---|---|
| `numero_controle_pncp` repetido em `compras.csv` | 0, a chave é única |
| (`numero_controle_pncp`, `numero_item`) repetido em `itens.csv` | 0, a chave é única |
| Item sem contratação correspondente | 0 |
| Resultado sem item correspondente | 0 |
| Contratação sem nenhum item | 0 |
| Itens por contratação | de 1 a 20 (mediana 1) |
| Resultados por item | de 1 a 1.773 (mediana 1). Os itens de SRP têm muitos classificados |
| Itens com `tem_resultado = True` | 6.225, e todos têm pelo menos 1 resultado não cancelado |
| Itens com `tem_resultado = False` | **852**, o mesmo número da prova real para itens sem resultado |

---

## 2. Dicionário das colunas

As colunas "Preench." e "Distintos" foram contadas sobre o arquivo bruto. Um vazio disfarçado, como "N/A", conta como preenchido, porque é texto.

### 2.1 `compras.csv`: uma linha por contratação

| Coluna | Significado | Preench. | Distintos | O que se observou |
|---|---|---|---|---|
| `numero_controle_pncp` | Identificador da contratação (chave) | 2.042 | 2.042 | Formato `CNPJ-1-SEQUENCIAL/ANO` |
| `ano_compra` | Ano do número da compra | 2.042 | 5 | 2022 a 2026. Não serve como data: o que vale é `data_publicacao` |
| `sequencial_compra` | Sequencial da compra no órgão | 2.042 | 1.140 | Número |
| `numero_compra` | Número dado pelo órgão | 2.042 | 570 | Texto livre (`90037`, `PE 009/2024`) |
| `processo` | Número do processo administrativo | 2.042 | 1.886 | **Vazios disfarçados**: N/A, NULL, `-`, `0`, SEM INFORMAÇÃO (72 ao todo) |
| `objeto_compra` | Descrição do que se compra | 2.042 | 1.980 | **43 com acento quebrado**, 128 com quebra de linha, NBSP e TAB |
| `srp` | Sistema de Registro de Preços | 2.042 | 2 | True 201 / False 1.841 |
| `cnpj_orgao` | CNPJ da unidade compradora | 2.042 | 539 | **Sujo**: com máscara, com espaços e com zeros perdidos (ver seção 3.3) |
| `razao_social_orgao` | Nome do órgão | 2.042 | 440 | **Mesmo CNPJ com várias grafias** (maiúsculas, espaços duplos, NBSP) |
| `poder_id` | E/L/J/N | 2.042 | 3 | E 1.873 · J 151 · L 18 (nenhum N) |
| `esfera_id` | F = Federal | 2.042 | 1 | Todos F |
| `uf_sigla` | UF da unidade | 2.042 | 27 | As 27 UFs, limpas |
| `uf_nome` | Nome da UF | 2.042 | 27 | Limpo, 1 nome por sigla |
| `municipio` | Município | 2.042 | 264 | **28 com acento quebrado** (`SÃ£o Carlos`) |
| `cod_ibge` | Código IBGE do município | 2.042 | 202 | Número |
| `nome_unidade` | Nome da unidade compradora | 2.042 | 1.046 | **14 com acento quebrado** (`GOIÃS`) |
| `modalidade_id` | Código da modalidade | 2.042 | 7 | 4, 5, 6, 7, 8, 9, 12. Cada id tem um único nome ✅ |
| `modalidade_nome` | Nome da modalidade | 2.042 | 7 | Igual à tabela 7.5 do enunciado |
| `modo_disputa` | Modo de disputa | 2.042 | 14 | **Vazios disfarçados**: N/A, n/a, NULL, Null, `-`, `0`, SEM INFORMAÇÃO, NÃO INFORMADO |
| `situacao_compra` | Situação da contratação | 2.042 | 4 | Divulgada 1.995 · Anulada 24 · Revogada 15 · Suspensa 8 |
| `valor_total_estimado` | Total estimado da contratação | 2.042 | 1.817 | **Dinheiro misturado** (seção 3.1). Não vai para a fato: o grão é o item |
| `valor_total_homologado` | Total homologado da contratação | 2.042 | 1.896 | Idem |
| `data_publicacao` | Publicação do edital | 2.042 | 1.846 | **7 formatos de data** (seção 3.2), de 02/01/2025 a 31/12/2025 |
| `data_abertura_proposta` | Início das propostas | 1.425 | 927 | 617 vazias, 7 formatos |
| `data_encerramento_proposta` | Fim das propostas | 1.425 | 1.167 | 617 vazias, 7 formatos |

### 2.2 `itens.csv`: uma linha por item licitado

| Coluna | Significado | Preench. | Distintos | O que se observou |
|---|---|---|---|---|
| `numero_controle_pncp` | Contratação do item | 7.077 | 2.042 | Todas as contratações têm item |
| `numero_item` | Número do item na contratação | 7.077 | 43 | Número |
| `descricao` | O que é o item | 7.077 | 3.633 | **116 com acento quebrado**, 196 com quebra de linha, NBSP e TAB |
| `material_ou_servico` | Material ou Serviço | 7.077 | 2 | Material 4.147 · Serviço 2.930 |
| `categoria_item` | Categoria | 7.077 | 1 | Sempre "Não se aplica" (não ajuda) |
| `quantidade` | Quantidade licitada | 7.077 | 1.115 | **Número com `R$`** em 1.148 linhas, além de formatos BR e US misturados |
| `unidade_medida` | Unidade | 7.068 | 359 | 9 vazias. Grafias variadas (`UNIDADE`, `Unidade`, `Unidade  `) e valores estranhos (`UNIDADE 0,00`, 53 linhas) |
| `valor_unitario_estimado` | Preço unitário esperado | 7.077 | 5.632 | **Dinheiro misturado** |
| `valor_total_estimado` | Total esperado | 7.077 | 6.123 | **Dinheiro misturado** |
| `sigiloso` | Orçamento sigiloso | 7.077 | 2 | True 54 / False 7.023 |
| `situacao_item` | Situação do item | 7.077 | 13 | Homologado 5.371 · Em andamento 758 · Fracassado 444 · Anulado/Revogado/Cancelado 149 · Deserto 135, além de **vazios disfarçados** (220) |
| `tem_resultado` | Tem fornecedor vencedor | 7.077 | 2 | True 6.225 / False 852 |
| `catalogo_codigo_item` | Código do catálogo oficial | 9 | 1 | Quase todo vazio (7.068) |
| `criterio_julgamento` | Critério de julgamento | 7.077 | 5 | Menor preço 4.850 · Não se aplica 1.883 · Maior desconto 208 · Técnica e preço 116 · Melhor técnica 20 |

### 2.3 `resultados.csv`: uma linha por fornecedor classificado em cada item

| Coluna | Significado | Preench. | Distintos | O que se observou |
|---|---|---|---|---|
| `numero_controle_pncp` | Contratação | 15.896 | 2.041 | Uma contratação não tem resultado |
| `numero_item` | Item | 15.896 | 41 | Número |
| `sequencial_resultado` | Sequência do resultado | 15.896 | 1.773 | Usado para desempatar o vencedor |
| `ordem_classificacao_srp` | Posição no ranking | 3.920 | 2 | `1.0` 3.919 · `4.0` 1 · **vazio 11.976** (vazio vale 1). Por isso o desempate pelo sequencial é decisivo |
| `ni_fornecedor` | CNPJ/CPF do fornecedor | 15.896 | 11.418 | **Muito sujo**: com máscara, com espaços e com zeros perdidos (seção 3.3) |
| `tipo_pessoa` | PJ, PF ou PE (estrangeiro) | 15.896 | 3 | PJ 11.344 · PF 4.531 · PE 21 |
| `nome_fornecedor` | Nome do fornecedor | 15.896 | 10.707 | **Mesmo documento com várias grafias**. 1 com acento quebrado (`AÃ©ronav Inc.`) |
| `porte` | Porte da empresa | 15.896 | 13 | ME 7.101 · Não Informado 4.415 · Demais 3.893 · EPP 9 · Não se aplica 9, além de **vazios disfarçados** (469) |
| `quantidade_homologada` | Quantidade comprada | 15.896 | 2.203 | **Número com `R$`** (2.561 linhas) e formatos misturados |
| `valor_unitario_homologado` | Preço unitário pago | 15.896 | 6.074 | **Dinheiro misturado** |
| `valor_total_homologado` | Total pago | 15.896 | 6.982 | **Dinheiro misturado** |
| `data_resultado` | Data da homologação | 15.896 | 2.318 | **7 formatos**, de 17/12/2024 a 05/10/2026 |
| `data_cancelamento` | Preenchida = resultado cancelado | 62 | 28 | Sempre em ISO com hora |

---

## 3. Formatos encontrados

### 3.1 Dinheiro e números

Os mesmos formatos aparecem em **todas** as colunas de dinheiro e quantidade, inclusive nas quantidades, que aparecem escritas com `R$`. Alguns valores vêm cercados de espaços comuns ou de NBSP (`\xa0`), como em `R$\xa03,00\xa0`.

| Formato | Exemplo real | `itens.valor_unitario_estimado` | `resultados.valor_total_homologado` |
|---|---|---|---|
| Ponto decimal | `6769268.15` | 5.475 | 12.064 |
| Com `R$` (no padrão BR) | `R$ 1.693,46` | 1.188 | 2.647 |
| BR com milhar | `20.307.804,45` | 111 | 544 |
| US com milhar | `37,942.21` | 113 | 517 |
| Só vírgula decimal | `10,81` | 190 | 124 |

- **Negativos entre parênteses ou com sinal de menos: nenhum encontrado** nos 3 arquivos. O planejamento da Sprint 1 previa esse caso, e a auditoria deve registrar que não ocorreu.
- **Casos ambíguos:** existem valores como `1.500` (23 em `valor_unitario_estimado`, 62 em `valor_unitario_homologado`) e `1,500` (3 e 2). O enunciado manda tratar **ponto ou vírgula sozinho como parte decimal**, então `1.500` vale 1,5.

### 3.2 Datas

As colunas de data de `compras.csv` e a `data_resultado` misturam **7 formatos**, em proporções parecidas:

| Formato | Exemplo real | `data_publicacao` | `data_resultado` |
|---|---|---|---|
| ISO com hora | `2025-01-06T11:51:06` | 1.319 | — |
| ISO | `2025-10-31` | — | 10.301 |
| BR com hora | `02/01/2025 09:03` | 126 | 934 |
| BR | `03/01/2025` | 117 | 929 |
| Com pontos | `02.01.2025` | 120 | 937 |
| Com traços | `02-01-2025` | 138 | 912 |
| Ano primeiro com barras | `2025/01/08` | 116 | 960 |
| Compacto | `20250103` | 106 | 923 |

- Todas as datas foram convertidas assumindo **dia antes do mês** (padrão brasileiro), sem nenhuma falha de conversão.
- `data_cancelamento` vem sempre em ISO com hora.
- 3.819 resultados têm `data_resultado` em 2026. Isso é esperado: o edital foi publicado em 2025 e a homologação saiu depois.

### 3.3 CNPJ / CPF

| Situação | `compras.cnpj_orgao` | `resultados.ni_fornecedor` |
|---|---|---|
| Com máscara (`51.593.855/0001-04`) | 176 | 1.633 |
| Com espaços/NBSP nas pontas (`' 41428781000105 '`) | 131 | 990 |
| 14 dígitos (CNPJ completo) | 1.965 | 11.150 |
| 11 a 13 dígitos em CNPJ (**zeros perdidos** no começo) | 77 | 194 (PJ) |
| 10 dígitos em PF (CPF com zero perdido) | — | 154 |

- Em `compras.cnpj_orgao`, os 3 valores com 11 dígitos (por exemplo, `59311000126`) são **CNPJs com 3 zeros perdidos**, não CPFs. O comprador é sempre um órgão.
- Em `resultados`, o tamanho certo depende do `tipo_pessoa`: **PJ → 14 dígitos (CNPJ), PF → 11 dígitos (CPF)**. Para completar com zeros, o `tipo_pessoa` é a referência.
- Os 21 fornecedores **PE (estrangeiros)** têm identificadores de 3 a 11 dígitos. Não são CNPJ nem CPF, então não devem ganhar zeros à esquerda.

---

## 4. Problemas de texto

### 4.1 Vazios disfarçados

| Coluna | Ocorrências (prévia) | Valores encontrados |
|---|---|---|
| `compras.processo` | 72 | N/A, NULL, `-`, `0`, SEM INFORMAÇÃO |
| `compras.modo_disputa` | 63 | N/A, n/a, NULL, Null, `-`, `0`, SEM INFORMAÇÃO, NÃO INFORMADO |
| `itens.situacao_item` | 220 | n/a, N/A, NULL, Null, `-`, `0`, SEM INFORMAÇÃO, NÃO INFORMADO |
| `resultados.porte` | 469 | N/A, n/a, NULL, Null, `-`, `0`, SEM INFORMAÇÃO, NÃO INFORMADO |

- Os valores aparecem em **maiúsculas e minúsculas variadas** (`NULL`, `Null`, `n/a`). A comparação deve ignorar maiúsculas.
- Em `porte`, o valor **"Não Informado"** (4.415, a maioria de PF) aparece misturado com "NÃO INFORMADO" em maiúsculas. Como a comparação ignora maiúsculas, **os dois contam como vazio disfarçado**. O resultado final é o mesmo: no `porte_descricao` eles viram "Não informado".
- **"Não se aplica"** também conta como vazio disfarçado. Ele aparece em `modo_disputa` (904), `criterio_julgamento` (1.883), `categoria_item` (7.077) e `porte` (9). O enunciado (desafio 4) coloca "NÃO SE APLICA" na lista de vazios disfarçados, e a lista do `src/limpeza.py` segue a mesma regra.
- *Correção feita na Sprint 1:* a primeira versão deste documento dizia que "Não se aplica" era uma informação legítima. A auditoria seguiu o enunciado, e as contagens oficiais estão no [README](../README.md#vazios-disfarçados).

### 4.2 Acentos quebrados (UTF-8 lido como Latin-1)

| Coluna | Registros | Sequências mais comuns | Exemplo |
|---|---|---|---|
| `itens.descricao` | 116 | `Ã§` (ç), `Ã£` (ã), `Ã­` (í), `Ã©` (é) | `CaracterÃ­sticas` |
| `compras.objeto_compra` | 43 | `Ã§`, `Ã£`, `Ã¡` (á), `Ãµ` (õ), `Ã‡` (Ç) | `ContrataÃ§Ã£o de empresa…` |
| `compras.municipio` | 28 | `Ã£`, `Ã³` (ó), `Ã­` | `SÃ£o Carlos` |
| `compras.nome_unidade` | 14 | `Ã` (Á), `Ã‡` (Ç), `Âº` (º) | `GOIÃS` |
| `resultados.nome_fornecedor` | 1 | `Ã©` | `AÃ©ronav Inc.` |

### 4.3 Caracteres invisíveis

- **NBSP (`\xa0`)** em quase todas as colunas de texto, dinheiro e documento, por exemplo 990 em `ni_fornecedor` e 704 em `valor_unitario_homologado`.
- **TAB** em `descricao` (40), `objeto_compra` (5) e `processo` (1).
- **Espaço de largura zero (`​`)** em 1 `objeto_compra`.

### 4.4 Mesmo órgão ou fornecedor escrito de jeitos diferentes

O mesmo documento aparece com variações de maiúsculas, espaços duplos e NBSP:

- **67 CNPJs de órgão** com mais de uma grafia de `razao_social_orgao`, por exemplo `COMANDO DA AERONAUTICA` · `Comando Da Aeronautica` · `  COMANDO  DA AERONAUTICA\xa0` · `comando da aeronautica`.
- **490 documentos de fornecedor** com mais de uma grafia de `nome_fornecedor`, por exemplo `MUNDIAL RESIDENCE TRANSPORTES E LOGISTICA LTDA` e `mundial residence transportes e logistica ltda`.

---

## 5. Datas invertidas

Este é o caso de uma homologação (`resultados.data_resultado`) com data **anterior** à publicação do edital (`compras.data_publicacao`), comparando só o dia:

- **234 resultados** em **134 contratações** (prévia).
- A data de resultado mais antiga é 17/12/2024, antes da primeira publicação da amostra (02/01/2025).

A forma de tratar essas linhas segue a regra 7 do enunciado e fica para as Sprints 1 a 3.

---

## 6. Respostas às perguntas do enunciado (seção 7.4)

| Pergunta | Resposta |
|---|---|
| Quantas linhas tem cada arquivo? | compras 2.042 · itens 7.077 · resultados 15.896 (registros, não linhas físicas) |
| Há `numero_controle_pncp` repetido em `compras.csv`? | Não |
| Que formatos de dinheiro aparecem? | Ponto decimal, `R$` em padrão BR, BR com milhar, US com milhar e só vírgula decimal, às vezes com NBSP. Nenhum negativo |
| Que formatos de data aparecem? | 7: ISO (com e sem hora), `dd/mm/aaaa` (com e sem hora), `dd.mm.aaaa`, `dd-mm-aaaa`, `aaaa/mm/dd` e `aaaammdd` |
| Que formatos de CNPJ aparecem? | Com máscara, só dígitos, com espaços/NBSP e com zeros perdidos no começo |
| Quais colunas têm N/A, `-`, `0`, vazio? | `processo`, `modo_disputa`, `situacao_item` e `porte` (vazios disfarçados); `data_abertura_proposta`, `data_encerramento_proposta`, `unidade_medida`, `catalogo_codigo_item`, `ordem_classificacao_srp` e `data_cancelamento` (vazios de verdade) |
| Existe texto com acento quebrado? Em quais colunas? | Sim: `descricao`, `objeto_compra`, `municipio`, `nome_unidade` e `nome_fornecedor` |
| Existe `data_resultado` anterior a `data_publicacao`? | Sim: 234 resultados em 134 contratações |

---

## 7. O que levar para as próximas Sprints

1. **Sprint 1:** transformar as prévias deste documento em contagens oficiais no README. Registrar também que **não há negativos entre parênteses**, mesmo estando no planejamento.
2. **Sprint 2:** a limpeza de números precisa tirar `R$`, NBSP e espaços **também das quantidades**, e não só do dinheiro.
3. **Sprint 2:** completar o documento com zeros conforme o `tipo_pessoa` (PJ → 14, PF → 11) e não mexer nos PE.
4. **Sprint 3:** quase não há `ordem_classificacao_srp` preenchida, então o vencedor sai, na prática, pelo **menor `sequencial_resultado`** entre os não cancelados.
5. **Sprint 3:** `unidade_medida` tem 359 grafias. Ela não entra na fato, mas vale padronizar se for usada em algum lugar.
