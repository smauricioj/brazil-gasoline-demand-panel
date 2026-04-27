import os
from pathlib import Path
from matplotlib.pylab import beta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl


def confidence() -> None:
    # Carrega os dados
    df_forecast = pd.read_excel(
        Path.cwd() / "data_forecast.xlsx", sheet_name="forecast", header=4
    )

    df_betas = pd.read_excel(Path.cwd() / "fgls_results.xlsx", sheet_name="beta")

    df_covar = pd.read_excel(
        Path.cwd() / "fgls_results.xlsx", sheet_name="cov_matrix", index_col=0
    )

    # Filtra os anos de interesse
    df_forecast = df_forecast[df_forecast["Year"].isin([2030, 2040, 2050, 2060])]

    # Seleciona as colunas relevantes (ajuste os nomes conforme o seu Excel)
    X_cols = [
        "lnPriceG",
        "lnPriceG_L1",
        "lnPriceG_L2",
        "ln_Pe",
        "ln_l1_Pe",
        "ln_l2_Pe",
        "D_gdp_pc",
        "lnICEV",
        "lnEV",
        "ln_W_adj_Mi_e",
        "y2020",
        "IPI reduction",
        "d_NO",
        "d_NE",
        "d_SE",
        "d_CW",
    ]
    X = df_forecast[X_cols].copy()
    X["_cons"] = 1  # Termo constante

    b = df_betas["beta"].to_numpy()

    V = df_covar.to_numpy()

    # Simula vetores beta
    B_sim = np.random.multivariate_normal(mean=b, cov=V, size=1000)

    # Gera previsões
    predictions = np.dot(B_sim, X.T)

    # Calcula intervalos de confiança
    mean_pred = predictions.mean(axis=0)
    lower_ci = np.percentile(predictions, 2.5, axis=0)
    upper_ci = np.percentile(predictions, 97.5, axis=0)

    # Salva os resultados
    results = pd.DataFrame(
        {
            "Year": df_forecast["Year"].values,
            "Mean": np.exp(mean_pred),
            "CI 2.5%": np.exp(lower_ci),
            "CI 97.5%": np.exp(upper_ci),
        }
    )

    print(results)

    results.to_excel(
        Path.cwd() / "data" / "output" / "forecast_with_confidence_intervals.xlsx",
        index=False,
    )


def imagem_barras() -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Patch
    from matplotlib.ticker import FuncFormatter

    mpl.rcParams["font.family"] = "Times New Roman"
    mpl.rcParams["font.size"] = 14

    # Dados
    years = ["2040", "2050", "2060"]
    means = {
        "S6": np.array([62, 12, 9]),
        "S7": np.array([93, 59, 10]),
        "S8": np.array([97, 85, 55]),
    }
    errors = {
        "S6": [np.array([3, 2, 1]), np.array([4, 1, 2])],
        "S7": [np.array([3, 4, 1]), np.array([5, 3, 2])],
        "S8": [np.array([4, 4, 4]), np.array([4, 4, 3])],
    }

    # Cores e bordas
    colors = {
        "S6": "#2ca02c",  # verde
        "S7": "#ff7f0e",  # laranja
        "S8": "#1f77b4",  # azul
    }
    edge_colors = {"S6": "#1d7a1d", "S7": "#cc660c", "S8": "#165a90"}

    # Preparação do gráfico
    x = np.arange(len(years))
    width = 0.2

    _, ax = plt.subplots(figsize=(8.3, 5.8))  # A5 landscape in inches

    # Barras e whiskers
    for _, (scenario, offset) in enumerate(zip(means.keys(), [-width, 0, width])):
        ax.bar(
            x + offset,
            means[scenario],
            width,
            label=scenario,
            color=colors[scenario],
            edgecolor=edge_colors[scenario],
            linewidth=1.2,
            zorder=2,
        )
        ax.errorbar(
            x + offset,
            means[scenario],
            yerr=errors[scenario],
            fmt="none",
            ecolor="black",
            capsize=5,
            elinewidth=1.2,
            zorder=3,
        )

    # Configurações dos eixos
    ax.set_xlabel("Year")
    ax.set_ylabel("Gasoline sales per capita (relative to 2023)")
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_ylim(0, 105)
    ax.tick_params(axis="y", labelsize=14, direction="in")
    ax.tick_params(axis="x", labelsize=14, direction="in")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{int(y)}%"))
    plt.axvline(x=plt.xlim()[0], color="black", ls="-")

    # Legenda
    legend_elements = [
        Patch(facecolor=colors[k], edgecolor=edge_colors[k], label=k) for k in means
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.1),
        ncol=3,
        frameon=False,
    )

    # Grade e estilo visual
    ax.grid(True, axis="y", linestyle="--", linewidth=0.5, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    plt.savefig(
        Path.cwd() / "data" / "output" / "bar_scenario_compare.pdf", format="pdf"
    )
    plt.close()


def main() -> None:
    # confidence()
    imagem_barras()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    main()
