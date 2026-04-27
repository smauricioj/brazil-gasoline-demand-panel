# -*- coding: utf-8 -*-
# Autor: Sergio Prolo
# Data: 07/02/2024

from math import log
import os
from json import load
from pathlib import Path
from unidecode import unidecode

from urllib.request import urlopen
from urllib.parse import urlunparse

from pandas import DataFrame
from libpysal.weights import W
from esda.moran import Moran

import matplotlib as mpl
import pandas as pd
import numpy as np
import geopandas as gpd

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# GLOBALS ---------------------

ANO_INI = 2006
ANO_FIM = 2023

# UTILS -----------------------


def ipea_df(
    fname: str | Path, vname: str | None = None, lag: int | None = None
) -> DataFrame:
    if not vname:
        vname = fname
    if not lag:
        lag = 0
    if isinstance(fname, str):
        fname = Path.cwd() / "data" / "input" / "ipeadata" / f"{fname}.csv"
    df = (
        pd.read_csv(
            fname,
            sep=";",
            index_col=None,
            skiprows=1,
            decimal=",",
        )
        .dropna(axis=1, how="all")
        .drop(["Sigla", "Estado"], axis="columns")
        .set_index("Código")
        .stack()
        .reset_index()
        .rename({"level_1": "Ano", 0: vname}, axis=1)
    )
    df["Ano"] = df["Ano"].astype(int)
    df = df.query(f"Ano >= {ANO_INI-lag} & Ano <= {ANO_FIM-lag}").reset_index()
    if lag > 0:
        df["Ano"] += lag
    return df


def save_pattern(
    df: DataFrame,
    vars: str | list,
    order: list = ["Código", "Ano"],
    round: int = 4,
    new_name: str | list | None = None,
) -> DataFrame:
    """Salva os arquivos intermediários no mesmo padrão"""
    if new_name:
        if type(vars) != type(new_name):
            raise TypeError("Variáveis e nomes não batem")
    if isinstance(vars, str):
        vars = [vars]
        if new_name:
            new_name = [new_name]
    if len(order) != 2:
        raise TypeError("Duas ordens, pls")
    df[order[0]] = df[order[0]].astype(int)
    df[order[1]] = pd.to_datetime(df[order[1]], format="%Y")
    df = (
        df[order + vars]
        .round(round)
        .sort_values(order, ignore_index=True)
        .rename({order[0]: "i", order[1]: "t"}, axis="columns")
        .set_index(["i", "t"])
        .copy(deep=True)
    )
    if new_name:
        df = df.rename({old: new_name[i] for i, old in enumerate(vars)}, axis="columns")
    return df


def deflate(inf_df: DataFrame, lag: int = 0) -> DataFrame:
    """Deflaciona valores com base no IPCA"""
    # Opções de leitura de csv
    col_types = {"ANO": int, "IPCA": float}
    csv_kwargs = {
        "sep": ";",
        "usecols": col_types.keys(),
        "dtype": col_types,
        "engine": "c",
        "decimal": ",",
        "encoding": "utf-8",
        "parse_dates": ["ANO"],
    }
    df = (
        pd.read_csv(
            Path.cwd() / "data" / "input" / "inflação" / "inflacao_anual.csv",
            **csv_kwargs,
        )
        .query(f"ANO >= {ANO_INI-lag} and ANO <= {ANO_FIM-lag}")
        .reset_index()
    )

    # Índice de deflação
    df["IP"] = 1.0
    for i in range(1, len(df)):
        df.loc[i, "IP"] = df.loc[i - 1, "IP"] * (1 + (df.loc[i, "IPCA"] / 100.0))

    # Fator de deflacionamento
    df["FD"] = 1.0
    for i in range(0, len(df)):
        df.loc[i, "FD"] = df.loc[lag, "IP"] / df.loc[i, "IP"]

    df["ANO"] += pd.DateOffset(years=lag)
    vars = inf_df.columns.values
    inf_df = inf_df.join(df.rename(columns={"ANO": "t"}).set_index("t")["FD"])
    for var in vars:
        inf_df[var] *= inf_df["FD"]

    return inf_df.drop("FD", axis="columns").round(4)


