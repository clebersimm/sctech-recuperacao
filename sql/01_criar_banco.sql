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
-- Chaves e ligacoes (cada regra tem nome, para a mensagem de erro dizer qual foi quebrada):
--   pk_...  chave primaria: o numero proprio de cada linha (sk_)
--   uq_...  valor unico: o codigo original (CNPJ, UF, modalidade) nao se repete
--   fk_...  ligacao: cada linha da fato aponta para uma linha que existe na dimensao
-- A linha "Nao informado" (sk = -1) nao foi criada: nenhuma ligacao da fato fica sem destino.
--
-- Travas (chk_...): o banco e a segunda barreira, recusa dado impossivel mesmo que passe pelo Python:
--   quantidade > 0, valores >= 0 (menos economia_valor), dias_ciclo >= 0 e colunas 0/1 so com 0 ou 1.
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
    poder           VARCHAR  NOT NULL,

    CONSTRAINT pk_dim_orgao       PRIMARY KEY (sk_orgao),
    CONSTRAINT uq_dim_orgao_cnpj  UNIQUE (cnpj_orgao)
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
    porte_descricao   VARCHAR  NOT NULL,

    CONSTRAINT pk_dim_fornecedor     PRIMARY KEY (sk_fornecedor),
    CONSTRAINT uq_dim_fornecedor_ni  UNIQUE (ni_fornecedor)
);


-- ---------------------------------------------------------------------------------------------
-- DIMENSAO: como comprou (uma linha por modalidade)
-- ---------------------------------------------------------------------------------------------
CREATE TABLE dim_modalidade (
    sk_modalidade      INTEGER  NOT NULL,
    modalidade_id      INTEGER  NOT NULL,
    nome_modalidade    VARCHAR  NOT NULL,
    grupo_modalidade   VARCHAR  NOT NULL,

    CONSTRAINT pk_dim_modalidade     PRIMARY KEY (sk_modalidade),
    CONSTRAINT uq_dim_modalidade_id  UNIQUE (modalidade_id)
);


-- ---------------------------------------------------------------------------------------------
-- DIMENSAO: onde (uma linha por UF)
-- ---------------------------------------------------------------------------------------------
CREATE TABLE dim_localidade (
    sk_localidade   INTEGER  NOT NULL,
    uf_sigla        VARCHAR  NOT NULL,
    uf_nome         VARCHAR  NOT NULL,
    regiao          VARCHAR  NOT NULL,

    CONSTRAINT pk_dim_localidade     PRIMARY KEY (sk_localidade),
    CONSTRAINT uq_dim_localidade_uf  UNIQUE (uf_sigla)
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
    ciclo_longo                 SMALLINT       NOT NULL,

    -- chave primaria e item sem repetir (numero_controle_pncp + numero_item, juntos, sao unicos)
    CONSTRAINT pk_fato_item_contratado  PRIMARY KEY (sk_fato),
    CONSTRAINT uq_fato_item             UNIQUE (numero_controle_pncp, numero_item),

    -- ligacoes: cada sk_ da fato precisa existir na dimensao
    CONSTRAINT fk_fato_orgao       FOREIGN KEY (sk_orgao)       REFERENCES dim_orgao (sk_orgao),
    CONSTRAINT fk_fato_fornecedor  FOREIGN KEY (sk_fornecedor)  REFERENCES dim_fornecedor (sk_fornecedor),
    CONSTRAINT fk_fato_modalidade  FOREIGN KEY (sk_modalidade)  REFERENCES dim_modalidade (sk_modalidade),
    CONSTRAINT fk_fato_localidade  FOREIGN KEY (sk_localidade)  REFERENCES dim_localidade (sk_localidade),

    -- travas: quantidade positiva
    CONSTRAINT chk_fato_quantidade                 CHECK (quantidade > 0),

    -- travas: valores nao negativos (>= 0, e nao > 0: um total pode arredondar para R$ 0,00,
    -- ex.: unitario R$ 0,0001 x quantidade 1). economia_valor NAO tem trava: e negativa quando ha sobrepreco
    CONSTRAINT chk_fato_valor_unitario_estimado    CHECK (valor_unitario_estimado >= 0),
    CONSTRAINT chk_fato_valor_total_estimado       CHECK (valor_total_estimado >= 0),
    CONSTRAINT chk_fato_valor_unitario_homologado  CHECK (valor_unitario_homologado >= 0),
    CONSTRAINT chk_fato_valor_total_homologado     CHECK (valor_total_homologado >= 0),
    CONSTRAINT chk_fato_valor_sobrepreco           CHECK (valor_sobrepreco >= 0),

    -- trava: ciclo nunca negativo (a regra 7 ja anula homologacao anterior a publicacao), vazio e aceito
    CONSTRAINT chk_fato_dias_ciclo                 CHECK (dias_ciclo >= 0),

    -- travas: colunas de 1 ou 0
    CONSTRAINT chk_fato_comparavel                 CHECK (comparavel IN (0, 1)),
    CONSTRAINT chk_fato_sobrepreco                 CHECK (sobrepreco IN (0, 1)),
    CONSTRAINT chk_fato_fornecedor_me_epp          CHECK (fornecedor_me_epp IN (0, 1)),
    CONSTRAINT chk_fato_contratacao_direta         CHECK (contratacao_direta IN (0, 1)),
    CONSTRAINT chk_fato_ciclo_longo                CHECK (ciclo_longo IN (0, 1))
);
