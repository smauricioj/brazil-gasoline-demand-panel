import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from pathlib import Path


os.chdir(os.path.dirname(os.path.realpath(__file__)))

# ── Data ──────────────────────────────────────────────────────────────────────
data = {
    "SIGLA": [
        "RO",
        "AC",
        "AM",
        "RR",
        "PA",
        "AP",
        "TO",
        "MA",
        "PI",
        "CE",
        "RN",
        "PB",
        "PE",
        "AL",
        "SE",
        "BA",
        "MG",
        "ES",
        "RJ",
        "SP",
        "PR",
        "SC",
        "RS",
        "MS",
        "MT",
        "GO",
        "DF",
    ],
    "sigma": [
        0.028272428,
        0.037075564,
        0.043542843,
        0.048828349,
        0.027161859,
        0.040092234,
        0.043023501,
        0.030837322,
        0.029989334,
        0.035185255,
        0.025197597,
        0.026058933,
        0.042090777,
        0.050784107,
        0.027699662,
        0.04852109,
        0.059558894,
        0.043489426,
        0.065305524,
        0.085534595,
        0.069328867,
        0.056063801,
        0.027906774,
        0.038154967,
        0.079445727,
        0.068600796,
        0.045714077,
    ],
    "rho": [
        0.69170743,
        0.64969057,
        0.91871452,
        0.9421007,
        0.79491878,
        0.72732532,
        0.85814005,
        0.88261569,
        0.87431186,
        0.94621211,
        0.49093872,
        0.63557994,
        0.8348977,
        0.42666453,
        0.51734591,
        0.869367,
        0.8888064,
        0.78261179,
        0.99124587,
        0.71418482,
        0.76503348,
        0.75056648,
        0.22441961,
        0.74716151,
        0.87497932,
        0.70854372,
        0.90451354,
    ],
    "region": [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
    ],
}
df = pd.DataFrame(data)

# ── Standardize ───────────────────────────────────────────────────────────────
scaler = StandardScaler()
X = scaler.fit_transform(df[["sigma", "rho"]])

# ── Elbow + Silhouette ────────────────────────────────────────────────────────
# wcss, sil = [], []
# K_range = range(2, 8)
# for k in K_range:
#     km = KMeans(n_clusters=k, random_state=42, n_init=50)
#     km.fit(X)
#     wcss.append(km.inertia_)
#     sil.append(silhouette_score(X, km.labels_))

# fig, axes = plt.subplots(1, 2, figsize=(10, 4))
# axes[0].plot(K_range, wcss, "o-", color="steelblue")
# axes[0].set_xlabel("Number of clusters $k$")
# axes[0].set_ylabel("Within-cluster sum of squares")
# axes[0].set_title("Elbow criterion")
# axes[1].plot(K_range, sil, "s-", color="darkorange")
# axes[1].set_xlabel("Number of clusters $k$")
# axes[1].set_ylabel("Silhouette score")
# axes[1].set_title("Silhouette criterion")
# plt.tight_layout()
# plt.savefig(Path.cwd() / "data" / "output" / "elbow_silhouette.png", dpi=150)
# plt.close()
# print("WCSS by k:", dict(zip(K_range, [round(w, 3) for w in wcss])))
# print("Silhouette by k:", dict(zip(K_range, [round(s, 3) for s in sil])))

# ── Fit preferred k (try 2 and 3) ─────────────────────────────────────────────
for k in [3]:
    km = KMeans(n_clusters=k, random_state=42, n_init=50)
    df[f"cluster_k{k}"] = km.fit_predict(X)
    centers = scaler.inverse_transform(km.cluster_centers_)
    print(f"\n── k={k} cluster centers (original scale) ──")
    for i, c in enumerate(centers):
        members = df[df[f"cluster_k{k}"] == i]["SIGLA"].tolist()
        print(f"  Cluster {i}: sigma={c[0]:.4f}, rho={c[1]:.4f}  →  {members}")

# ── Scatter plot for k=3 ──────────────────────────────────────────────────────
k = 3
colors = sns.color_palette("tab10", n_colors=k)
labels_map = {0: "High-inertia regime", 1: "Responsive regime", 2: "Volatile regime"}
markers_map = {0: "o", 1: "s", 2: "^"}

fig, ax = plt.subplots(figsize=(8, 6))
for i, row in df.iterrows():
    c = colors[row[f"cluster_k{k}"]]
    ax.scatter(
        row["rho"],
        row["sigma"],
        color=c,
        s=60,
        zorder=3,
        marker=markers_map[row[f"cluster_k{k}"]],
    )
    ax.annotate(
        row["SIGLA"],
        (row["rho"], row["sigma"]),
        textcoords="offset points",
        xytext=(5, -7),
        fontsize=9,
        color=c,
    )

patches = [mpatches.Patch(color=colors[i], label=labels_map[i]) for i in range(k)]
patches = [
    mlines.Line2D(
        [],
        [],
        color=colors[i],
        marker=markers_map[i],
        markersize=10,
        label=labels_map[i],
        ls="None",
    )
    for i in range(k)
]
ax.legend(handles=patches, frameon=True, fontsize=11, loc="upper left")
ax.set_xlabel(r"$\hat{\rho}_s$ [s.u.]", fontsize=12)
ax.set_ylabel(r"$\hat{\sigma}_s$ [ln(m³)]", fontsize=12)
ax.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(Path.cwd() / "data" / "output" / "scatter_sigma_rho_clusters.pdf", dpi=300)
plt.close()
print("\nPlots saved.")
