-- =============================================================================================
-- 02_perguntas.sql  -  AS 6 PERGUNTAS DA CONTROLADORIA (secao 4.4 do enunciado)
-- =============================================================================================
-- Rode no pgAdmin, no banco pncp_controladoria, depois da carga (python -m src.carregar).
-- Cada consulta tem um comentario dizendo o que ela responde. Compare com a prova real (anexo 8).
--
-- Regras usadas em todas as consultas:
--   * percentual = SOMA / SOMA, nunca media de percentuais
--   * a economia so conta os itens comparaveis (comparavel = 1)
--   * as metricas do ETL (sobrepreco, fornecedor_me_epp...) ja estao na fato: nao sao recalculadas aqui
--   * NULLIF(denominador, 0) evita divisao por zero (Credenciamento nao tem item comparavel)
--   * o 100.0 evita a divisao inteira (que daria 0)
-- =============================================================================================


-- #############################################################################################
-- PERGUNTA 1 - ECONOMIA GLOBAL DO PODER PUBLICO
-- Quantos itens foram homologados acima do estimado, quanto isso custou e onde eles se concentram
-- (modalidade, perfil e regiao)? Qual e o percentual e o valor nominal economizado pelo governo?
-- #############################################################################################

-- 1.1 Resumo: economia (R$ e %) na base comparavel e total do sobrepreco
--     Prova real: 5.457 comparaveis | estimado comparavel R$ 6.867.663.469,91 | economia R$ 992.861.686,95
--                 economia 14,46% | 27 itens com sobrepreco | R$ 44.440,34
SELECT
    COUNT(*)                                                                    AS itens,
    SUM(comparavel)                                                             AS itens_comparaveis,
    SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END)          AS estimado_comparavel,
    SUM(economia_valor)                                                         AS economia_valor,
    ROUND(SUM(economia_valor) * 100.0
          / NULLIF(SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END), 0), 2)
                                                                                AS economia_pct,
    SUM(sobrepreco)                                                             AS itens_sobrepreco,
    SUM(valor_sobrepreco)                                                       AS valor_sobrepreco
FROM fato_item_contratado;


-- 1.2 Onde se concentra o sobrepreco: por modalidade
SELECT
    m.nome_modalidade,
    SUM(f.sobrepreco)        AS itens_sobrepreco,
    SUM(f.valor_sobrepreco)  AS valor_sobrepreco
FROM fato_item_contratado f
JOIN dim_modalidade m ON m.sk_modalidade = f.sk_modalidade
GROUP BY m.nome_modalidade
ORDER BY valor_sobrepreco DESC, itens_sobrepreco DESC;


-- 1.3 Onde se concentra o sobrepreco: por perfil do gasto (coluna da propria fato)
SELECT
    perfil_gasto,
    SUM(sobrepreco)        AS itens_sobrepreco,
    SUM(valor_sobrepreco)  AS valor_sobrepreco
FROM fato_item_contratado
GROUP BY perfil_gasto
ORDER BY valor_sobrepreco DESC, itens_sobrepreco DESC;


-- 1.4 Onde se concentra o sobrepreco: por regiao
SELECT
    l.regiao,
    SUM(f.sobrepreco)        AS itens_sobrepreco,
    SUM(f.valor_sobrepreco)  AS valor_sobrepreco
FROM fato_item_contratado f
JOIN dim_localidade l ON l.sk_localidade = f.sk_localidade
GROUP BY l.regiao
ORDER BY valor_sobrepreco DESC, itens_sobrepreco DESC;


-- #############################################################################################
-- PERGUNTA 2 - CONCENTRACAO DE FORNECEDORES E ME/EPP
-- Quanto do volume e dos itens vai para micro e pequenas empresas (ME/EPP)? Quem sao os maiores
-- fornecedores em volume financeiro e qual percentual do orcamento publico esta concentrado neles?
-- #############################################################################################

