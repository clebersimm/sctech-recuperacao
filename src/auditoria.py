"""
auditoria.py  -  CONTAR OS PROBLEMAS DOS DADOS BRUTOS   (Sprint 1)
====================================================================
Este script NAO corrige nada. Ele so le os 3 arquivos de data/raw/ e CONTA quantos registros tem cada problema.
Os numeros que ele mostra sao os mesmos que estao na secao "Auditoria dos dados" do README.md.

COMO RODAR:   python -m src.auditoria
A saida ja sai em formato de tabela markdown, pronta para copiar para o README.

COMO FUNCIONA (passo a passo)
-----------------------------
1. Os arquivos sao lidos TUDO COMO TEXTO (dtype=str), do mesmo jeito que no montar_tabelas.py.
   Assim o CNPJ nao perde o zero da esquerda na leitura e "N/A" nao vira vazio sozinho:
   vemos o dado exatamente como ele veio.
2. Para cada coluna, o script faz perguntas de "sim ou nao" a cada registro
   (ex.: "este CNPJ tem ponto ou traco?") e soma quantos responderam "sim".
   Essas perguntas sao feitas com EXPRESSOES REGULARES: um molde que descreve um formato de texto.
   Exemplo: r"\\d+,\\d+"  quer dizer "digitos, uma virgula, digitos"  ->  combina com "12,5".
3. Um mesmo registro pode ter mais de um problema (ex.: "R$ 1.234,56" tem R$ E milhar no padrao BR),
   por isso as colunas de uma tabela NAO devem ser somadas entre si.
   A excecao sao as colunas de FORMATO do numero (ponto decimal, so virgula, BR, US, milhar sem decimal):
   cada registro cai em um formato so, e a soma delas da o total de registros.

O QUE ESTA AUDITADO AQUI
------------------------
- Item 1.1: documentos (CNPJ/CPF) e dinheiro/numeros.   -> funcoes auditar_documentos() e auditar_dinheiro()
- Item 1.2: formatos de data e homologacao antes da publicacao.
                                                         -> funcoes auditar_formatos_data() e auditar_datas_invertidas()
- Item 1.3: vazios disfarcados, acentos quebrados, caracteres invisiveis e nomes escritos de jeitos diferentes.
                                -> funcoes auditar_vazios(), auditar_acentos_invisiveis(), exemplos_acento()
                                   e auditar_grafias()
- Item 1.4: a lista resumida de todos os problemas.     -> funcao resumo() (e a primeira tabela da saida)
"""

import re

import pandas as pd

from src import config

# Textos que significam "sem valor" (comparados em MAIUSCULAS). E a mesma lista do src/limpeza.py,
# mais o texto vazio. Aqui ela so serve para CONTAR, nao para limpar.
NULOS = {"", "N/A", "NULL", "NONE", "NAN", "-", "0", "SEM INFORMAÇÃO", "SEM INFORMACAO",
         "NÃO INFORMADO", "NAO INFORMADO", "NÃO SE APLICA", "NAO SE APLICA"}

# Espaco comum, TAB ou NBSP (\xa0, o espaco "sem quebra" que vem de sistemas antigos) no comeco ou no fim do texto
ESPACO_NAS_PONTAS = re.compile(r"^[\s\xa0]|[\s\xa0]$")

# Tamanho certo de cada tipo de documento: PJ = CNPJ (14 digitos), PF = CPF (11 digitos).
# PE (estrangeiro) nao tem tamanho fixo e NAO deve ganhar zeros.
TAMANHO_DOCUMENTO = {"PJ": 14, "PF": 11}


def ler(nome):
    """Le um CSV de data/raw/ tudo como texto, sem transformar nada."""
    return pd.read_csv(config.PASTA_RAW / f"{nome}.csv", dtype=str, keep_default_na=False)


def tabela_markdown(cabecalho, linhas):
    """Monta uma tabela markdown a partir de uma lista de cabecalho e de uma lista de linhas.
    Numeros inteiros saem com ponto de milhar no padrao brasileiro (1633 -> 1.633)."""
    def fmt(valor):
        return f"{valor:,}".replace(",", ".") if isinstance(valor, int) else str(valor)
    texto = "| " + " | ".join(cabecalho) + " |\n"
    texto += "|" + "---|" * len(cabecalho) + "\n"
    for linha in linhas:
        texto += "| " + " | ".join(fmt(v) for v in linha) + " |\n"
    return texto


