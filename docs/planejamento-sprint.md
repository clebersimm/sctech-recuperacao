# Planejamento das Sprints

Este documento apresenta o planejamento do desenvolvimento do projeto: **Esteira analítica de compras públicas (PNCP 2025) para a Controladoria**   
Foi escolhido o documento markdown por manter a coerencia com o resto do desenvolvimento do projeto e padão de visualização do github.   

## Legenda de status

- Utilização de marcação visual para orientação do andamento das sprints.   

| Ícone | Status |
|---|---|
| ⬜ | A fazer |
| 🔄 | Em andamento |
| ✅ | Concluído |


## Visão geral

| Sprint | Nome | Objetivo | Status |
|---|---|---|---|
| 0 | Preparação | Preparar repositório e ambiente e entender os dados | ✅ |
| 1 | Auditoria | Descobrir e contar os problemas dos dados | ✅ |
| 2 | Limpeza | Completar as funções que corrigem os problemas dos dados | ✅ |
| 3 | Montar as tabelas | Aplicar as regras de negócio e montar a fato e as 4 dimensões | 🔄 |
| 4 | Banco de dados | Criar as tabelas no PostgreSQL e carregar os dados automaticamente | ⬜ |
| 5 | Perguntas em SQL | Responder às 6 perguntas da Controladoria com consultas no banco | ⬜ |
| 6 | Power BI | Montar o painel visual que conta a história das 6 perguntas | ⬜ |
| 7 | Documentação e entrega | Documentar o projeto no README e entregar o link do repositório | ⬜ |

---

## Sprint 0 – Preparação e conhecimento dos dados

**Objetivo:** deixar o repositório e o ambiente prontos e entender o que existe em cada arquivo de dados.


| # | Tarefa | Escopo | Status |
|---|---|---|---|
| 0.1 | Preparar o repositório | Criar o repositório no GitHub, guardar os arquivos do kit no Git e organizar as pastas (`docs/`, `sql/`, `powerbi/`), sem arquivos soltos na raiz | ✅ |
| 0.2 | Preparar o ambiente | Instalar as bibliotecas do `requirements.txt`, ter o PostgreSQL funcionando e preencher o `.env` | ✅ |
| 0.3 | Conhecer os dados | Abrir os 3 CSVs, descrever cada coluna e ver quantas linhas tem cada arquivo, os formatos de dinheiro, data e CNPJ, os acentos quebrados e as datas invertidas. Resultado em [`docs/conhecendo-os-dados.md`](conhecendo-os-dados.md) | ✅ |

---

## Sprint 1 – Auditoria (contar os problemas)

**Objetivo:** descobrir quais problemas existem nos dados e quantos registros cada um afeta, antes de corrigir qualquer coisa.
**Como saber que acabou:** o README lista cada problema e quantos registros ele afeta.

