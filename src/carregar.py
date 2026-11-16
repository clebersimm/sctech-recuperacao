"""
carregar.py  -  CARGA NO POSTGRESQL
===================================
Passos:  1) recria o banco e as tabelas (banco.recriar_banco + sql/01_criar_banco.sql)
         2) carrega as 4 DIMENSOES   3) carrega a FATO (as dimensoes vem primeiro!)   4) confere as contagens
Usa so o que o kit ja traz: src/config.py e src/banco.py (recriar_banco, conectar, executar_script, inserir_em_lote, consultar).
O sql/01_criar_banco.sql e o SEU script (veja a secao 4.3 do enunciado): crie esse arquivo antes de rodar a carga.
Ele so cria as tabelas: o banco em si e recriado por banco.recriar_banco().
Dica: veja a carga em lote do 1_extrair.py do Desafio Transparencia (banco.inserir_em_lote).

TUDO OU NADA: antes de enviar, os arquivos passam por uma validacao (validar). Depois, criar as tabelas e carregar
as 5 tabelas e UM pacote so: o commit acontece uma vez, no final. Se qualquer passo der erro, o rollback desfaz tudo,
a mensagem diz em qual tabela foi, e o script termina com erro (codigo 1).

COMO RODAR (depois do montar_tabelas):   python -m src.carregar
"""

import sys

import pandas as pd
from psycopg2 import Error as ErroBanco

from src import banco, config

# Cada dimensao: (nome da tabela, colunas, chave natural, chave substituta)
DIMENSOES = [("dim_orgao", ["sk_orgao", "cnpj_orgao", "nome_orgao", "poder"], "cnpj_orgao", "sk_orgao"),
             ("dim_fornecedor", ["sk_fornecedor", "ni_fornecedor", "nome_fornecedor", "tipo_pessoa", "porte",
                                 "porte_descricao"], "ni_fornecedor", "sk_fornecedor"),
             ("dim_modalidade", ["sk_modalidade", "modalidade_id", "nome_modalidade", "grupo_modalidade"],
              "modalidade_id", "sk_modalidade"),
             ("dim_localidade", ["sk_localidade", "uf_sigla", "uf_nome", "regiao"], "uf_sigla", "sk_localidade")]

COLUNAS_FATO = ["numero_controle_pncp", "numero_item", "sk_orgao", "sk_fornecedor", "sk_modalidade", "sk_localidade",
                "data_publicacao", "data_homologacao", "descricao_item", "perfil_gasto", "quantidade",
                "valor_unitario_estimado", "valor_total_estimado", "valor_unitario_homologado", "valor_total_homologado",
                "comparavel", "economia_valor", "dias_ciclo",
                "sobrepreco", "valor_sobrepreco", "fornecedor_me_epp", "contratacao_direta", "ciclo_longo"]


def ler(nome, **opcoes):
    """PRONTA. Le um CSV de data/processed. Campo vazio vira NaN (que mais abaixo vira None = NULL no banco)."""
    return pd.read_csv(config.PASTA_PROCESSED / f"{nome}.csv", keep_default_na=False, na_values=[""], **opcoes)


def tuplas(tabela, colunas):
    """PRONTA. Transforma o DataFrame em uma lista de tuplas simples, que e o que o banco entende.
    Valor vazio (NaN) vira None, que o banco grava como NULL."""
    dados = tabela[colunas].astype(object)
    dados = dados.where(dados.notna(), None)
    return [tuple(linha) for linha in dados.itertuples(index=False, name=None)]


def inserir(con, tabela, colunas, dados):
    """Monta o INSERT INTO ... VALUES (%s, %s, ...) e envia todas as linhas de uma vez.
    gravar=False: o commit fica para o final da carga (tudo ou nada)."""
    # Um %s para cada coluna
    marcadores = ", ".join(["%s"] * len(colunas))
    sql = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({marcadores})"
    # Envia em lote
    banco.inserir_em_lote(con, sql, tuplas(dados, colunas), gravar=False)
    print(f"   {tabela}: {len(dados)} linhas")


