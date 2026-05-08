"""Generate paper figures from paper_results.json artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np


CAPEX_E = 100_000   # EUR/MWh
CAPEX_P = 75_000    # EUR/MW
DISCOUNT = 0.07
LIFETIME = 15
B_P = 1.0


def lifetime_npv(R_year: float, b_E: float, b_P: float = B_P) -> float:
    df_sum = sum((1 + DISCOUNT) ** -y for y in range(LIFETIME))
    return R_year * df_sum - CAPEX_E * b_E - CAPEX_P * b_P


def load_results(*paths) -> dict:
    """Merge paper_results JSONs from multiple files."""
    merged = {"meta": {}, "by_year": {}}
    for p in paths:
        with open(p) as f:
            r = json.load(f)
        if not merged["meta"]:
            merged["meta"] = r["meta"]
        merged["by_year"].update(r["by_year"])
    return merged


def figure_revenue_vs_bE(merged: dict, out: str = "fig_paper_revenue.png"):
    years = sorted(merged["by_year"].keys())
    fig, axes = plt.subplots(1, len(years), figsize=(5 * len(years), 4.5),
                              sharey=False)
    if len(years) == 1:
        axes = [axes]
    cmap = {
        "linear_single":   ("#aaaaaa", "o", "LP-linear single"),
        "linear_ensemble": ("#117733", "s", "LP-linear K=4-lag"),
        "quadratic_single": ("#cc6677", "D", "QP-quadratic single"),
        "quadratic_ensemble": ("#4477aa", "^", "QP-quadratic K=4-lag"),
    }
    for ax, year in zip(axes, years):
        for key, (color, marker, label) in cmap.items():
            rows = merged["by_year"][year][key]
            b_E = [r["b_E"] for r in rows]
            R = [r["R"] for r in rows]
            ax.plot(b_E, R, marker=marker, color=color, label=label, lw=1.5, ms=7)
        ax.set_xscale("log")
        ax.set_xlabel(r"$b_E$ (MWh)")
        ax.set_ylabel("Annual realised revenue (EUR)")
        ax.set_title(f"DK1 {year}")
        ax.grid(alpha=0.3)
        if year == years[0]:
            ax.legend(fontsize=8, loc="lower right")
    fig.suptitle("Realised arbitrage revenue vs battery capacity, by year + policy", y=1.02)
    fig.tight_layout()
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(f"Wrote {out}")


def figure_npv_vs_bE(merged: dict, out: str = "fig_paper_npv.png"):
    years = sorted(merged["by_year"].keys())
    fig, axes = plt.subplots(1, len(years), figsize=(5 * len(years), 4.5),
                              sharey=False)
    if len(years) == 1:
        axes = [axes]
    cmap = {
        "linear_single":   ("#aaaaaa", "o", "LP-linear single"),
        "linear_ensemble": ("#117733", "s", "LP-linear K=4-lag"),
        "quadratic_single": ("#cc6677", "D", "QP-quadratic single"),
        "quadratic_ensemble": ("#4477aa", "^", "QP-quadratic K=4-lag"),
    }
    for ax, year in zip(axes, years):
        bE_stars = []
        for key, (color, marker, label) in cmap.items():
            rows = merged["by_year"][year][key]
            b_E = np.array([r["b_E"] for r in rows])
            R = np.array([r["R"] for r in rows])
            npv = np.array([lifetime_npv(r, b) for r, b in zip(R, b_E)])
            ax.plot(b_E, npv, marker=marker, color=color, label=label, lw=1.5, ms=7)
            bE_star = b_E[np.argmax(npv)]
            bE_stars.append((label, bE_star, float(np.max(npv))))
        ax.axhline(0, color="black", lw=0.5)
        ax.set_xscale("log")
        ax.set_xlabel(r"$b_E$ (MWh)")
        ax.set_ylabel("Lifetime NPV (EUR, 15 yr, 7%)")
        title = f"DK1 {year}"
        title += f"   $b_E^*$ = " + " / ".join(f"{s:.0f}" for _, s, _ in bE_stars)
        ax.set_title(title)
        ax.grid(alpha=0.3)
        if year == years[0]:
            ax.legend(fontsize=8, loc="lower left")
    fig.suptitle("Lifetime NPV vs battery capacity, by year + policy. Argmax shift = sizing-shift evidence.", y=1.02)
    fig.tight_layout()
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(f"Wrote {out}")


def figure_lift_vs_bE(merged: dict, out: str = "fig_paper_lift.png"):
    years = sorted(merged["by_year"].keys())
    fig, axes = plt.subplots(1, len(years), figsize=(5 * len(years), 4.5),
                              sharey=True)
    if len(years) == 1:
        axes = [axes]
    for ax, year in zip(axes, years):
        for cost, color, marker in [("linear", "#cc6677", "o"), ("quadratic", "#4477aa", "s")]:
            single = merged["by_year"][year][f"{cost}_single"]
            ens = merged["by_year"][year][f"{cost}_ensemble"]
            b_E = np.array([r["b_E"] for r in single])
            R_s = np.array([r["R"] for r in single])
            R_e = np.array([r["R"] for r in ens])
            lift = (R_e - R_s) / np.maximum(np.abs(R_s), 1e-6) * 100
            ax.plot(b_E, lift, marker=marker, color=color, label=f"{cost.title()}", lw=1.5)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_xscale("log")
        ax.set_xlabel(r"$b_E$ (MWh)")
        ax.set_ylabel("Ensemble revenue lift over single (%)")
        ax.set_title(f"DK1 {year}")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=9)
    fig.suptitle("Ensemble lift vs $b_E$. Constant-in-$b_E$ lift -> argmax invariant. Falling lift -> argmax shift.", y=1.02)
    fig.tight_layout()
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(f"Wrote {out}")


def figure_spectrum(merged: dict, out: str = "fig_paper_spectrum.png"):
    """Plot welch PSDs of synthetic AR(1) + DK1 yearly traces."""
    from price_signal import synth_diurnal
    from dk_loader import load_dk_year
    from spectrum import welch_psd

    fig, ax = plt.subplots(figsize=(9, 5))
    # Synthetic
    x = synth_diurnal(168 * 4, seed=0)
    p, P = welch_psd(x)
    ax.loglog(p, P, label="Synthetic diurnal AR(1)", color="#aaaaaa", lw=1.5)
    # DK1 each year
    colors = {"2021": "#117733", "2022": "#cc6677", "2023": "#4477aa"}
    for year in sorted(merged["by_year"].keys()):
        df = load_dk_year(int(year))
        x = df["da_eur_per_mwh"].to_numpy()
        p, P = welch_psd(x)
        ax.loglog(p, P, label=f"DK1 {year}", color=colors[year], lw=1.5)
    for tau, label in [(12, "12h"), (24, "1d"), (168, "1 wk"), (720, "1 mo")]:
        ax.axvline(tau, color="black", ls=":", lw=0.6, alpha=0.5)
        ax.text(tau, ax.get_ylim()[1] * 0.4, label, ha="center", fontsize=8, alpha=0.6)
    ax.set_xlabel("Period (hours)")
    ax.set_ylabel("PSD (EUR/MWh)$^2$ / cyc/day")
    ax.set_title("Spectral content: synthetic vs DK1 day-ahead prices")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(f"Wrote {out}")


def summary_table(merged: dict) -> None:
    print("\nSummary table (lifetime NPV, EUR):")
    years = sorted(merged["by_year"].keys())
    print(f"{'year':>6} | {'metric':>12} | {'lin_s':>11} | {'lin_e':>11} | {'qp_s':>11} | {'qp_e':>11} | {'lift_qp':>8}")
    for year in years:
        ye = merged["by_year"][year]
        # find argmax NPV per policy
        best = {}
        for policy in ["linear_single", "linear_ensemble", "quadratic_single", "quadratic_ensemble"]:
            rows = ye[policy]
            best_npv = -1e18
            best_b = 0
            for row in rows:
                npv = lifetime_npv(row["R"], row["b_E"])
                if npv > best_npv:
                    best_npv = npv
                    best_b = row["b_E"]
            best[policy] = (best_b, best_npv)
        lift = (best["quadratic_ensemble"][1] - best["quadratic_single"][1]) / max(abs(best["quadratic_single"][1]), 1.0) * 100
        print(f"{year:>6} | {'b_E*':>12} | {best['linear_single'][0]:11.0f} | {best['linear_ensemble'][0]:11.0f} | {best['quadratic_single'][0]:11.0f} | {best['quadratic_ensemble'][0]:11.0f} |")
        print(f"{'':>6} | {'NPV*':>12} | {best['linear_single'][1]:11.0f} | {best['linear_ensemble'][1]:11.0f} | {best['quadratic_single'][1]:11.0f} | {best['quadratic_ensemble'][1]:11.0f} | {lift:+7.1f}%")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="paper_results JSON files")
    args = parser.parse_args()
    merged = load_results(*args.paths)
    figure_revenue_vs_bE(merged)
    figure_npv_vs_bE(merged)
    figure_lift_vs_bE(merged)
    figure_spectrum(merged)
    summary_table(merged)


if __name__ == "__main__":
    main()