# ---------------------------------------------------------------------------------------------
# ITEM 1.1 (parte 1) - DOCUMENTOS: CNPJ / CPF
# ---------------------------------------------------------------------------------------------
def contar_documento(coluna, tipo_pessoa=None):
    """Conta os problemas de uma coluna de documento e devolve um dicionario {problema: quantidade}.

    coluna      -> a coluna de texto com o CNPJ/CPF (ex.: resultados["ni_fornecedor"])
    tipo_pessoa -> a coluna com PJ/PF/PE, quando existir. Sem ela (caso do orgao), todo documento e CNPJ.

    Como cada problema e reconhecido:
    - mascara ............ tem ponto, barra ou traco ("51.593.855/0001-04")
    - espacos ............ comeca ou termina com espaco/NBSP (" 41428781000105 ")
    - zero perdido ....... depois de tirar tudo que nao e digito, sobram MENOS digitos que o tamanho certo.
                           Acontece quando alguem abriu o arquivo numa planilha e o CNPJ virou numero:
                           "01222333000181" vira 1222333000181 (o zero da esquerda some)
    - digitos demais ..... sobram MAIS digitos que o tamanho certo (documento impossivel)
    """
    sem_espaco = coluna.str.strip(" \xa0\t")
    digitos = coluna.str.replace(r"\D", "", regex=True)          # \D = tudo que NAO e digito
    qtd_digitos = digitos.str.len()

    if tipo_pessoa is None:                                       # documento de orgao: sempre CNPJ
        tipo_pessoa = pd.Series("PJ", index=coluna.index)
    tamanho_certo = tipo_pessoa.map(TAMANHO_DOCUMENTO)            # PE fica sem tamanho (NaN)
    eh_pj, eh_pf, eh_pe = tipo_pessoa == "PJ", tipo_pessoa == "PF", tipo_pessoa == "PE"

    # Documento "limpo" (so para medir quantos fornecedores/orgaos diferentes existem de verdade)
    limpo = digitos.copy()
    limpo[eh_pj] = digitos[eh_pj].str.zfill(14)
    limpo[eh_pf] = digitos[eh_pf].str.zfill(11)
    limpo[eh_pe] = sem_espaco[eh_pe].str.upper()

    # Um mesmo documento limpo aparece com mais de um tipo de pessoa? (a "mistura de tipos" do desafio 1)
    tipos_por_documento = pd.DataFrame({"doc": limpo, "tipo": tipo_pessoa}).groupby("doc")["tipo"].nunique()

    return {
        "Total de registros": len(coluna),
        "Vazio ou nulo disfarçado (N/A, -, ...)": int(sem_espaco.str.upper().isin(NULOS).sum()),
        "Com máscara (pontos, barra, traço)": int(sem_espaco.str.contains(r"[./-]").sum()),
        "Com espaços sobrando nas pontas": int(coluna.str.contains(ESPACO_NAS_PONTAS).sum()),
        "CNPJ com zeros perdidos no começo (PJ)": int((eh_pj & (qtd_digitos > 0) & (qtd_digitos < 14)).sum()),
        "CPF com zeros perdidos no começo (PF)": int((eh_pf & (qtd_digitos > 0) & (qtd_digitos < 11)).sum()),
        "Com dígitos demais": int((qtd_digitos > tamanho_certo).sum()),
        "PJ com 11 dígitos (tamanho de CPF)": int((eh_pj & (qtd_digitos == 11)).sum()),
        "Estrangeiros (PE), não recebem zeros": int(eh_pe.sum()),
        "Mesmo documento com tipos de pessoa diferentes": int((tipos_por_documento > 1).sum()),
        "Documentos distintos antes de limpar": int(coluna.nunique()),
        "Documentos distintos depois de limpar": int(limpo.nunique()),
    }


def auditar_documentos(compras, resultados):
    """Monta a tabela de documentos: uma coluna para o orgao e outra para o fornecedor."""
    orgao = contar_documento(compras["cnpj_orgao"])
    fornecedor = contar_documento(resultados["ni_fornecedor"], resultados["tipo_pessoa"])
    linhas = [[problema, orgao[problema], fornecedor[problema]] for problema in orgao]
    return tabela_markdown(["Problema", "compras.cnpj_orgao", "resultados.ni_fornecedor"], linhas)


# ---------------------------------------------------------------------------------------------
# ITEM 1.1 (parte 2) - DINHEIRO E NUMEROS ESCRITOS COMO TEXTO
# ---------------------------------------------------------------------------------------------
# Formatos do numero, olhando so para o "miolo" (sem R$ e sem espacos). Cada registro cai em UM so formato.
FORMATOS_NUMERO = {
    "Ponto decimal (1234.56)": r"\d+\.\d+",
    "Só vírgula decimal (12,5)": r"\d+,\d+",
    "BR com milhar (1.234,56)": r"\d{1,3}(\.\d{3})+,\d+",
    "US com milhar (1,234.56)": r"\d{1,3}(,\d{3})+\.\d+",
    "Milhar sem decimal (1.234.567)": r"\d{1,3}([.,]\d{3}){2,}",
    "Inteiro sem separador (1234)": r"\d+",
}

