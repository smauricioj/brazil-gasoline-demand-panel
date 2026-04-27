import pandas as pd
import numpy as np
from pathlib import Path
import os

# ── Parâmetros da equação de Gompertz ──────────────────────────────────────────
A = 1.798
B = -0.096


def gompertz_scrappage(age: int) -> float:
    """
    Fração acumulada de veículos sucateados com uma dada idade (anos).
    S(t) = exp( -exp( a + b*t ) )

    Comportamento:
      - age = 0  → S ≈ 0.002  (quase nenhum veículo sucateado)
      - age → ∞  → S → 1.0   (todos sucateados)
    A frota sobrevivente de uma coorte é (1 − S(age)).
    """
    return np.exp(-np.exp(A + B * age))


# ── Leitura dos dados ──────────────────────────────────────────────────────────
os.chdir(os.path.dirname(os.path.realpath(__file__)))
print(Path.cwd())
df = pd.read_csv(Path.cwd() / "data" / "input" / "licenciamentos.csv")

fuel_types = ["Gasoline", "Ethanol", "Flex", "Electric"]

# Substitui "-" por 0 e converte para numérico
for col in fuel_types:
    df[col] = (
        pd.to_numeric(
            df[col].astype(str).str.strip().replace("-", "0"), errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

years = df["t"].values

# ── Cálculo da frota circulante ────────────────────────────────────────────────
# Para cada ano-calendário Y e tipo de combustível i:
#   Fr_i(Y) = Σ_{a ≤ Y}  V_ia · (1 − S(Y − a))
#
# onde (Y − a) é a idade da coorte emplacada no ano (a).

results = {"Ano": years}

for fuel in fuel_types:
    fleet_per_year = []

    for Y in years:
        total = 0.0
        # Itera sobre todas as coortes emplacadas até o ano Y
        for _, row in df[df["t"] <= Y].iterrows():
            V_ia = row[fuel]
            if V_ia == 0:
                continue
            age = Y - row["t"]  # idade da coorte no ano Y
            S = gompertz_scrappage(age)  # fração já sucateada
            total += V_ia * (1 - S)  # sobreviventes da coorte

        fleet_per_year.append(round(total))

    results[f"Frota_{fuel}"] = fleet_per_year

result_df = pd.DataFrame(results)
result_df["Frota_Total"] = result_df[[f"Frota_{f}" for f in fuel_types]].sum(axis=1)

# ── Saída ──────────────────────────────────────────────────────────────────────
output_path = Path.cwd() / "data" / "input" / "frota_circulante.csv"
result_df.to_csv(output_path, index=False)

print(result_df.to_string(index=False))
print(f"\nResultados salvos em: {output_path}")
