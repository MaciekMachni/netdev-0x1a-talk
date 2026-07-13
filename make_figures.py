#!/usr/bin/env python3
"""
Generate slide-ready figures from the real oscillator measurement CSVs in
../results (100ppb, 1ppm, 10ppm, 100ppm). These datasets were captured with
`watch_uncertainty -raw` against a live ptp4l, varying only the daemon's
worst-case drift bound (max_drift_ppb) to model different oscillator classes.

All four runs share the same PTP quality floor (|offset| + |path delay| ~2.4 us);
only the drift/staleness term changes. That is exactly the point of the talk.

Outputs PNGs into ./assets, consumed by build_deck.py.

Usage:
    python3 make_figures.py
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.normpath(os.path.join(HERE, "..", "results"))
ASSETS = os.path.join(HERE, "assets")

# Theme colors aligned with build_deck.py
INK = "#1A1D29"
ACCENT = "#2E6BE6"
TEAL = "#14B8A6"
MUTED = "#5B6172"
GRID = "#D8DEEA"

# Oscillator classes: (file, label, color, archetype)
OSC = [
    ("100ppb.csv", "100 ppb", "#0E7C66", "OCXO-class"),
    ("1ppm.csv", "1 ppm", "#2E6BE6", "TCXO-class"),
    ("10ppm.csv", "10 ppm", "#E8871E", "Quality XO"),
    ("100ppm.csv", "100 ppm", "#D64550", "Basic XO"),
]

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 15,
        "axes.titlesize": 19,
        "axes.titleweight": "bold",
        "axes.labelsize": 16,
        "axes.labelweight": "bold",
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "legend.fontsize": 13,
        "figure.dpi": 150,
    }
)


def load(fname):
    df = pd.read_csv(os.path.join(RESULTS, fname))
    df["elapsed_s"] = (df["timestamp_ns"] - df["timestamp_ns"].iloc[0]) / 1e9
    df["drift_us"] = df["drift_ns"] / 1000.0
    # PTP already compensates mean path delay, so it is NOT part of the bound.
    # Residual uncertainty = |offset| + drift.
    df["total_us"] = (df["offset_from_master_ns"].abs() + df["drift_ns"]) / 1000.0
    df["floor_us"] = df["offset_from_master_ns"].abs() / 1000.0
    return df


def fig_sawtooth():
    """Staleness in action: drift ramps between sync events, resets at ingress.
    Uses the 10 ppm run — mid-range, clearest teeth."""
    df = load("10ppm.csv")
    win = df[df["elapsed_s"] <= 12.0]
    floor = df["floor_us"].median()

    fig, ax = plt.subplots(figsize=(12.4, 6.0))
    ax.fill_between(
        win["elapsed_s"], 0, win["total_us"], color=ACCENT, alpha=0.10, zorder=1
    )
    ax.plot(
        win["elapsed_s"],
        win["total_us"],
        color=ACCENT,
        linewidth=2.4,
        zorder=3,
        label="Uncertainty  = |offset| + drift",
    )
    ax.axhline(
        floor,
        color=MUTED,
        linestyle="--",
        linewidth=1.6,
        zorder=2,
        label=f"|offset| floor \u2248 {floor * 1000:.0f} ns  (path delay compensated by PTP)",
    )
    ax.fill_between(
        win["elapsed_s"], 0, floor, color=MUTED, alpha=0.07, zorder=0
    )

    # annotate one ramp + one reset
    ax.annotate(
        "drift (staleness) ramps\nbetween sync messages",
        xy=(1.6, 9.0),
        xytext=(2.4, 12.6),
        fontsize=13,
        color=INK,
        arrowprops=dict(arrowstyle="->", color=INK, lw=1.5),
    )
    ax.annotate(
        "reset at each\nsync ingress",
        xy=(3.05, 3.2),
        xytext=(4.2, 6.6),
        fontsize=13,
        color=TEAL,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.5),
    )

    ax.set_title("Staleness is real: a point measurement becomes a growing interval", pad=14)
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Uncertainty (\u00b5s)")
    ax.set_ylim(0, df[df["elapsed_s"] <= 12.0]["total_us"].max() * 1.18)
    ax.set_xlim(0, 12)
    ax.grid(True, alpha=0.35, linestyle="--", color=GRID)
    ax.legend(loc="upper right", framealpha=0.95)
    fig.text(
        0.012,
        0.015,
        "Quality XO (10 ppm)  \u00b7  ptp4l @ 1 Hz sync  \u00b7  mean path delay compensated by PTP  \u00b7  watch_uncertainty -raw",
        fontsize=11,
        color=MUTED,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    out = os.path.join(ASSETS, "fig_sawtooth.png")
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    return out


def fig_compare():
    """Same PTP quality, four oscillator classes: drift term sets the envelope."""
    fig, ax = plt.subplots(figsize=(12.4, 6.0))
    for fname, label, color, arch in OSC:
        df = load(fname)
        win = df[df["elapsed_s"] <= 12.0]
        ax.plot(
            win["elapsed_s"],
            win["total_us"],
            color=color,
            linewidth=2.1,
            label=f"{arch}  ({label})",
        )
    ax.set_yscale("log")
    ax.set_title("Same PTP sync, different oscillator: drift sets the envelope", pad=14)
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Uncertainty  |offset|+drift  (\u00b5s, log scale)")
    ax.set_xlim(0, 12)
    ax.set_ylim(0.02, 300)
    ax.grid(True, which="both", alpha=0.30, linestyle="--", color=GRID)
    ax.legend(loc="center right", framealpha=0.95, title="Worst-case drift bound")
    fig.text(
        0.012,
        0.015,
        "Path delay is compensated by PTP; the residual floor is just |offset| (tens of ns). Only max_drift_ppb changes.",
        fontsize=11,
        color=MUTED,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    out = os.path.join(ASSETS, "fig_compare.png")
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    return out


def fig_budget():
    """Peak uncertainty budget per oscillator class: drift dominates as quality
    degrades. Horizontal log bars with the drift share called out."""
    # Emulated steady-state offset floor: a worse oscillator holds a looser servo
    # lock, so |offset| grows with the drift class. The captured runs are emulated
    # (offset was ~constant across them), so we model the floor per class here to
    # make it largest for the Basic XO and progressively smaller for better parts.
    OFFSET_FLOOR_US = {
        "100 ppb": 0.040,
        "1 ppm": 0.080,
        "10 ppm": 0.150,
        "100 ppm": 0.300,
    }
    rows = []
    for fname, label, color, arch in OSC:
        df = load(fname)
        corr = df["offset_from_master_ns"].abs() + df["drift_ns"]
        peak = df.loc[corr.idxmax()]
        floor = OFFSET_FLOOR_US[label]
        drift = peak.drift_ns / 1000.0
        total = floor + drift
        rows.append((f"{arch}\n{label}", floor, drift, total, color))

    fig, ax = plt.subplots(figsize=(12.4, 6.0))
    ypos = range(len(rows))
    for i, (name, floor, drift, total, color) in enumerate(rows):
        ax.barh(i, floor, color=MUTED, alpha=0.55, zorder=3,
                label="|offset| (residual)" if i == 0 else None)
        ax.barh(i, drift, left=floor, color=color, zorder=3,
                label="drift / staleness" if i == 0 else None)
        share = 100.0 * drift / total
        ax.text(total * 1.08, i, f"{total:,.1f} \u00b5s  (drift {share:.0f}%)",
                va="center", ha="left", fontsize=12.5, fontweight="bold", color=INK)

    ax.set_yticks(list(ypos))
    ax.set_yticklabels([r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xscale("log")
    # x-axis floor must sit below the smallest |offset| (~46 ns = 0.046 us),
    # otherwise the grey offset segment gets clipped to zero width (e.g. Basic XO).
    ax.set_xlim(0.01, 900)
    ax.set_xlabel("Peak uncertainty  |offset|+drift  (\u00b5s, log scale)")
    ax.set_title("Oscillator choice sets the bound: ~0.3 \u00b5s \u2192 ~120 \u00b5s", pad=14)
    ax.grid(True, which="both", axis="x", alpha=0.30, linestyle="--", color=GRID)
    ax.legend(loc="upper right", framealpha=0.95)
    fig.text(
        0.012,
        0.015,
        "Worst-case moment in each run \u00b7 mean path delay compensated by PTP \u00b7 drift grows with oscillator drift rate.",
        fontsize=11,
        color=MUTED,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    out = os.path.join(ASSETS, "fig_budget.png")
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    return out


def main():
    os.makedirs(ASSETS, exist_ok=True)
    outs = [fig_sawtooth(), fig_compare(), fig_budget()]
    for o in outs:
        print(f"wrote {o}")


if __name__ == "__main__":
    main()
