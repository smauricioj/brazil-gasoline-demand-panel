from typing import Dict, Self
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from numpy import mean
import pandas as pd
import geopandas as gpd
from pathlib import Path
import mapclassify
from shapely.geometry.point import Point
from matplotlib_scalebar.scalebar import ScaleBar


class CloropethMap:

    __instance: Self = None

    @classmethod
    def get_instance(cls) -> Self:
        if not cls.__instance:
            cls.__instance = CloropethMap()
        return cls.__instance

    def __init__(self):
        self.__init_dataframes()
        # Estados
        self.__plot_kwds: Dict = dict(
            cmap="summer_r",
            edgecolor="blue",
            linewidth=0.5,
            linestyle="-",
            legend_kwds=dict(
                title=None,
                fmt="{:.2f}",
                interval=True,
                frameon=True,
                reverse=True,
                fontsize=11,
                loc="lower left",
            ),
        )
        # Regiões
        self.__plot_reg_kwds: Dict = dict(color="black", ls="-", lw=1)
        # Bussula
        x, y, arrow_length = 0.04, 0.9, 0.15
        self.__plot_bussula_kwds: Dict = dict(
            text="N",
            xy=(x, y),
            xytext=(x, y - arrow_length),
            arrowprops=dict(facecolor="black", width=4, headwidth=12),
            ha="center",
            va="center",
            fontsize=15,
        )
        # Escala
        points = gpd.GeoSeries(
            [Point(-73.5, 40.5), Point(-74.5, 40.5)], crs=4326
        )  # Geographic WGS 84 - degrees
        points = points.to_crs(32619)  # Projected WGS 84 - meters
        distance_meters = points[0].distance(points[1])
        self.__plot_escala_kwds: Dict = dict(
            dx=distance_meters, units="m", location="upper left"
        )

    def __init_dataframes(self) -> None:
        self.dados: pd.DataFrame = pd.read_csv(
            Path.cwd() / "data" / "input" / "data_tese.csv", encoding="utf-8", sep=","
        )

        self.malha_estadual: gpd.GeoDataFrame = gpd.read_file(
            Path.cwd() / "data" / "input" / "malha" / "malha_estadual_2021.shp"
        )
        self.malha_estadual["CD_UF"] = self.malha_estadual["CD_UF"].astype(int)

        self.malha_regional: gpd.GeoDataFrame = self.malha_estadual.dissolve(
            by="NM_REGIAO"
        ).reset_index()

        for df in [self.malha_regional, self.malha_estadual]:
            df["geometry"] = df["geometry"].simplify(
                tolerance=0.1, preserve_topology=True
            )

        self.estados: pd.DataFrame = pd.read_csv(
            Path.cwd() / "data" / "input" / "estados.csv",
            delimiter=";",
            usecols=["CD_UF", "X_TXT_OFF", "Y_TXT_OFF"],
            index_col="CD_UF",
            dtype={"X_TXT_OFF": float, "Y_TXT_OFF": float},
        )

        self.estados["TXT_OFF"] = list(
            zip(self.estados["X_TXT_OFF"], self.estados["Y_TXT_OFF"])
        )

        self.malha_estadual = (
            self.malha_estadual.set_index("CD_UF")
            .join(other=self.estados["TXT_OFF"])
            .to_crs(4326)
            .reset_index()
        )

    def __malha_com_coluna(self, dados: pd.Series) -> pd.DataFrame:
        return self.malha_estadual.set_index("CD_UF").join(other=dados).reset_index()

    def __agg_df(self, column: str, agg_method: str) -> pd.DataFrame:
        return self.__malha_com_coluna(
            dados=self.dados.groupby(by="i").agg(agg_method)[[column]]
        )

    def __year_df(self, column: str, year: int) -> pd.DataFrame:
        return self.__malha_com_coluna(
            dados=self.dados[self.dados["t"] == year].set_index("i")[[column]]
        )

    def plot(
        self,
        column: str,
        legend: bool,
        legend_title: str = None,
        file_name: str = None,
        year: int = 2021,
        ax: mpl.axes.Axes = None,
        compass: bool = False,
        scale: bool = False,
    ) -> mpl.axes.Axes:
        # Dados para plotar
        df = self.__year_df(column, year)

        # Estados com cores - usar UserDefined para forçar os bins exatos
        plot_kwds = self.__plot_kwds.copy()
        plot_kwds["column"] = column
        plot_kwds["scheme"] = "UserDefined"
        if ax:
            bins = mapclassify.Quantiles(self.dados[column], k=9).bins.tolist()
        else:
            bins = mapclassify.Quantiles(df[column], k=7).bins.tolist()
        plot_kwds["classification_kwds"] = {"bins": bins}
        plot_kwds["legend"] = legend

        if legend and legend_title:
            plot_kwds["legend_kwds"] = plot_kwds["legend_kwds"].copy()
            plot_kwds["legend_kwds"]["title"] = legend_title

        # Se ax foi fornecido, usar ele; senão o geopandas cria um novo
        if ax is not None:
            plot_kwds["ax"] = ax

        ax = df.plot(**plot_kwds)

        # IDS
        for _, row in df.iterrows():
            x = row.geometry.centroid.x + row.TXT_OFF[0]
            y = row.geometry.centroid.y + row.TXT_OFF[1]
            ax.text(x, y, row.SIGLA, fontsize=10)

        # Regiões
        self.malha_regional.boundary.plot(ax=ax, **self.__plot_reg_kwds)

        # Bussula
        if compass:
            ax.annotate(**self.__plot_bussula_kwds, xycoords=ax.transAxes)

        # Escala
        if scale:
            ax.add_artist(ScaleBar(**self.__plot_escala_kwds))

        # Ano
        if not file_name:
            ax.annotate(
                text=f"{year}",
                xy=(0.65, 0.14),
                fontsize=28,
                xycoords=ax.transAxes,
            )

        # Config
        ax.set_axis_off()

        # Se file_name foi fornecido e não há ax externo, salvar e fechar
        if file_name and ax.get_figure() == plt.gcf():
            plt.gcf().set_figwidth(5.5)
            plt.axis("equal")
            plt.tight_layout()
            plt.savefig(Path.cwd() / "data" / "output" / f"{file_name}.pdf", dpi=300)
            plt.close()

        return ax

    def plot_comparison(
        self,
        column: str,
        legend_title: str,
        file_name: str,
        year1: int = 2006,
        year2: int = 2021,
    ) -> None:
        """
        Plota dois mapas coropléticos em comparação (um acima do outro).

        Args:
            column: Nome da coluna a ser plotada
            legend_title: Título da legenda
            file_name: Nome do arquivo para salvar
            year1: Primeiro ano (padrão: 2006)
            year2: Segundo ano (padrão: 2021)
            norm: Se a escala deve ser normalizada
        """
        # Tamanho A4 em polegadas: 8.27 x 11.69 inches (210mm x 297mm)
        # _, (ax1, ax2) = plt.subplots(
        #     2, 1, figsize=(8.27, 11.69), constrained_layout=True
        # )
        _, (ax1, ax2) = plt.subplots(
            1, 2, figsize=(11.69, 8.27), constrained_layout=True
        )

        # Plotar mapa do primeiro ano
        self.plot(
            column=column,
            legend=False,
            year=year1,
            ax=ax1,
            compass=True,
            scale=True,
        )

        # Plotar mapa do segundo ano
        self.plot(
            column=column,
            legend=True,
            legend_title=legend_title,
            year=year2,
            ax=ax2,
        )

        # Ajustar aspecto dos mapas
        ax1.set_aspect("equal")
        ax2.set_aspect("equal")

        # Salvar figura
        plt.savefig(
            Path.cwd() / "data" / "output" / f"{file_name}.pdf",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()


def main() -> None:
    mpl.rcParams.update(
        {
            "font.size": 9,
            "font.family": "sans-serif",
            "text.usetex": True,
            "figure.dpi": 450,
        }
    )

    clp = CloropethMap.get_instance()

    # Comparação entre dois anos (2006 vs 2021) escala normalizada
    clp.plot_comparison(
        column="Sg_pc",
        legend_title="Gasoline sales $\\textit{per capita}$ (m³)",
        file_name="sales_percapita_comparison_2006_2023_norm",
        year1=2006,
        year2=2023,
    )


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    main()