-- 2.1 ME/EPP: itens e volume (usa a coluna fornecedor_me_epp da fato, nao o porte da dim_fornecedor)
--     Prova real: 3.853 itens | R$ 1.603.610.879,06 | 19,93% do volume
SELECT
    COUNT(*)                                                                    AS itens,
    SUM(fornecedor_me_epp)                                                      AS itens_me_epp,
    ROUND(SUM(fornecedor_me_epp) * 100.0 / COUNT(*), 2)                         AS itens_me_epp_pct,
    SUM(valor_total_homologado)                                                 AS volume_total,
    SUM(CASE WHEN fornecedor_me_epp = 1 THEN valor_total_homologado ELSE 0 END) AS volume_me_epp,
    ROUND(SUM(CASE WHEN fornecedor_me_epp = 1 THEN valor_total_homologado ELSE 0 END) * 100.0
          / NULLIF(SUM(valor_total_homologado), 0), 2)                          AS volume_me_epp_pct
FROM fato_item_contratado;


-- 2.2 Os 10 maiores fornecedores em volume (fornecedor = CNPJ/CPF limpo; filiais contam separado)
--     O percentual do total sai de uma subconsulta no denominador
SELECT
    d.ni_fornecedor,
    d.nome_fornecedor,
    d.porte_descricao,
    COUNT(*)                     AS itens,
    SUM(f.valor_total_homologado) AS volume,
    ROUND(SUM(f.valor_total_homologado) * 100.0
          / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2) AS volume_pct
FROM fato_item_contratado f
JOIN dim_fornecedor d ON d.sk_fornecedor = f.sk_fornecedor
GROUP BY d.ni_fornecedor, d.nome_fornecedor, d.porte_descricao
ORDER BY volume DESC
LIMIT 10;


-- 2.3 Concentracao: quanto do volume total fica com os 10 maiores fornecedores
SELECT
    SUM(volume)                                                                 AS volume_top10,
    ROUND(SUM(volume) * 100.0
          / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2)  AS concentracao_top10_pct
FROM (
    SELECT sk_fornecedor, SUM(valor_total_homologado) AS volume
    FROM fato_item_contratado
    GROUP BY sk_fornecedor
    ORDER BY volume DESC
    LIMIT 10
) AS top10;


-- #############################################################################################
-- PERGUNTA 3 - EFICACIA POR MODALIDADE E CONTRATACAO DIRETA
-- Quanto do volume e contratado sem licitacao (Dispensa e Inexigibilidade) e como o ciclo dessas
-- contratacoes se compara ao das demais? Como os grupos de modalidade se comparam?
-- #############################################################################################

-- 3.1 Volume contratado sem licitacao (contratacao_direta = 1: Dispensa ou Inexigibilidade)
--     Prova real: 1.890 itens | R$ 253.252.588,63 | 3,15% do volume
SELECT
    SUM(contratacao_direta)                                                      AS itens_contratacao_direta,
    SUM(CASE WHEN contratacao_direta = 1 THEN valor_total_homologado ELSE 0 END) AS volume_contratacao_direta,
    ROUND(SUM(CASE WHEN contratacao_direta = 1 THEN valor_total_homologado ELSE 0 END) * 100.0
          / NULLIF(SUM(valor_total_homologado), 0), 2)                           AS volume_contratacao_direta_pct
FROM fato_item_contratado;


-- 3.2 Ciclo da contratacao direta x demais (AVG ja ignora os itens sem ciclo)
--     % de ciclo longo = itens com ciclo longo / itens COM ciclo (nunca / total de itens)
SELECT
    CASE WHEN contratacao_direta = 1 THEN 'Contratação direta' ELSE 'Demais modalidades' END AS tipo,
    COUNT(dias_ciclo)                                                AS itens_com_ciclo,
    ROUND(AVG(dias_ciclo), 1)                                        AS ciclo_medio_dias,
    ROUND(SUM(ciclo_longo) * 100.0 / NULLIF(COUNT(dias_ciclo), 0), 2) AS ciclo_longo_pct