# Colunas de dinheiro e quantidade de cada arquivo (as quantidades tambem vem com R$!)
COLUNAS_NUMERICAS = {
    "compras": ["valor_total_estimado", "valor_total_homologado"],
    "itens": ["quantidade", "valor_unitario_estimado", "valor_total_estimado"],
    "resultados": ["quantidade_homologada", "valor_unitario_homologado", "valor_total_homologado"],
}


def contar_numero(coluna):
    """Conta os problemas de uma coluna de dinheiro/numero e devolve um dicionario {problema: quantidade}.

    Primeiro o texto e "descascado": troca o NBSP por espaco, tira o R$ e os espacos. O que sobra e o miolo
    ("R$\\xa01.234,56 " -> "1.234,56"), e e nele que se reconhece o formato.

    - ambiguo ........ um ponto OU uma virgula sozinho seguido de exatamente 3 digitos ("1.500", "1,500").
                       Poderia ser mil e quinhentos ou um e meio. A regra do enunciado diz: separador sozinho
                       e SEMPRE decimal, entao vale 1,5. Esses registros ja estao contados no ponto/virgula decimal.
    - negativo ....... entre parenteses "(1.500,00)" ou com sinal de menos no comeco ou no fim
    - fora do padrao . nao se encaixa em nenhum formato conhecido nem e nulo disfarcado (deve ser 0)
    """
    texto = coluna.str.replace("\xa0", " ").str.strip()
    miolo = texto.str.replace("R$", "", regex=False).str.replace(" ", "")

    resultado = {
        "Total": len(coluna),
        "Com R$": int(texto.str.contains("R$", regex=False).sum()),
        "Espaços sobrando": int(coluna.str.contains(r"^[\s\xa0]|[\s\xa0]$|\xa0").sum()),
    }
    reconhecido = texto.str.upper().isin(NULOS - {"0"})           # aqui o "0" e numero, nao nulo
    for nome, molde in FORMATOS_NUMERO.items():
        combina = miolo.str.fullmatch(molde)
        resultado[nome] = int(combina.sum())
        reconhecido |= combina
    negativo = miolo.str.contains(r"^\(.*\)$|^-|-$")
    reconhecido |= negativo
    resultado["Ambíguo (1.500)"] = int(miolo.str.fullmatch(r"\d{1,3}[.,]\d{3}").sum())
    resultado["Negativo"] = int(negativo.sum())
    resultado["Zero"] = int(miolo.str.fullmatch(r"0+([.,]0+)?").sum())
    resultado["Vazio ou nulo disfarçado"] = int(texto.str.upper().isin(NULOS - {"0"}).sum())
    resultado["Fora do padrão"] = int((~reconhecido).sum())
    return resultado


def auditar_dinheiro(arquivos):
    """Monta a tabela de dinheiro/numeros: uma linha por coluna numerica dos 3 arquivos."""
    linhas, cabecalho = [], None
    for nome_arquivo, colunas in COLUNAS_NUMERICAS.items():
        for coluna in colunas:
            contagem = contar_numero(arquivos[nome_arquivo][coluna])
            cabecalho = cabecalho or ["Coluna"] + list(contagem)
            linhas.append([f"{nome_arquivo}.{coluna}"] + list(contagem.values()))
    return tabela_markdown(cabecalho, linhas)


