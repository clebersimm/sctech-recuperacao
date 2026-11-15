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