FROM fato_item_contratado
GROUP BY contratacao_direta
ORDER BY contratacao_direta DESC;


-- 3.3 Comparacao entre os grupos de modalidade
--     Prova real (itens): Pregao 3.051 | Contratacao direta 1.890 | Credenciamento 601 | Concorrencia 584
--     Credenciamento fica com economia_pct vazia: nao tem item comparavel (e esperado, nao e erro)
SELECT
    m.grupo_modalidade,
    COUNT(*)                                                                    AS itens,
    SUM(f.valor_total_homologado)                                               AS volume,
    ROUND(SUM(f.valor_total_homologado) * 100.0
          / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2)  AS volume_pct,
    ROUND(SUM(f.economia_valor) * 100.0
          / NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2)
                                                                                AS economia_pct,
    ROUND(AVG(f.dias_ciclo), 1)                                                 AS ciclo_medio_dias
FROM fato_item_contratado f
JOIN dim_modalidade m ON m.sk_modalidade = f.sk_modalidade
GROUP BY m.grupo_modalidade
ORDER BY volume DESC;


-- #############################################################################################
-- PERGUNTA 4 - TEMPO DO CICLO DE COMPRAS
-- Quais orgaos e modalidades tem a maior proporcao de itens com ciclo longo (acima de 90 dias)?
-- Qual a duracao media (em dias) entre o edital e a homologacao, segmentada por modalidade?
-- #############################################################################################

-- 4.1 Os 10 orgaos com maior proporcao de ciclo longo
--     Agrupa pelo NOME padronizado (o mesmo orgao tem varios CNPJ) e so orgaos com 5 ou mais itens com ciclo.
--     Empate no %: fica na frente quem tem mais itens com ciclo.
SELECT
    o.nome_orgao,
    COUNT(f.dias_ciclo)                                     AS itens_com_ciclo,
    SUM(f.ciclo_longo)                                      AS itens_ciclo_longo,
    ROUND(SUM(f.ciclo_longo) * 100.0 / COUNT(f.dias_ciclo), 2) AS ciclo_longo_pct,
    ROUND(AVG(f.dias_ciclo), 1)                             AS ciclo_medio_dias
FROM fato_item_contratado f
JOIN dim_orgao o ON o.sk_orgao = f.sk_orgao
GROUP BY o.nome_orgao
HAVING COUNT(f.dias_ciclo) >= 5
ORDER BY ciclo_longo_pct DESC, itens_com_ciclo DESC
LIMIT 10;


-- 4.2 Por modalidade: proporcao de ciclo longo e duracao media
--     Prova real (geral): 5.896 itens com ciclo | ciclo medio 48,1 dias | 830 com ciclo longo (14,1%)
SELECT
    m.nome_modalidade,
    COUNT(f.dias_ciclo)                                                  AS itens_com_ciclo,
    SUM(f.ciclo_longo)                                                   AS itens_ciclo_longo,
    ROUND(SUM(f.ciclo_longo) * 100.0 / NULLIF(COUNT(f.dias_ciclo), 0), 2) AS ciclo_longo_pct,
    ROUND(AVG(f.dias_ciclo), 1)                                          AS ciclo_medio_dias
FROM fato_item_contratado f
JOIN dim_modalidade m ON m.sk_modalidade = f.sk_modalidade
GROUP BY m.nome_modalidade
ORDER BY ciclo_longo_pct DESC;


-- 4.3 Total geral do ciclo (referencia para comparar as modalidades)
SELECT
    COUNT(dias_ciclo)                                      AS itens_com_ciclo,
    ROUND(AVG(dias_ciclo), 1)                              AS ciclo_medio_dias,
    MAX(dias_ciclo)                                        AS ciclo_maximo_dias,
    SUM(ciclo_longo)                                       AS itens_ciclo_longo,
    ROUND(SUM(ciclo_longo) * 100.0 / COUNT(dias_ciclo), 2) AS ciclo_longo_pct
FROM fato_item_contratado;