# ---------------------------------------------------------------------------------------------
# ITEM 1.2 - DATAS: FORMATOS MISTURADOS E HOMOLOGACAO ANTES DA PUBLICACAO
# ---------------------------------------------------------------------------------------------
# Cada formato de data tem: (nome que aparece na tabela, molde para reconhecer, formato para ler a data).
# No formato de leitura, %d = dia, %m = mes, %Y = ano com 4 digitos, %H:%M = hora e minuto.
# Os formatos que comecam pelo dia sao lidos como padrao brasileiro: DIA antes do MES.
FORMATOS_DATA = [
    ("ISO com hora (2025-01-06T11:51:06)", r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S"),
    ("ISO (2025-10-31)", r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
    ("BR com hora (02/01/2025 09:03)", r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", "%d/%m/%Y %H:%M"),
    ("BR (03/01/2025)", r"\d{2}/\d{2}/\d{4}", "%d/%m/%Y"),
    ("Com pontos (02.01.2025)", r"\d{2}\.\d{2}\.\d{4}", "%d.%m.%Y"),
    ("Com traços (02-01-2025)", r"\d{2}-\d{2}-\d{4}", "%d-%m-%Y"),
    ("Ano primeiro com barras (2025/01/08)", r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
    ("Compacto (20250103)", r"\d{8}", "%Y%m%d"),
]

# Colunas de data de cada arquivo
COLUNAS_DATA = {
    "compras": ["data_publicacao", "data_abertura_proposta", "data_encerramento_proposta"],
    "resultados": ["data_resultado", "data_cancelamento"],
}


def ler_datas(coluna):
    """Transforma uma coluna de texto em datas (sem a hora), testando formato por formato.
    Devolve (datas, formato): 'datas' e a coluna ja convertida (NaT quando nao deu para ler)
    e 'formato' diz em qual formato cada registro foi reconhecido (vazio quando nenhum serviu).
    Nao altera os arquivos: so serve para a contagem."""
    texto = coluna.str.replace("\xa0", " ").str.strip()
    # "datetime64[s]" guarda a data em segundos: assim cabem anos absurdos como 9999, que existem na base
    datas = pd.Series(pd.NaT, index=coluna.index, dtype="datetime64[s]")
    formato = pd.Series("", index=coluna.index)
    for nome, molde, leitura in FORMATOS_DATA:
        combina = texto.str.fullmatch(molde) & (formato == "")      # so quem ainda nao achou o formato
        formato[combina] = nome
        # errors="coerce": se a data for impossivel (31/02/2025), vira NaT em vez de dar erro
        datas[combina] = pd.to_datetime(texto[combina], format=leitura, errors="coerce").astype("datetime64[s]")
    return datas.dt.normalize(), formato                            # normalize() tira a hora


def contar_data(coluna):
    """Conta os formatos e os problemas de uma coluna de data e devolve um dicionario {problema: quantidade}.

    - vazio ............ texto vazio ou nulo disfarcado ("N/A", "-")
    - impossivel ....... o formato e conhecido, mas a data nao existe (ex.: 31/02/2025)
    - ano absurdo ...... ano fora de 2000 a 2030 (ex.: 0001-01-01), a mesma faixa usada no src/limpeza.py
    - fora do padrao ... preenchido, mas nao se encaixa em nenhum dos formatos conhecidos (deve ser 0)
    """
    texto = coluna.str.replace("\xa0", " ").str.strip()
    vazio = texto.str.upper().isin(NULOS)
    datas, formato = ler_datas(coluna)
    reconhecido = formato != ""

    resultado = {"Total": len(coluna), "Vazio": int(vazio.sum())}
    for nome, _, _ in FORMATOS_DATA:
        resultado[nome] = int((formato == nome).sum())
    resultado["Data impossível"] = int((reconhecido & datas.isna()).sum())
    resultado["Ano fora de 2000-2030"] = int(((datas.dt.year < 2000) | (datas.dt.year > 2030)).sum())
    resultado["Fora do padrão"] = int((~vazio & ~reconhecido).sum())
    resultado["Data mais antiga"] = datas.min().strftime("%d/%m/%Y") if datas.notna().any() else "-"
    resultado["Data mais nova"] = datas.max().strftime("%d/%m/%Y") if datas.notna().any() else "-"
    return resultado


def auditar_formatos_data(arquivos):
    """Monta a tabela de formatos de data: uma COLUNA da tabela para cada coluna de data dos arquivos
    (a tabela fica 'deitada', com os formatos nas linhas, para caber na tela)."""
    contagens = {f"{arq}.{col}": contar_data(arquivos[arq][col])
                 for arq, colunas in COLUNAS_DATA.items() for col in colunas}
    problemas = list(next(iter(contagens.values())))
    linhas = [[p] + [contagens[c][p] for c in contagens] for p in problemas]
    return tabela_markdown(["Formato / problema"] + [f"`{c}`" for c in contagens], linhas)


def auditar_datas_invertidas(compras, itens, resultados):
    """Conta as homologacoes (resultados.data_resultado) com data ANTERIOR a publicacao do edital
    (compras.data_publicacao). Compara so o dia, sem a hora: homologar no mesmo dia da publicacao e valido.

    A contagem e feita em 4 niveis, porque cada etapa do projeto olha para um deles:
    - todos os resultados ........................ o arquivo bruto inteiro
    - resultados nao cancelados .................. os que podem ser escolhidos como vencedor (regra 2)
    - itens com pelo menos 1 resultado invertido . quantos itens podem ficar sem data de homologacao (regra 7)
    - contratacoes ............................... quantos editais tem o problema
    O numero final de itens SEM data de homologacao na fato so e conhecido na Sprint 3,
    depois de escolher o vencedor de cada item."""
    publicacao, _ = ler_datas(compras["data_publicacao"])
    homologacao, _ = ler_datas(resultados["data_resultado"])
    tabela = pd.DataFrame({
        "numero_controle_pncp": resultados["numero_controle_pncp"],
        "numero_item": resultados["numero_item"],
        "homologacao": homologacao,
        "cancelado": resultados["data_cancelamento"].str.strip() != "",
    }).merge(pd.DataFrame({"numero_controle_pncp": compras["numero_controle_pncp"], "publicacao": publicacao}),
             on="numero_controle_pncp", how="left")
    tabela["invertida"] = tabela["homologacao"] < tabela["publicacao"]
    tabela["mesmo_dia"] = tabela["homologacao"] == tabela["publicacao"]
    tabela["dias"] = (tabela["publicacao"] - tabela["homologacao"]).dt.days

    invertidas = tabela[tabela["invertida"]]
    validos = tabela[~tabela["cancelado"]]
    itens_invertidos = invertidas[["numero_controle_pncp", "numero_item"]].drop_duplicates()
    linhas = [
        ["Resultados com homologação antes da publicação", int(tabela["invertida"].sum()), len(tabela)],
        ["... entre os resultados não cancelados", int(validos["invertida"].sum()), len(validos)],
        ["Itens com pelo menos 1 resultado invertido", len(itens_invertidos), len(itens)],
        ["Contratações com pelo menos 1 resultado invertido",
         int(invertidas["numero_controle_pncp"].nunique()), len(compras)],
        ["Resultados homologados no mesmo dia da publicação (válidos, ciclo de 0 dia)",
         int(tabela["mesmo_dia"].sum()), len(tabela)],
        ["Resultados sem data de publicação ou de homologação para comparar",
         int((tabela["homologacao"].isna() | tabela["publicacao"].isna()).sum()), len(tabela)],
    ]
    texto = tabela_markdown(["Situação", "Registros", "De um total de"], linhas)
    if len(invertidas):
        texto += (f"\nQuanto antes da publicação: de {int(invertidas['dias'].min())} a "
                  f"{int(invertidas['dias'].max())} dias (mediana de {int(invertidas['dias'].median())} dia(s)).\n")
    return texto


# ---------------------------------------------------------------------------------------------
# ITEM 1.3 - TEXTO: VAZIOS DISFARCADOS, ACENTOS QUEBRADOS, CARACTERES INVISIVEIS E NOMES REPETIDOS
# ---------------------------------------------------------------------------------------------
# Colunas que NAO sao texto livre: as de dinheiro/numero e as de data ja foram auditadas nos itens 1.1 e 1.2.
# Nelas o "0" e um numero de verdade, por isso ficam de fora da contagem de vazios disfarcados.
COLUNAS_NAO_TEXTO = {col for cols in COLUNAS_NUMERICAS.values() for col in cols} | \
                    {col for cols in COLUNAS_DATA.values() for col in cols}

# Acento quebrado: o texto foi gravado em UTF-8 e lido como Latin-1, entao "ç" vira "Ã§" e "ã" vira "Ã£".
# O sinal e um "Ã" ou "Â" seguido de um caractere da faixa \x80-\xBF (onde ficam "§", "£", "©", "º"...).
ACENTO_QUEBRADO = re.compile(r"[ÃÂ][\x80-\xbf]")

# Caracteres invisiveis ou que "sujam" o texto sem aparecer na tela
INVISIVEIS = {
    "NBSP (espaço sem quebra, \\xa0)": "\xa0",
    "TAB": "\t",
    "Quebra de linha dentro do texto": "\n",
    "Largura zero (\\u200b, \\u200c, \\u200d, \\ufeff)": "[​‌‍﻿]",
}


def consertar_acento(texto):
    """Mesma ideia da funcao do src/limpeza.py: desfaz a leitura errada (Latin-1 -> UTF-8).
    Se o texto nao tem o problema, devolve como estava. Aqui so serve para medir o efeito da correcao."""
    try:
        return texto.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def nome_padrao(coluna):
    """Versao 'padronizada' de um nome, so para comparar grafias: sem invisiveis, acento consertado,
    MAIUSCULAS, hifen com espaco dos dois lados e um unico espaco entre as palavras (as mesmas regras do
    padronizar_nome() do src/limpeza.py).   '  Comando  da Aeronautica\\xa0' -> 'COMANDO DA AERONAUTICA'"""
    return (coluna.str.replace(r"[​‌‍﻿]", "", regex=True)
                  .map(consertar_acento)
                  .str.upper()
                  .str.replace("-", " - ", regex=False)
                  .str.split().str.join(" "))


def auditar_vazios(arquivos):
    """Conta os vazios disfarcados em TODAS as colunas de texto dos 3 arquivos.
    Um registro e vazio disfarcado quando, sem espacos nas pontas e em MAIUSCULAS, esta na lista NULOS
    ("N/A", "NULL", "-", "0", "SEM INFORMAÇÃO", "NÃO INFORMADO", "NÃO SE APLICA"...).
    O vazio de verdade (texto "") e contado a parte. So aparecem na tabela as colunas que tem algum dos dois."""
    linhas = []
    for nome_arquivo, df in arquivos.items():
        for coluna in df.columns:
            if coluna in COLUNAS_NAO_TEXTO:
                continue
            chave = df[coluna].str.replace("\xa0", " ").str.strip().str.upper()
            vazio = chave == ""
            disfarcado = chave.isin(NULOS - {""})
            if vazio.any() or disfarcado.any():
                valores = df.loc[disfarcado, coluna].str.strip().value_counts()
                exemplos = ", ".join(f"`{v}` ({n})" for v, n in valores.items())
                linhas.append([f"`{nome_arquivo}.{coluna}`", len(df), int(vazio.sum()),
                               int(disfarcado.sum()), exemplos or "-"])
    return tabela_markdown(["Coluna", "Total", "Vazio de verdade", "Vazio disfarçado",
                            "Valores encontrados (quantidade)"], linhas)


def auditar_acentos_invisiveis(arquivos):
    """Conta, em cada coluna de texto, os registros com acento quebrado e com cada tipo de caractere invisivel.
    Tambem conta os espacos sobrando (nas pontas ou repetidos no meio). So aparecem as colunas com algum problema."""
    linhas = []
    for nome_arquivo, df in arquivos.items():
        for coluna in df.columns:
            if coluna in COLUNAS_NAO_TEXTO:
                continue
            texto = df[coluna]
            contagem = [int(texto.str.contains(ACENTO_QUEBRADO).sum())]
            contagem += [int(texto.str.contains(molde).sum()) for molde in INVISIVEIS.values()]
            contagem.append(int(texto.str.contains(r"^[ \xa0\t]|[ \xa0\t]$| {2,}").sum()))
            if any(contagem):
                linhas.append([f"`{nome_arquivo}.{coluna}`", len(df)] + contagem)
    return tabela_markdown(["Coluna", "Total", "Acento quebrado"] + list(INVISIVEIS) + ["Espaços sobrando"], linhas)


def exemplos_acento(arquivos, limite=5):
    """Mostra alguns exemplos de acento quebrado e como ficam depois de consertados."""
    linhas = []
    for nome_arquivo, df in arquivos.items():
        for coluna in df.columns:
            if coluna in COLUNAS_NAO_TEXTO:
                continue
            quebrados = df[coluna][df[coluna].str.contains(ACENTO_QUEBRADO)]
            if len(quebrados):
                # pega so a primeira palavra quebrada, para o exemplo ficar curto
                palavra = quebrados.iloc[0].split()
                palavra = next(p for p in palavra if ACENTO_QUEBRADO.search(p))
                linhas.append([f"`{nome_arquivo}.{coluna}`", f"`{palavra}`", f"`{consertar_acento(palavra)}`"])
    return tabela_markdown(["Coluna", "Como está", "Depois de consertar"], linhas[:limite])


def auditar_grafias(compras, resultados):
    """O mesmo orgao ou fornecedor escrito de jeitos diferentes.

    Para cada documento (CNPJ/CPF ja limpo do jeito do item 1.1), conta quantas grafias do nome existem:
    - 'como veio' ........... o texto exatamente como esta no arquivo
    - 'depois de padronizar'  o texto com acento consertado, em MAIUSCULAS e sem espacos sobrando
    Se depois de padronizar sobra so 1 nome por documento, a padronizacao resolve o problema.

    Tambem conta o caso contrario, importante para o ranking de orgaos (pergunta 4): o MESMO nome padronizado
    com VARIOS CNPJ (unidades diferentes do mesmo orgao)."""
    doc_orgao = compras["cnpj_orgao"].str.replace(r"\D", "", regex=True).str.zfill(14)
    digitos = resultados["ni_fornecedor"].str.replace(r"\D", "", regex=True)
    tipo = resultados["tipo_pessoa"]
    doc_forn = digitos.copy()
    doc_forn[tipo == "PJ"] = digitos[tipo == "PJ"].str.zfill(14)
    doc_forn[tipo == "PF"] = digitos[tipo == "PF"].str.zfill(11)
    doc_forn[tipo == "PE"] = resultados["ni_fornecedor"][tipo == "PE"].str.strip(" \xa0\t").str.upper()

    casos = [
        ("Órgão (`razao_social_orgao` por CNPJ)", doc_orgao, compras["razao_social_orgao"]),
        ("Unidade (`nome_unidade` por CNPJ)", doc_orgao, compras["nome_unidade"]),
        ("Fornecedor (`nome_fornecedor` por CNPJ/CPF)", doc_forn, resultados["nome_fornecedor"]),
    ]
    linhas = []
    for nome, documento, coluna in casos:
        bruto = pd.DataFrame({"doc": documento, "nome": coluna}).groupby("doc")["nome"].nunique()
        padrao = pd.DataFrame({"doc": documento, "nome": nome_padrao(coluna)}).groupby("doc")["nome"].nunique()
        linhas.append([nome, len(bruto), int((bruto > 1).sum()), int((padrao > 1).sum()),
                       int(coluna.nunique()), int(nome_padrao(coluna).nunique())])
    texto = tabela_markdown(["Caso", "Documentos distintos", "Com mais de 1 grafia (como veio)",
                             "Com mais de 1 grafia (depois de padronizar)", "Nomes distintos (como veio)",
                             "Nomes distintos (depois de padronizar)"], linhas)

    # Mesmo nome padronizado, varios CNPJ (unidades do mesmo orgao)
    por_nome = pd.DataFrame({"doc": doc_orgao, "nome": nome_padrao(compras["razao_social_orgao"])}) \
        .groupby("nome")["doc"].nunique().sort_values(ascending=False)
    texto += (f"\nÓrgãos (nome padronizado) com mais de 1 CNPJ: {int((por_nome > 1).sum())} de {len(por_nome)}. "
              f"Maiores: " + ", ".join(f"{n} ({q} CNPJ)" for n, q in por_nome.head(3).items()) + ".\n")
    return texto


# ---------------------------------------------------------------------------------------------
# ITEM 1.4 - RESUMO: A LISTA DE TODOS OS PROBLEMAS E QUANTOS REGISTROS CADA UM AFETA
# ---------------------------------------------------------------------------------------------
def resumo(arquivos):
    """Junta as contagens dos itens 1.1, 1.2 e 1.3 numa lista unica: uma linha por problema.
    Nao conta nada novo: usa as mesmas funcoes de contagem acima e SOMA o resultado das colunas onde o problema
    aparece. A ultima coluna diz em que Sprint o problema e tratado.

    'Registros afetados' e a soma das colunas: se um registro tem o problema em 2 colunas, conta 2 vezes."""
    compras, resultados = arquivos["compras"], arquivos["resultados"]
    orgao = contar_documento(compras["cnpj_orgao"])
    forn = contar_documento(resultados["ni_fornecedor"], resultados["tipo_pessoa"])
    numeros = {f"{a}.{c}": contar_numero(arquivos[a][c]) for a, cols in COLUNAS_NUMERICAS.items() for c in cols}
    datas = {f"{a}.{c}": contar_data(arquivos[a][c]) for a, cols in COLUNAS_DATA.items() for c in cols}

    def soma_numeros(chave):
        return sum(c[chave] for c in numeros.values())

    # Texto: soma as colunas de texto dos 3 arquivos
    vazios = acentos = invisiveis = 0
    for df in arquivos.values():
        for coluna in df.columns:
            if coluna in COLUNAS_NAO_TEXTO or coluna in ("cnpj_orgao", "ni_fornecedor"):
                continue                                  # documentos ja foram contados no item 1.1
            texto = df[coluna]
            vazios += int(texto.str.replace("\xa0", " ").str.strip().str.upper().isin(NULOS - {""}).sum())
            acentos += int(texto.str.contains(ACENTO_QUEBRADO).sum())
            invisiveis += int(texto.str.contains("|".join(INVISIVEIS.values())).sum())

    # Datas fora do formato ISO (aaaa-mm-dd), so nas duas datas que vao para a fato
    fora_iso = sum(datas[c]["Total"] - datas[c]["ISO com hora (2025-01-06T11:51:06)"] - datas[c]["ISO (2025-10-31)"]
                   for c in ["compras.data_publicacao", "resultados.data_resultado"])

    # Nomes: reaproveita a mesma logica do item 1.3
    doc_orgao = compras["cnpj_orgao"].str.replace(r"\D", "", regex=True).str.zfill(14)
    grafias_orgao = pd.DataFrame({"d": doc_orgao, "n": compras["razao_social_orgao"]}).groupby("d")["n"].nunique()
    nomes_varios_cnpj = pd.DataFrame({"d": doc_orgao, "n": nome_padrao(compras["razao_social_orgao"])}) \
        .groupby("n")["d"].nunique()
    digitos = resultados["ni_fornecedor"].str.replace(r"\D", "", regex=True)
    tipo = resultados["tipo_pessoa"]
    doc_forn = digitos.where(tipo != "PJ", digitos.str.zfill(14)).where(tipo != "PF", digitos.str.zfill(11))
    doc_forn = doc_forn.where(tipo != "PE", resultados["ni_fornecedor"].str.strip(" \xa0\t").str.upper())
    grafias_forn = pd.DataFrame({"d": doc_forn, "n": resultados["nome_fornecedor"]}).groupby("d")["n"].nunique()

    invertidas = auditar_datas_invertidas(compras, arquivos["itens"], resultados)
    qtd_invertidas = int(re.search(r"antes da publicação \| ([\d.]+)", invertidas).group(1).replace(".", ""))

    linhas = [
        ["1", "CNPJ/CPF com máscara (pontos, barra, traço)", "`cnpj_orgao`, `ni_fornecedor`",
         orgao["Com máscara (pontos, barra, traço)"] + forn["Com máscara (pontos, barra, traço)"], "Sprint 2"],
        ["1", "CNPJ/CPF com espaços sobrando", "`cnpj_orgao`, `ni_fornecedor`",
         orgao["Com espaços sobrando nas pontas"] + forn["Com espaços sobrando nas pontas"], "Sprint 2"],
        ["1", "CNPJ/CPF com zeros perdidos no começo", "`cnpj_orgao`, `ni_fornecedor`",
         orgao["CNPJ com zeros perdidos no começo (PJ)"] + forn["CNPJ com zeros perdidos no começo (PJ)"]
         + forn["CPF com zeros perdidos no começo (PF)"], "Sprint 2"],
        ["2", "Dinheiro e quantidade com `R$`", "8 colunas de valor e quantidade", soma_numeros("Com R$"), "Sprint 2"],
        ["2", "Dinheiro e quantidade com espaços sobrando (inclui NBSP)", "8 colunas de valor e quantidade",
         soma_numeros("Espaços sobrando"), "Sprint 2"],
        ["2", "Número fora do padrão ponto decimal (vírgula decimal, BR com milhar, US com milhar, milhar repetido)",
         "8 colunas de valor e quantidade",
         sum(soma_numeros(k) for k in ["Só vírgula decimal (12,5)", "BR com milhar (1.234,56)",
                                       "US com milhar (1,234.56)", "Milhar sem decimal (1.234.567)"]), "Sprint 2"],
        ["2", "Número ambíguo (`1.500`, vale 1,5 pela regra)", "valores unitários e totais",
         soma_numeros("Ambíguo (1.500)"), "Sprint 2"],
        ["2", "Valor negativo (entre parênteses ou com sinal)", "8 colunas de valor e quantidade",
         soma_numeros("Negativo"), "não ocorre"],
        ["3", "Data fora do formato ISO (`aaaa-mm-dd`)", "`data_publicacao`, `data_resultado`", fora_iso, "Sprint 2"],
        ["3", "Homologação antes da publicação do edital", "`data_resultado` × `data_publicacao`",
         qtd_invertidas, "Sprint 3 (regra 7)"],
        ["3", "Ano absurdo (2035 a 9999, Credenciamento)", "`data_encerramento_proposta`",
         datas["compras.data_encerramento_proposta"]["Ano fora de 2000-2030"], "não vai para a fato"],
        ["4", "Vazio disfarçado (N/A, NULL, -, 0, Não se aplica, Não Informado…)", "6 colunas de texto",
         vazios, "Sprint 2"],
        ["5", "Acento quebrado (`Ã§`, `Ã£`)", "5 colunas de texto", acentos, "Sprint 2"],
        ["5", "Caractere invisível (NBSP, TAB, quebra de linha, largura zero)", "colunas de texto", invisiveis,
         "Sprint 2"],
        ["5", "Órgão com o nome escrito de jeitos diferentes (CNPJ)", "`razao_social_orgao`",
         int((grafias_orgao > 1).sum()), "Sprint 2"],
        ["5", "Fornecedor com o nome escrito de jeitos diferentes (CNPJ/CPF)", "`nome_fornecedor`",
         int((grafias_forn > 1).sum()), "Sprint 2 e 3"],
        ["5", "Mesmo nome de órgão com vários CNPJ (unidades)", "`razao_social_orgao`",
         int((nomes_varios_cnpj > 1).sum()), "Sprint 5 (agrupar pelo nome)"],
    ]
    return tabela_markdown(["Desafio", "Problema", "Onde aparece", "Registros afetados", "Tratado em"], linhas)


# ---------------------------------------------------------------------------------------------
def main():
    arquivos = {nome: ler(nome) for nome in ["compras", "itens", "resultados"]}
    print("## 1.4 Resumo dos problemas\n")
    print(resumo(arquivos))
    print("## 1.1 Documentos (CNPJ/CPF)\n")
    print(auditar_documentos(arquivos["compras"], arquivos["resultados"]))
    print("## 1.1 Dinheiro e números\n")
    print(auditar_dinheiro(arquivos))
    print("## 1.2 Formatos de data\n")
    print(auditar_formatos_data(arquivos))
    print("## 1.2 Homologação antes da publicação\n")
    print(auditar_datas_invertidas(arquivos["compras"], arquivos["itens"], arquivos["resultados"]))
    print("## 1.3 Vazios disfarçados\n")
    print(auditar_vazios(arquivos))
    print("## 1.3 Acentos quebrados e caracteres invisíveis\n")
    print(auditar_acentos_invisiveis(arquivos))
    print(exemplos_acento(arquivos))
    print("## 1.3 Mesmo órgão ou fornecedor escrito de jeitos diferentes\n")
    print(auditar_grafias(arquivos["compras"], arquivos["resultados"]))


if __name__ == "__main__":
    main()