def weighted_var(var: pd.Series, weights: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Multiplicação matricial entre distancias e vetor coluna"""
    return pd.DataFrame(weights.values @ var.values, index=var.index).rename(
        {0: f"{prefix}_{var.name}"}, axis="columns"
    )


def queen_matrix() -> None:
    """Matriz de adjacencias (feio, mas eu precisava fazer o quanto antes então...)"""

    df = pd.read_csv(
        Path.cwd() / "data" / "input" / "estrutura" / "estados.csv",
        sep=";",
        encoding="utf-8",
        dtype=str,
    )
    states = df["CD_UF"].astype(int).values
    N = len(states)

    dm = pd.DataFrame(data=np.full((N, N), 0), index=states, columns=states)

    def sym(df, i, j) -> DataFrame:
        df.at[i, j] = 1
        df.at[j, i] = 1
        return df

    # RO 11
    sym(dm, 11, 12)  # AC
    sym(dm, 11, 13)  # AM
    sym(dm, 11, 51)  # MT

    # AC 12
    sym(dm, 12, 13)  # AM

    # AM 13
    sym(dm, 13, 14)  # RR
    sym(dm, 13, 15)  # PA
    sym(dm, 13, 51)  # MT

    # RR 14
    sym(dm, 14, 15)  # PA

    # PA 15
    sym(dm, 15, 16)  # AP

    # AP 16

    # TO 17
    sym(dm, 17, 21)  # MA
    sym(dm, 17, 22)  # PI
    sym(dm, 17, 29)  # BA
    sym(dm, 17, 51)  # MT
    sym(dm, 17, 52)  # GO

    # 21 MA
    sym(dm, 21, 22)  # PI

    # 22 PI
    sym(dm, 22, 23)  # CE
    sym(dm, 22, 26)  # PE
    sym(dm, 22, 29)  # BA

    # 23 CE
    sym(dm, 23, 24)  # RN
    sym(dm, 23, 25)  # PB
    sym(dm, 23, 26)  # PE

    # 24 RN
    sym(dm, 24, 25)  # PB

    # 25 PB
    sym(dm, 25, 26)  # PE

    # 26 PE
    sym(dm, 26, 27)  # AL
    sym(dm, 26, 29)  # BA

    # 27 AL
    sym(dm, 27, 28)  # SE
    sym(dm, 27, 29)  # BA

    # 28 SE
    sym(dm, 28, 29)  # BA

    # 29 BA
    sym(dm, 29, 31)  # MG
    sym(dm, 29, 32)  # ES
    sym(dm, 29, 52)  # GO

    # 31 MG
    sym(dm, 31, 32)  # ES
    sym(dm, 31, 33)  # RJ
    sym(dm, 31, 35)  # SP
    sym(dm, 31, 50)  # MS
    sym(dm, 31, 52)  # GO
    sym(dm, 31, 53)  # DF

    # 32 ES
    sym(dm, 32, 33)  # RJ

    # 33 RJ
    sym(dm, 33, 35)  # SP

    # 35 SP
    sym(dm, 35, 50)  # MS
    sym(dm, 35, 41)  # PR

    # 41 PR
    sym(dm, 41, 42)  # SC
    sym(dm, 41, 50)  # MS

    # 42 SC
    sym(dm, 42, 43)  # RS

    # 43 RS

    # 50 MS
    sym(dm, 50, 51)  # MT
    sym(dm, 50, 52)  # GO

    # 51 MT
    sym(dm, 51, 52)  # GO

    # 52 GO
    sym(dm, 52, 53)  # DF

    dm.to_csv(Path.cwd() / "data" / "input" / "estrutura" / "adjacencias.csv")


def lagged_panel(df: pd.DataFrame) -> pd.DataFrame:
    l_df = df.unstack(level=0).shift(1)
    return l_df.fillna(value=l_df[1:3].mean()).stack()


# VARS ------------------------
def pop(raw: bool = False) -> DataFrame:
    """API do ibge"""
    cols = ["CD_UF", "NM_UF", "SIGLA"]
    df = pd.read_csv(
        Path.cwd() / "data" / "input" / "estrutura" / "estados.csv",
        usecols=cols,
        sep=";",
        encoding="utf-8",
        dtype=str,
    ).set_index("CD_UF")
    anos = list(range(ANO_INI, ANO_FIM + 1))
    if raw:
        url_parts = {
            "scheme": "https",
            "netloc": "servicodados.ibge.gov.br",
            "path": "/api/v3/agregados/6579/periodos/"
            + "|".join(str(ano) for ano in anos)
            + "/variaveis/9324",
            "params": "",
            "query": "localidades=N3[all]",
            "fragment": "",
        }
        print(urlunparse(url_parts.values()))
        with urlopen(urlunparse(url_parts.values())) as response:
            if response.status != 200:
                raise ConnectionError()
            data = load(response)[0]["resultados"][0]["series"]
    else:
        with open(Path.cwd() / "data" / "input" / "ibge" / "raw_pop.json") as file:
            data = load(file)[0]["resultados"][0]["series"]
    for ano in anos:
        # Em 2007, 2010, 2022 e 2023, não tem população aproximada
        if ano not in [2007, 2010, 2022, 2023]:
            df[ano] = {
                str(d["localidade"]["id"]): int(d["serie"][str(ano)]) for d in data
            }
        else:
            df[ano] = {str(d["localidade"]["id"]): np.nan for d in data}
    df = (
        df.drop(["NM_UF", "SIGLA"], axis="columns")
        .interpolate(method="linear", axis="columns")
        .round(0)
        .stack()
        .reset_index()
        .rename({f"level_1": "Ano", 0: "Pop"}, axis=1)
    )
    df["Pop"] = df["Pop"].astype(int)
    df["Ano"] = df["Ano"]
    return save_pattern(df=df, order=["CD_UF", "Ano"], vars="Pop", round=1)


def sales() -> DataFrame:
    """Arquivo mensal por estado da ANP"""
    prods = ["GASOLINA C"]
    df = (
        pd.read_csv(
            Path.cwd()
            / "data"
            / "input"
            / "vendas"
            / "vendas-combustiveis-m3-1990-2023.csv",
            sep=";",
            index_col=None,
            decimal=",",
        )
        .query(f"ANO >= {ANO_INI} and ANO <= {ANO_FIM} and PRODUTO in @prods")
        .groupby(["ANO", "PRODUTO", "UNIDADE DA FEDERAÇÃO"])
        .agg({"VENDAS": "sum"})
        .unstack(level=1)
        .reset_index()
    )
    df.columns = ["_".join(a).strip("_") for a in df.columns.to_flat_index()]
    df = df.rename(
        {
            "UNIDADE DA FEDERAÇÃO": "UF",
            "VENDAS_GASOLINA C": "Sg",
        },
        axis="columns",
    )
    df_estados = pd.read_csv(
        Path.cwd() / "data" / "input" / "estrutura" / "estados.csv",
        usecols=["NM_UF", "CD_UF"],
        index_col=None,
        sep=";",
        encoding="utf-8",
        dtype=str,
    )
    df_estados["NM_UF"] = df_estados["NM_UF"].apply(unidecode).str.lower()
    df["UF"] = df["UF"].apply(unidecode).str.lower()
    df = df.set_index("UF").join(df_estados.set_index("NM_UF")).reset_index()

    return save_pattern(
        df=df,
        order=["CD_UF", "ANO"],
        vars=["Sg"],
        round=2,
    )


def prices(lag: int = 0) -> DataFrame:
    """Dois arquivos da anp separados por ano"""
    df_pre = pd.read_excel(
        Path.cwd() / "data" / "input" / "preços" / "prec_pre_2013.xlsx",
        index_col=None,
        decimal=".",
        thousands=",",
        skiprows=12,
        usecols=["MÊS", "PRODUTO", "ESTADO", "PREÇO MÉDIO REVENDA"],
    )
    df_pos = pd.read_excel(
        Path.cwd() / "data" / "input" / "preços" / "prec_pos_2013.xlsx",
        index_col=None,
        decimal=".",
        thousands=",",
        skiprows=16,
        usecols=["MÊS", "PRODUTO", "ESTADO", "PREÇO MÉDIO REVENDA"],
    )
    df_pos["PRODUTO"] = df_pos["PRODUTO"].replace("OLEO DIESEL", "ÓLEO DIESEL")
    df = pd.concat([df_pre, df_pos], ignore_index=True)
    df["ANO"] = df["MÊS"].dt.year
    df = df.drop("MÊS", axis="columns")
    df = (
        df.query(f"ANO >= {ANO_INI - lag} and ANO <= {ANO_FIM - lag}")
        .groupby(["ANO", "PRODUTO", "ESTADO"])
        .agg({"PREÇO MÉDIO REVENDA": "mean"})
        .unstack(level=1)
        .reset_index()
    )
    df["ANO"] += lag
    df.columns = ["_".join(a).strip("_") for a in df.columns.to_flat_index()]
    df = df.rename(
        {
            "PREÇO MÉDIO REVENDA_GASOLINA COMUM": "Pg",
            "PREÇO MÉDIO REVENDA_ETANOL HIDRATADO": "Pe",
            "PREÇO MÉDIO REVENDA_ÓLEO DIESEL": "Pd",
        },
        axis="columns",
    )
    df_states = pd.read_csv(
        Path.cwd() / "data" / "input" / "estrutura" / "estados.csv",
        sep=";",
        encoding="utf-8",
        dtype=str,
    )
    df_states["NM_UF"] = df_states["NM_UF"].apply(unidecode).str.upper()
    df = (
        df[["ESTADO", "ANO", "Pg", "Pe", "Pd"]]
        .set_index("ESTADO")
        .join(df_states[["NM_UF", "CD_UF"]].set_index("NM_UF"))
        .reset_index()
        .drop("ESTADO", axis="columns")
    )
    return save_pattern(
        df=df,
        order=["CD_UF", "ANO"],
        vars=["Pg", "Pe", "Pd"],
        round=2,
    )


def fleet() -> DataFrame:
    """Arquivos anuais da frota em dezembro do Senatran"""
    dfs: list[pd.DataFrame] = []
    for ano in range(ANO_INI, ANO_FIM + 1):
        df: pd.DataFrame = (
            pd.read_excel(
                Path.cwd() / "data" / "input" / "frota" / f"f{ano}.xlsx",
                index_col=None,
                decimal=".",
                thousands=",",
                skiprows=2,
                skipfooter=7,
                usecols=["UF", "AUTOMÓVEL", "MOTOCICLETA"],
            )
            .dropna()
            .reset_index(drop=True)
        )
        df["ANO"] = [ano for _ in range(len(df))]
        dfs.append(df)

    df = pd.concat(dfs).reset_index(drop=True)
    df["UF"] = df["UF"].str.strip(" ")
    df = (
        df[["UF", "ANO", "AUTOMÓVEL", "MOTOCICLETA"]]
        .rename({"AUTOMÓVEL": "Vc", "MOTOCICLETA": "Vm"}, axis="columns")
        .set_index("UF")
        .join(
            pd.read_csv(
                Path.cwd() / "data" / "input" / "estrutura" / "estados.csv",
                usecols=["NM_UF", "CD_UF"],
                index_col="NM_UF",
                sep=";",
                encoding="utf-8",
                dtype=str,
            )
        )
        .reset_index()
        .drop("UF", axis="columns")
    )
    return save_pattern(
        df=df,
        order=["CD_UF", "ANO"],
        vars=["Vc", "Vm"],
        round=0,
    )


def electric_share(pop: pd.Series) -> DataFrame:
    electric_stock: pd.DataFrame = pd.read_csv(
        Path.cwd() / "data" / "input" / "anfavea" / "electric.csv"
    )
    ipea_var: str = "gdp"
    weights: pd.DataFrame = ipea_df(ipea_var).rename({ipea_var: "w"}, axis="columns")
    weights["Ano"] = weights["Ano"].astype(int)
    pop = pop.reset_index().rename({"i": "Código", "t": "Ano"}, axis="columns")
    pop["Ano"] = pop["Ano"].dt.year
    weights = weights.set_index(["Código", "Ano"]).join(
        pop.set_index(["Código", "Ano"])
    )
    weights["w"] /= weights["Pop"]
    weights = weights.drop("Pop", axis="columns").reset_index()
    weights = weights.set_index("Ano").join(
        weights.groupby("Ano").agg({"w": "sum"}).rename({"w": "total"}, axis="columns")
    )
    weights["w"] /= weights["total"]
    weights = weights.join(electric_stock.set_index("t")).reset_index()
    weights["Ve"] = (weights["Ve"] * weights["w"]).astype(int)
    return save_pattern(
        df=weights,
        order=["Código", "Ano"],
        vars="Ve",
        round=1,
    )


def FGLS_stats_replace() -> None:
    """Atualiza os status do FGLS (espero não usar mais)"""
    df: pd.DataFrame = pd.read_csv(
        Path.cwd() / "stata" / "FGLS_stats.csv",
    )
    results: pd.DataFrame = pd.read_csv(
        Path.cwd() / "stata" / "FGLS_stats_fmt.csv",
        sep=";",
        header=None,
        dtype=float,
        decimal=".",
    )
    df["Variance"] = results[0]
    df["Autocorrelation"] = results[1]
    df = df.set_index("CD_UF")
    df.to_csv(Path.cwd() / "stata" / "FGLS_stats.csv")


# FUNCS -----------------------


def local_data() -> None:
    """Usando para fazer apenas uma imagem"""
    df = sales()
    df = df.join(pop(raw=False))
    df["Sg_pc"] = df["Sg"] / df["Pop"]
    df["Se_pc"] = df["Se"] / df["Pop"]
    df = df.join(deflate(prices()))
    df = df.reset_index()
    df["t"] = df["t"].dt.year
    df = df.set_index(["i", "t"])
    df.to_csv(
        Path.cwd() / "data" / "output" / "data_tese.csv",
        encoding="utf-8",
        sep=",",
        date_format="%Y",
    )


def total_data() -> None:
    """Captura todas as variáveis e salva tdo em um arquivo só"""
    # Vendas
    df = sales()

    # População
    df = df.join(pop(raw=False))

    # Vendas per capita
    df["Sg_pc"] = df["Sg"] / df["Pop"]

    # Frota e IM
    df = df.join(fleet())
    df = df.join(electric_share(df["Pop"].copy(deep=True)))
    df["V"] = df["Vm"] + df["Vc"] - df["Ve"]
    df["Mi_c"] = df["V"] / df["Pop"]
    df["Mi_e"] = (1000 * df["Ve"]) / df["Pop"]
    df = df.drop(["Vc", "Vm"], axis="columns")

    # Preços
    df = df.join(deflate(prices()))
    for lag in [1, 2]:
        df = df.join(
            deflate(prices(lag), lag).add_prefix(prefix=f"l{lag}_", axis="columns")
        )
    df = df.join(save_pattern(df=ipea_df(fname="gdp", lag=0), vars="gdp"))
    df = df.join(
        save_pattern(df=ipea_df(fname="gdp", lag=1), vars="gdp").rename(
            {"gdp": "l1_gdp"}, axis="columns"
        )
    )
    df["gdp_pc"] = df["gdp"] / df["Pop"]
    df["l1_gdp_pc"] = df["l1_gdp"] / df["Pop"]
    df = df.drop(["gdp", "l1_gdp"], axis="columns")

    # Coisas dos indices
    df = df.reset_index()
    df["t"] = df["t"].dt.year
    df = df.set_index(["i", "t"])

    # Salva
    df.to_csv(
        Path.cwd() / "data" / "output" / "data_2023.csv",
        encoding="utf-8",
        sep=",",
        date_format="%Y",
    )


def distance_matrix(conf: dict) -> None:
    """Calculando as distancias"""

    def dist_matrix_constructor(states: np.array, years: np.array) -> pd.DataFrame:
        """Matriz quadrada com base nos estados e anos dos dados"""
        N, T = len(states), len(years)
        prod_index = pd.MultiIndex.from_product([states, years], names=["i", "t"])
        return pd.DataFrame(
            data=np.full((N * T, N * T), 0.0), index=prod_index, columns=prod_index
        )

    # Vars
    OUTPUT = Path.cwd() / "data" / "output"

    # Ler dados originais
    queen = pd.read_csv(
        Path.cwd() / "data" / "input" / "estrutura" / f"adjacencias.csv",
        encoding="utf-8",
        sep=",",
        index_col=0,
    )
    data = pd.read_csv(
        Path.cwd() / "data" / "output" / f"data_2023.csv",
        encoding="utf-8",
        sep=",",
        date_format="%Y",
    )
    # Dimensões
    states = np.unique(data["i"].values)  # 1,2,...,N
    years = np.unique(data["t"].values)  # 1,2,...,T
    data = data.set_index(["i", "t"])
    # Matriz normalizada
    data = (data - data.min()) / (data.max() - data.min())

    # Matrizes vão ser salvas a partir de um dicionário
    dms: dict = dict()

    ## Adjacencias
    # Construção
    dm = dist_matrix_constructor(states, years)
    for i in dm.index.values:
        for j in dm.columns.values:
            dm.at[i, j] = np.abs((queen.at[i[0], str(j[0])]))
    # Padronização
    dm = ((dm.T / dm.T.sum()).T) * len(years)
    # Salva
    dms["adjacent"] = dm.copy(deep=True)
    # Salva
    with pd.ExcelWriter(OUTPUT / f"distances.xlsx") as w:
        for df_name, df in dms.items():
            df.to_excel(w, sheet_name=df_name)
    return None


def stata_data() -> None:
    """Dados para regressão usando Stata"""

    # Matrizes de distâncias
    dm = pd.read_excel(
        Path.cwd() / "data" / "output" / f"distances.xlsx",
        sheet_name=None,
        header=[0, 1],
        index_col=[0, 1],
    )

    # Dados
    data = pd.read_csv(
        Path.cwd() / "data" / "output" / f"data_2023.csv",
        encoding="utf-8",
        sep=",",
        date_format="%Y",
    ).set_index(["i", "t"])

    # Interações
    interactions = {"Mi_e": ["adjacent"]}
    for var, interaction in interactions.items():
        for theme in interaction:
            data = data.join(
                weighted_var(var=data[var], weights=dm[theme], prefix=f"W_{theme[:3]}")
            )

    # Colunas para regressão
    cols = [
        "Sg_pc",
        "Pg",
        "l1_Pg",
        "l2_Pg",
        "Pe",
        "l1_Pe",
        "l2_Pe",
        "Mi_e",
        "W_adj_Mi_e",
        "Mi_c",
        "gdp_pc",
        "l1_gdp_pc",
    ]

    data = data[cols]

    # Logaritmos
    data = np.log(data.replace(to_replace=0, value=0.00001)).add_prefix("ln_")

    # Salva
    with pd.ExcelWriter(Path.cwd() / "stata_scripts" / "data_stata_pre.xlsx") as w:
        data.to_excel(excel_writer=w, merge_cells=False)


# MAIN -----------------------
def main() -> None:
    total_data()
    stata_data()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    main()
