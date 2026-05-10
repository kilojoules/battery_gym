"""Stress-test figures: 2-D heatmap, quantile-vs-persistence, SLP comparison."""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np


CAPEX_E = 100_000
CAPEX_P = 75_000
DISC = sum((1.07) ** -y for y in range(15))
B_P_DEFAULT = 1.0


def lifetime_npv(R, b_E, b_P=B_P_DEFAULT):
    return R * DISC - CAPEX_E * b_E - CAPEX_P * b_P


# -----------------------------------------------------------------------------
# 2-D heatmap from results_2d/*.json
# -----------------------------------------------------------------------------
def figure_2d_heatmap(out: str = "fig_paper_2d.png"):
    files = sorted(glob.glob("results_2d/2d_*.json"))
    if not files:
        print("no results_2d files; skipping")
        return
    bymyp = {}
    for fp in files:
        r = json.load(open(fp))
        bP, bE = r["b_P"], r["b_E"]
        for src, ye_dict in r["by_market"].items():
            for year, pol_dict in ye_dict.items():
                for pol, vals in pol_dict.items():
                    npv = lifetime_npv(vals["R"], bE, bP)
                    bymyp.setdefault((src, year, pol), {})[(bP, bE)] = npv

    bP_grid = sorted({k[0] for d in bymyp.values() for k in d.keys()})
    bE_grid = sorted({k[1] for d in bymyp.values() for k in d.keys()})

    panels = [(s, y) for s in ["dk1", "ercot"] for y in ["2021", "2022", "2023"]]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
    for i, (src, year) in enumerate(panels):
        ax = axes[i // 3, i % 3]
        # Use QP-ensemble NPV surface
        d = bymyp.get((src, year, "quadratic_ensemble"), {})
        if not d:
            ax.axis("off"); continue
        Z = np.zeros((len(bP_grid), len(bE_grid)))
        for ip, bP in enumerate(bP_grid):
            for ib, bE in enumerate(bE_grid):
                Z[ip, ib] = d.get((bP, bE), np.nan) / 1e6
        im = ax.pcolormesh(bE_grid, bP_grid, Z, shading="nearest", cmap="viridis")
        # Mark argmaxes for each policy
        markers = {"linear_single": ("o", "white"), "linear_ensemble": ("s", "yellow"),
                    "quadratic_single": ("D", "magenta"), "quadratic_ensemble": ("^", "red")}
        for pol, (mk, color) in markers.items():
            d2 = bymyp.get((src, year, pol), {})
            if d2:
                best = max(d2.items(), key=lambda kv: kv[1])
                ax.plot(best[0][1], best[0][0], marker=mk, color=color,
                        ms=10, mew=1.5, mec="black", label=pol[:9])
        ax.set_xscale("log")
        ax.set_yscale("log")
        market_label = "DK1" if src == "dk1" else "ERCOT N."
        ax.set_title(f"{market_label} {year}")
        if i // 3 == 1:
            ax.set_xlabel(r"$b_E$ (MWh)")
        if i % 3 == 0:
            ax.set_ylabel(r"$b_P$ (MW)")
        plt.colorbar(im, ax=ax, label="NPV (M)")
        if i == 0:
            ax.legend(fontsize=7, loc="lower right")
    fig.suptitle("2-D NPV surfaces (QP-ensemble dispatch). Markers: argmax per policy. Colocation -> argmax invariant.", y=1.02)
    fig.tight_layout()
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(f"Wrote {out}")


# -----------------------------------------------------------------------------
# Quantile-vs-persistence comparison
# -----------------------------------------------------------------------------
def figure_quantile_vs_persistence(out: str = "fig_paper_quantile.png"):
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    panels = [(s, y) for s in ["dk1", "ercot"] for y in [2021, 2022, 2023]]
    for i, (src, year) in enumerate(panels):
        ax = axes[i // 3, i % 3]
        # Persistence
        try:
            if src == "dk1":
                p = json.load(open(f"paper_{year}.json"))
                ye_p = p["by_year"][str(year)]
            else:
                p = json.load(open("paper_ercot.json"))
                ye_p = p["by_year"][str(year)]
        except FileNotFoundError:
            ax.axis("off"); continue
        # Quantile
        try:
            q = json.load(open(f"results_quantile/{src}_{year}.json"))
            ye_q = q["by_year"][str(year)]
        except FileNotFoundError:
            ye_q = None
        for label, ye, ls in [("persistence-K=4", ye_p, "-"),
                                 ("quantile-K=20", ye_q, "--")]:
            if ye is None: continue
            for cost, color in [("linear", "#cc6677"), ("quadratic", "#4477aa")]:
                rows_s = ye[f"{cost}_single"]
                rows_e = ye[f"{cost}_ensemble"]
                bE = np.array([r["b_E"] for r in rows_s])
                R_s = np.array([r["R"] for r in rows_s])
                R_e = np.array([r["R"] for r in rows_e])
                npv_s = np.array([lifetime_npv(R, b) for R, b in zip(R_s, bE)])
                npv_e = np.array([lifetime_npv(R, b) for R, b in zip(R_e, bE)])
                ax.plot(bE, npv_s / 1e6, color=color, ls=ls, alpha=0.55, lw=1.0)
                ax.plot(bE, npv_e / 1e6, color=color, ls=ls, lw=2.0,
                        label=f"{cost}-ens {label}" if i == 0 else None)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_xscale("log")
        market_label = "DK1" if src == "dk1" else "ERCOT N."
        ax.set_title(f"{market_label} {year}", fontsize=10)
        if i // 3 == 1:
            ax.set_xlabel(r"$b_E$ (MWh)")
        if i % 3 == 0:
            ax.set_ylabel("NPV (M, 15y, 7%)")
        ax.grid(alpha=0.3)
        if i == 0:
            ax.legend(fontsize=7)
    fig.suptitle("Persistence-K=4 (solid) vs Quantile-K=20 (dashed) ensembles. DK1 2022 quantile breaks invariance.", y=1.005)
    fig.tight_layout()
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(f"Wrote {out}")


# -----------------------------------------------------------------------------
# SLP comparison
# -----------------------------------------------------------------------------
def figure_slp(out: str = "fig_paper_slp.png"):
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    panels = [(s, y) for s in ["dk1", "ercot"] for y in [2021, 2022, 2023]]
    for i, (src, year) in enumerate(panels):
        ax = axes[i // 3, i % 3]
        try:
            if src == "dk1":
                p = json.load(open(f"paper_{year}.json"))
                ye_p = p["by_year"][str(year)]
            else:
                p = json.load(open("paper_ercot.json"))
                ye_p = p["by_year"][str(year)]
        except FileNotFoundError:
            ax.axis("off"); continue
        try:
            s_data = json.load(open(f"results_slp/{src}_{year}.json"))
            ye_slp = s_data["by_year"][str(year)]
        except FileNotFoundError:
            ye_slp = None
        # Plot QP-single, QP-ensemble, SLP
        for key, color, label in [("quadratic_single", "#cc6677", "QP-single"),
                                   ("quadratic_ensemble", "#4477aa", "QP-ens K=4 lag")]:
            rows = ye_p[key]
            bE = np.array([r["b_E"] for r in rows])
            npv = np.array([lifetime_npv(r["R"], b) for r, b in zip(rows, bE)])
            ax.plot(bE, npv / 1e6, "-", color=color, lw=2,
                     label=label if i == 0 else None)
        if ye_slp:
            rows = ye_slp.get("quadratic_slp", [])
            bE = np.array([r["b_E"] for r in rows])
            npv = np.array([lifetime_npv(r["R"], b) for r, b in zip(rows, bE)])
            ax.plot(bE, npv / 1e6, "D-", color="#117733", lw=2,
                     label="SLP rolling N=50" if i == 0 else None, ms=6)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_xscale("log")
        market_label = "DK1" if src == "dk1" else "ERCOT N."
        ax.set_title(f"{market_label} {year}", fontsize=10)
        if i // 3 == 1:
            ax.set_xlabel(r"$b_E$ (MWh)")
        if i % 3 == 0:
            ax.set_ylabel("NPV (M, 15y, 7%)")
        ax.grid(alpha=0.3)
        if i == 0:
            ax.legend(fontsize=8)
    fig.suptitle("SLP rolling-window dispatch vs full-horizon QP-single + QP-ensemble. SLP NPV is lower (rolling vs perfect-foresight gap) but $b_E^*$ matches.", y=1.005)
    fig.tight_layout()
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(f"Wrote {out}")


if __name__ == "__main__":
    figure_2d_heatmap()
    figure_quantile_vs_persistence()
    figure_slp()