def validar(dimensoes, fato):
    """Validacao previa de integridade, ANTES de enviar ao banco. Devolve a lista de problemas (vazia = tudo certo).
    Confere: chave substituta e chave natural sem repetir e sem vazio em cada dimensao; item sem repetir na fato;
    todo sk_ da fato existe na sua dimensao."""
    problemas = []
    for nome, _, chave, sk in DIMENSOES:
        dim = dimensoes[nome]
        for coluna in (sk, chave):
            if dim[coluna].isna().any():
                problemas.append(f"{nome}: {dim[coluna].isna().sum()} linha(s) com {coluna} vazio")
            if dim[coluna].duplicated().any():
                problemas.append(f"{nome}: {dim[coluna].duplicated().sum()} {coluna} repetido(s)")
        # todo sk_ da fato precisa existir na dimensao (as dimensoes foram lidas como texto)
        sem_destino = ~fato[sk].isin(pd.to_numeric(dim[sk]))
        if sem_destino.any():
            problemas.append(f"fato_item_contratado: {sem_destino.sum()} linha(s) com {sk} que nao existe em {nome}")
    repetidos = fato.duplicated(["numero_controle_pncp", "numero_item"]).sum()
    if repetidos:
        problemas.append(f"fato_item_contratado: {repetidos} item(ns) repetido(s) (numero_controle_pncp + numero_item)")
    return problemas


def main():
    # 0) Ler e validar ANTES de mexer no banco: se a validacao falhar, o banco nem e recriado
    # dtype=str: o CNPJ nao pode perder o zero da esquerda ao ser lido
    dimensoes = {nome: ler(nome, dtype=str) for nome, *_ in DIMENSOES}
    fato = ler("fato_item_contratado")
    # dias_ciclo vem como 48.0 (decimal) porque tem vazios; o banco quer inteiro: "Int64" aceita inteiro e vazio
    fato["dias_ciclo"] = fato["dias_ciclo"].astype("Int64")

    print("Validacao previa:")
    problemas = validar(dimensoes, fato)
    if problemas:
        for problema in problemas:
            print(f"   ERRO: {problema}")
        print("Carga cancelada: corrija o montar_tabelas e rode de novo. O banco nao foi alterado.")
        sys.exit(1)
    print("   OK: chaves sem repetir e toda ligacao da fato aponta para uma linha que existe")

    # 1) Banco (o recriar_banco apaga e cria de novo)
    banco.recriar_banco()
    con = banco.conectar()
    etapa = "criar as tabelas (sql/01_criar_banco.sql)"
    try:
        # Tabelas: executa o arquivo SQL de criacao, sem gravar ainda
        banco.executar_script(con, config.PASTA_SQL / "01_criar_banco.sql", gravar=False)

        # 2) Dimensoes PRIMEIRO: a fato tem chave estrangeira para elas, entao elas precisam existir antes.
        print("Carga:")
        for nome, colunas, _, _ in DIMENSOES:
            etapa = f"carregar {nome}"
            inserir(con, nome, colunas, dimensoes[nome])

        # 3) Fato (depois das dimensoes)
        etapa = "carregar fato_item_contratado"
        inserir(con, "fato_item_contratado", COLUNAS_FATO, fato)

        # Tudo certo: grava tudo de uma vez
        etapa = "gravar (commit)"
        con.commit()
    except ErroBanco as erro:
        # Qualquer erro: desfaz tudo (as tabelas e as linhas), mostra onde foi e termina com erro
        con.rollback()
        con.close()
        regra = getattr(getattr(erro, "diag", None), "constraint_name", None)
        print(f"\nERRO ao {etapa}" + (f": violou a regra {regra}" if regra else ""))
        print(f"   Detalhe do banco: {str(erro).strip().splitlines()[0]}")
        print("Nada foi gravado: o rollback desfez a carga inteira.")
        sys.exit(1)

    # 4) Conferencia: o que esta no banco tem que bater com a prova real (anexo 8 do enunciado)
    print("Conferencia:")
    for tabela, esperado in [("fato_item_contratado", 6126), ("dim_orgao", 363), ("dim_fornecedor", 2652),
                             ("dim_modalidade", 7), ("dim_localidade", 27)]:
        # Conta as linhas da tabela
        n = banco.consultar(con, f"SELECT COUNT(*) FROM {tabela}")[0][0]
        print(f"   {tabela}: {n} (esperado {esperado}) -> {'OK' if n == esperado else 'DIVERGENTE'}")
    con.close()


if __name__ == "__main__":
    main()
