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
  (os itens 1.2 - datas e 1.3 - textos entram neste mesmo arquivo nas proximas tarefas)
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
def main():
    arquivos = {nome: ler(nome) for nome in ["compras", "itens", "resultados"]}
    print("## 1.1 Documentos (CNPJ/CPF)\n")
    print(auditar_documentos(arquivos["compras"], arquivos["resultados"]))
    print("## 1.1 Dinheiro e números\n")
    print(auditar_dinheiro(arquivos))


if __name__ == "__main__":
    main()