| # | Tarefa | Escopo | Status |
|---|---|---|---|
| 1.1 | Contar problemas de documentos e dinheiro | CNPJ/CPF com pontos, traços e zeros perdidos; dinheiro escrito com R$, ponto e vírgula trocados e negativos entre parênteses. Script em [`src/auditoria.py`](../src/auditoria.py) e resultado no [README](../README.md#auditoria-dos-dados) | ✅ |
| 1.2 | Contar problemas de datas | Datas escritas em formatos diferentes e homologações com data anterior à publicação do edital. Script em [`src/auditoria.py`](../src/auditoria.py) e resultado no [README](../README.md#datas-em-formatos-diferentes) | ✅ |
| 1.3 | Contar problemas de texto | Vazios disfarçados ("N/A", "NULL", "-", "0", "SEM INFORMAÇÃO"), acentos quebrados (Ã§, Ã£) e o mesmo órgão ou fornecedor escrito de jeitos diferentes. Script em [`src/auditoria.py`](../src/auditoria.py) e resultado no [README](../README.md#vazios-disfarçados) | ✅ |
| 1.4 | Registrar no README | Montar a lista dos problemas encontrados, com a quantidade de registros de cada um. Tabela [Resumo dos problemas](../README.md#resumo-dos-problemas) no README, gerada pela função `resumo()` do `src/auditoria.py` | ✅ |

---

## Sprint 2 – Limpeza (completar o `src/limpeza.py`)

**Objetivo:** completar as funções que corrigem cada tipo de problema encontrado na auditoria.
**Como saber que acabou:** o autoteste (`python -m src.limpeza`) mostra ✔ em todos os exemplos.

| # | Tarefa | Escopo | Status |
|---|---|---|---|
| 2.1 | Limpar textos e vazios | Tirar caracteres invisíveis e espaços sobrando, consertar acentos, tratar "N/A", "-" e "NULL" como vazio e padronizar os nomes (`remover_invisiveis`, `consertar_acento`, `tirar_espacos`, `eh_nulo`, `limpar_texto`, `padronizar_nome`) | ✅ |
| 2.2 | Limpar CNPJ/CPF | Tirar pontos e traços e devolver os zeros perdidos no começo (`limpar_documento`) | ✅ |
| 2.3 | Converter dinheiro, números e datas | Transformar texto em número (ponto ou vírgula sozinho é sempre a parte decimal) e deixar as datas no mesmo padrão (`converter_numero`, `converter_data`) | ✅ |
| 2.4 | Rodar o autoteste | Executar `python -m src.limpeza` e conferir ✔ em todos os exemplos | ✅ |

---

## Sprint 3 – Montar as tabelas (completar o `src/montar_tabelas.py`)

**Objetivo:** aplicar as regras de negócio da Controladoria e montar a tabela principal (fato) e as 4 tabelas de apoio (dimensões).
**Como saber que acabou:** as linhas, as somas e as 5 métricas batem com a prova real (anexo 8).

| # | Tarefa | Escopo | Status |
|---|---|---|---|
| 3.1 | Limpar os arquivos e criar as colunas novas | Usar as funções da Sprint 2 nos 3 arquivos e criar a região, o grupo da modalidade, o porte e o poder por extenso (etapas 1 e 1B) | ✅ |
| 3.2 | Escolher o vencedor e juntar os arquivos | Descartar os cancelados, ficar com o 1º colocado (no empate, o de menor sequencial) e ligar compras, itens e vencedores; só entram itens com resultado (etapas 2 e 3) | ✅ |
| 3.3 | Calcular os valores e rejeitar itens impossíveis | Valor unitário × quantidade homologada; depois tirar itens com valores inválidos, sigilosos ou absurdos e contar quantos foram (etapas 4 e 5) | ✅ |
| 3.4 | Calcular economia, tempo e tipo de gasto | Marcar o que é comparável e a economia, contar os dias entre a publicação e a homologação e classificar em Bens, Serviços ou Obras (etapas 6, 7 e 8) | ✅ |
| 3.5 | Calcular as 5 métricas | Sobrepreço, valor do sobrepreço, fornecedor ME/EPP, contratação direta e ciclo longo (etapa 8B) | ✅ |
| 3.6 | Montar as dimensões e conferir | Criar órgão, fornecedor, modalidade e localidade com seus números de identificação e comparar com a prova real (ex.: 6.126 itens na fato e 99 rejeitados) (etapas 9 e 10) | ⬜ |

---

## Sprint 4 – Banco de dados (escrever `sql/01_criar_banco.sql` e completar `src/carregar.py`)

**Objetivo:** criar as 5 tabelas no PostgreSQL com as regras de proteção e carregar os dados tratados de forma automática.
**Como saber que acabou:** as contagens no banco são iguais às dos arquivos e toda ligação da fato aponta para uma linha que existe.

| # | Tarefa | Escopo | Status |
|---|---|---|---|
| 4.1 | Escrever o script de criação das tabelas | Criar `sql/01_criar_banco.sql` com a fato e as 4 dimensões, usando os nomes do enunciado e os tipos certos (dinheiro como decimal, datas como data, 0/1 como número pequeno) | ⬜ |
| 4.2 | Definir as chaves e as ligações | Cada tabela tem seu número próprio (`sk_…`), o código original (CNPJ, UF, modalidade) não se repete, toda linha da fato aponta para uma dimensão que existe e, se faltar dado, usa-se a linha "Não informado" (−1) | ⬜ |
| 4.3 | Colocar as travas do banco | Recusar quantidade ≤ 0 e valores negativos; as colunas das métricas só aceitam 0 ou 1 | ⬜ |
| 4.4 | Completar a carga e conferir | Completar o `src/carregar.py` para enviar os dados em lote, desfazendo tudo se der erro; rodar `python -m src.carregar` e comparar as contagens com a prova real | ⬜ |

---

## Sprint 5 – Perguntas em SQL (escrever `sql/02_perguntas.sql`)

**Objetivo:** responder às 6 perguntas da Controladoria com consultas no banco.
**Como saber que acabou:** as respostas fazem sentido e batem com a prova real.

| # | Tarefa | Escopo | Status |
|---|---|---|---|
| 5.1 | Perguntas 1 e 2 – Economia e fornecedores | Quanto o governo economizou (R$ e %) e quantos itens saíram acima do estimado; quanto vai para micro e pequenas empresas e quanto fica com os 10 maiores fornecedores | ⬜ |
| 5.2 | Perguntas 3 e 4 – Modalidades e tempo | Quanto é contratado sem licitação e como os grupos de modalidade se comparam; quais órgãos e modalidades mais passam de 90 dias e qual é o tempo médio | ⬜ |
| 5.3 | Perguntas 5 e 6 – Regiões e tipo de gasto | Quais estados e regiões gastam mais, têm mais desconto e mais contratação direta; como o dinheiro se divide entre bens, serviços e obras | ⬜ |
| 5.4 | Rodar e conferir | Executar as consultas no pgAdmin e comparar com a prova real (ex.: economia de 14,46%) | ⬜ |

---

## Sprint 6 – Power BI

**Objetivo:** montar o painel visual que conta a história das 6 perguntas.
**Como saber que acabou:** as mesmas respostas do SQL aparecem no painel.

| # | Tarefa | Escopo | Status |
|---|---|---|---|
| 6.1 | Preparar o modelo | Trazer a fato e as 4 dimensões do PostgreSQL, ligar as dimensões à fato e desligar a hierarquia automática de datas (proibida no enunciado) | ⬜ |
| 6.2 | Criar o Calendário | Tabela de datas que se ajusta sozinha aos dados, com o mês em ordem certa, ligada às duas datas da fato | ⬜ |
| 6.3 | Criar as medidas | As 10 medidas obrigatórias em uma tabela só para elas, com pastas por pergunta, mais as medidas de apoio das 5 métricas na pasta "ETL" | ⬜ |
| 6.4 | Montar as páginas e a navegação | Uma página por pergunta (pergunta, números e frase de conclusão), menu que abre e fecha com botões e a dica ao passar o mouse | ⬜ |
| 6.5 | Cuidar do visual e salvar | Contraste, repetição, alinhamento e proximidade, com cores só para destacar o que importa; guardar o `.pbix` na pasta `powerbi/` | ⬜ |

---

## Sprint 7 – Documentação e entrega

**Objetivo:** documentar o projeto para que qualquer pessoa consiga entender e repetir o trabalho.
**Como saber que acabou:** alguém reproduz o projeto só lendo o README.

| # | Tarefa | Escopo | Status |
|---|---|---|---|
| 7.1 | Apresentar o projeto | Explicar o problema da Controladoria, dar um nome ao projeto, listar as ferramentas usadas (Python, pandas, PostgreSQL…) e apontar melhorias futuras | ⬜ |
| 7.2 | Explicar o tratamento dos dados | Contar as decisões técnicas e por quê (incluindo discordâncias das regras), a lista dos problemas tratados e a regra de cada uma das 5 métricas com os números obtidos | ⬜ |
| 7.3 | Explicar o banco e a execução | Diagrama da fato ligada às 4 dimensões e o passo a passo para rodar tudo do zero: instalar, preencher o `.env`, limpar, montar e carregar | ⬜ |
| 7.4 | Figura das Sprints | Salvar uma imagem deste planejamento em `docs/img/sprints.png` e colocá-la no README | ⬜ |
