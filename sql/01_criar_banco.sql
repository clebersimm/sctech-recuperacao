-- =============================================================================================
-- 01_criar_banco.sql  -  CRIA AS 5 TABELAS DO BANCO (1 fato + 4 dimensoes)
-- =============================================================================================
-- Executado pelo src/carregar.py, logo depois de banco.recriar_banco() apagar e criar o banco de novo.
-- Por isso este script so cria as tabelas (sem DROP TABLE nem CREATE DATABASE).
--
-- Tipos (secao 4.3 do enunciado):
--   texto = VARCHAR (descricao do item = TEXT)        datas = DATE
--   dinheiro = DECIMAL(18,2)                           1 ou 0 = SMALLINT
--   precos unitarios e quantidades = DECIMAL(18,4)
--
-- NOT NULL = a coluna nao pode ficar vazia. So ficam sem NOT NULL as colunas que podem vir vazias:
--   dim_fornecedor.porte (porte nao informado), fato.data_homologacao e fato.dias_ciclo (regra 7).
--
-- As dimensoes vem primeiro, porque a fato aponta para elas.
-- =============================================================================================


-- ---------------------------------------------------------------------------------------------
-- DIMENSAO: quem comprou (uma linha por CNPJ de orgao)
-- ---------------------------------------------------------------------------------------------
CREATE TABLE dim_orgao (
    sk_orgao        INTEGER  NOT NULL,
    cnpj_orgao      VARCHAR  NOT NULL,
    nome_orgao      VARCHAR  NOT NULL,
    poder           VARCHAR  NOT NULL
);


-- ---------------------------------------------------------------------------------------------
-- DIMENSAO: quem vendeu (uma linha por CNPJ/CPF de fornecedor)
-- ---------------------------------------------------------------------------------------------
CREATE TABLE dim_fornecedor (
    sk_fornecedor     INTEGER  NOT NULL,
    ni_fornecedor     VARCHAR  NOT NULL,
    nome_fornecedor   VARCHAR  NOT NULL,
    tipo_pessoa       VARCHAR  NOT NULL,
    porte             VARCHAR,
    porte_descricao   VARCHAR  NOT NULL
);


-- ---------------------------------------------------------------------------------------------
-- DIMENSAO: como comprou (uma linha por modalidade)
-- ---------------------------------------------------------------------------------------------
CREATE TABLE dim_modalidade (
    sk_modalidade      INTEGER  NOT NULL,
    modalidade_id      INTEGER  NOT NULL,
    nome_modalidade    VARCHAR  NOT NULL,
    grupo_modalidade   VARCHAR  NOT NULL
);


-- ---------------------------------------------------------------------------------------------
-- DIMENSAO: onde (uma linha por UF)
-- ---------------------------------------------------------------------------------------------
CREATE TABLE dim_localidade (
    sk_localidade   INTEGER  NOT NULL,
    uf_sigla        VARCHAR  NOT NULL,
    uf_nome         VARCHAR  NOT NULL,
    regiao          VARCHAR  NOT NULL
);


-- ---------------------------------------------------------------------------------------------
-- FATO: o que foi comprado (uma linha por item de contratacao, com o vencedor)
-- sk_fato e numerado pelo proprio banco (1, 2, 3...), porque a carga nao envia essa coluna.
-- ---------------------------------------------------------------------------------------------
CREATE TABLE fato_item_contratado (
    sk_fato                     INTEGER        GENERATED ALWAYS AS IDENTITY,
    numero_controle_pncp        VARCHAR        NOT NULL,
    numero_item                 INTEGER        NOT NULL,

    -- ligacoes com as dimensoes
    sk_orgao                    INTEGER        NOT NULL,
    sk_fornecedor               INTEGER        NOT NULL,
    sk_modalidade               INTEGER        NOT NULL,
    sk_localidade               INTEGER        NOT NULL,

    -- datas (data_homologacao fica vazia quando a homologacao e anterior a publicacao, regra 7)
    data_publicacao             DATE           NOT NULL,
    data_homologacao            DATE,

    -- item
    descricao_item              TEXT           NOT NULL,
    perfil_gasto                VARCHAR        NOT NULL,

    -- numeros
    quantidade                  DECIMAL(18,4)  NOT NULL,
    valor_unitario_estimado     DECIMAL(18,4)  NOT NULL,
    valor_total_estimado        DECIMAL(18,2)  NOT NULL,
    valor_unitario_homologado   DECIMAL(18,4)  NOT NULL,
    valor_total_homologado      DECIMAL(18,2)  NOT NULL,

    -- calculados no Python (regras 6 e 7)
    comparavel                  SMALLINT       NOT NULL,
    economia_valor              DECIMAL(18,2)  NOT NULL,
    dias_ciclo                  INTEGER,

    -- metricas do ETL (regra 13)
    sobrepreco                  SMALLINT       NOT NULL,
    valor_sobrepreco            DECIMAL(18,2)  NOT NULL,
    fornecedor_me_epp           SMALLINT       NOT NULL,
    contratacao_direta          SMALLINT       NOT NULL,
    ciclo_longo                 SMALLINT       NOT NULL
);
