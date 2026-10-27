#!/usr/bin/env python3
"""
make_figures.py — The Polycrisis Apocalypse Humanity Is Facing
Generates 10 brand-styled figures (H Heuristics navy/blue/orange) with the
docx-safe save_chart pattern: RGBA->RGB, resize to 1100px wide, dpi=200 metadata.
"""
import io, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
from PIL import Image

OUT = "figures"
os.makedirs(OUT, exist_ok=True)

NAVY = "#0F4D92"
BLUE = "#3775BA"
ORANGE = "#E67E22"
GREY = "#6C757D"
DARK = "#2C3E50"
RED = "#C0392B"
GREEN = "#27AE60"
LIGHT = "#D6E4F0"
PALE = "#F4F6F8"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": "#8A9099",
    "axes.labelcolor": DARK,
    "text.color": DARK,
    "xtick.color": GREY,
    "ytick.color": GREY,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
})


def save_chart(fig, name):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, facecolor="white", bbox_inches="tight")
    buf.seek(0)
    im = Image.open(buf).convert("RGB")
    w, h = im.size
    target = 1100
    if w != target:
        im = im.resize((target, max(1, int(h * target / w))), Image.LANCZOS)
    im.save(os.path.join(OUT, f"{name}.png"), dpi=(200, 200))
    plt.close(fig)
    print(f"  saved {name}.png")


# ── Figure 1: The polycrisis engine (loop schematic) ──────────────────────
def fig1():
    fig, ax = plt.subplots(figsize=(10, 7.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.2); ax.axis("off")
    nodes = [
        ("Pollution", 1.6, 5.4, NAVY),
        ("Climate change", 3.6, 6.6, BLUE),
        ("Poverty", 6.4, 6.6, ORANGE),
        ("Conflict", 8.4, 5.4, RED),
        ("Weapons\nproliferation", 7.4, 2.4, GREY),
        ("Institutional\nerosion", 2.6, 2.4, DARK),
    ]
    pos = {n[0]: (n[1], n[2]) for n in nodes}
    for name, x, y, c in nodes:
        ax.add_patch(Circle((x, y), 0.62, facecolor=c, edgecolor="white", lw=2, zorder=2))
        ax.text(x, y, name, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold", zorder=3)
    edges = [
        ("Pollution", "Climate change"), ("Climate change", "Poverty"),
        ("Poverty", "Conflict"), ("Conflict", "Weapons\nproliferation"),
        ("Weapons\nproliferation", "Institutional\nerosion"),
        ("Institutional\nerosion", "Pollution"),
        ("Climate change", "Conflict"), ("Poverty", "Pollution"),
        ("Conflict", "Institutional\nerosion"),
    ]
    for a, b in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=14, lw=1.8, color=GREY,
                                     shrinkA=38, shrinkB=38, zorder=1))
    ax.text(5, 0.55, "The polycrisis engine: each crisis feeds the others, so the whole system degrades\n"
                     "even when no single shock is lethal on its own.",
            ha="center", va="center", fontsize=11, color=DARK, style="italic")
    ax.set_title("Figure 1: The Polycrisis Engine", color=NAVY, pad=14)
    save_chart(fig, "fig1_polycrisis_engine")


# ── Figure 2: Habitability tiers ──────────────────────────────────────────
def fig2():
    tiers = ["Stable\nrefugia", "Survivability\nRisk Zone", "High-Stress\nBelt", "Dead\nZones"]
    y2025 = [2.4, 3.6, 1.7, 0.3]
    y2050 = [1.8, 4.2, 2.8, 0.7]
    y2100 = [1.6, 5.1, 2.9, 0.6]
    x = np.arange(len(tiers)); w = 0.26
    fig, ax = plt.subplots(figsize=(9.6, 6.0))
    ax.bar(x - w, y2025, w, label="2025", color=BLUE)
    ax.bar(x, y2050, w, label="2050", color=ORANGE)
    ax.bar(x + w, y2100, w, label="2100", color=NAVY)
    ax.set_xticks(x); ax.set_xticklabels(tiers, fontsize=9.5)
    ax.set_ylabel("Population (billions)")
    ax.set_ylim(0, 6.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("Where humanity lives under compounding risk", color=NAVY, pad=12)
    ax.annotate("Majority of humanity", xy=(1.0, 4.2), xytext=(1.6, 5.6),
                fontsize=9.5, color=DARK, arrowprops=dict(arrowstyle="->", color=DARK))
    ax.grid(axis="y", color=PALE, lw=0.8)
    ax.set_axisbelow(True)
    save_chart(fig, "fig2_habitability_tiers")


# ── Figure 3: Share trapped in survivability risk regions ─────────────────
def fig3():
    t = np.linspace(2025, 2300, 300)
    managed = np.clip(52 * (1 - 0.45 * (1 - np.exp(-(t - 2025) / 90))) - 8 * (t - 2025) / 275, 28, 55)
    plateau = 40 + 18 * (1 - np.exp(-(t - 2025) / 55))
    worsen = np.clip(40 + 34 * (1 - np.exp(-(t - 2025) / 60)) + 0.05 * (t - 2025), 40, 88)
    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    ax.plot(t, managed, color=GREEN, lw=2.4, label="Managed adaptation")
    ax.plot(t, plateau, color=BLUE, lw=2.4, label="Trapped majority (stabilizes at unsafe levels)")
    ax.plot(t, worsen, color=RED, lw=2.4, label="Worsening (pessimistic)")
    ax.axhline(50, color=GREY, lw=1.0, ls="--")
    ax.text(2026, 51.5, "Half of humanity", color=GREY, fontsize=9)
    ax.set_xlabel("Year"); ax.set_ylabel("Share of humanity in survivability risk regions (%)")
    ax.set_ylim(0, 100); ax.set_xlim(2025, 2300)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_title("The apocalypse is a plateau, then a decline — not a single event", color=NAVY, pad=12)
    ax.annotate("stabilization at unsafe levels", xy=(2160, 58.5), xytext=(2060, 72),
                fontsize=9.5, color=DARK, arrowprops=dict(arrowstyle="->", color=DARK))
    ax.annotate("extinction pathway", xy=(2280, 85), xytext=(2215, 92),
                fontsize=9.5, color=RED, arrowprops=dict(arrowstyle="->", color=RED))
    ax.grid(axis="y", color=PALE, lw=0.8); ax.set_axisbelow(True)
    save_chart(fig, "fig3_trapped_share")


# ── Figure 4: Africa's rise vs Europe / North America ─────────────────────
def fig4():
    years = [1950, 1970, 1990, 2010, 2024, 2050, 2075, 2100]
    africa = [0.23, 0.37, 0.64, 1.06, 1.51, 2.5, 3.2, 3.81]
    europe = [0.55, 0.66, 0.72, 0.74, 0.745, 0.70, 0.65, 0.59]
    namerica = [0.17, 0.23, 0.28, 0.34, 0.38, 0.42, 0.43, 0.44]
    fig, ax = plt.subplots(figsize=(9.6, 5.8))
    ax.plot(years, africa, color=ORANGE, lw=3, marker="o", ms=4, label="Africa")
    ax.plot(years, europe, color=BLUE, lw=3, marker="o", ms=4, label="Europe")
    ax.plot(years, namerica, color=GREY, lw=3, marker="o", ms=4, label="North America")
    ax.fill_between(years, africa, 0, color=ORANGE, alpha=0.12)
    ax.set_xlabel("Year"); ax.set_ylabel("Population (billions)")
    ax.set_xlim(1950, 2100); ax.set_ylim(0, 4.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Demographic tectonics: Africa adds ~2.3 billion people while Europe declines",
                 color=NAVY, pad=12)
    ax.annotate("1.51B (2024)", xy=(2024, 1.51), xytext=(1992, 2.0), fontsize=9,
                color=ORANGE, arrowprops=dict(arrowstyle="->", color=ORANGE))
    ax.annotate("3.81B (2100)", xy=(2100, 3.81), xytext=(2068, 3.55), fontsize=9,
                color=ORANGE, arrowprops=dict(arrowstyle="->", color=ORANGE))
    ax.annotate("0.59B (2100)", xy=(2100, 0.59), xytext=(2072, 1.15), fontsize=9,
                color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE))
    ax.grid(axis="y", color=PALE, lw=0.8); ax.set_axisbelow(True)
    save_chart(fig, "fig4_africa_rise")


# ── Figure 5: Regional shares of world population ─────────────────────────
def fig5():
    regions = ["Africa", "Asia", "Europe", "Latin America\n& Caribbean", "North America", "Oceania"]
    s2024 = [18.4, 59.2, 9.1, 8.3, 4.7, 0.56]
    s2100 = [37.4, 45.0, 5.8, 6.4, 4.3, 0.7]
    y = np.arange(len(regions))[::-1]
    fig, ax = plt.subplots(figsize=(9.6, 5.8))
    ax.barh(y + 0.18, s2024, 0.36, color=BLUE, label="2024")
    ax.barh(y - 0.18, s2100, 0.36, color=ORANGE, label="2100")
    ax.set_yticks(y); ax.set_yticklabels(regions, fontsize=9.5)
    ax.set_xlabel("Share of world population (%)")
    ax.set_xlim(0, 65)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("By 2100 more than 8 in 10 people will live in Asia or Africa", color=NAVY, pad=12)
    for yi, a, b in zip(y, s2024, s2100):
        ax.text(a + 0.5, yi + 0.18, f"{a:.0f}%", va="center", fontsize=8.5, color=BLUE)
        ax.text(b + 0.5, yi - 0.18, f"{b:.0f}%", va="center", fontsize=8.5, color=ORANGE)
    ax.grid(axis="x", color=PALE, lw=0.8); ax.set_axisbelow(True)
    save_chart(fig, "fig5_world_share_2100")


# ── Figure 6: The median human's region ───────────────────────────────────
def fig6():
    years = np.arange(1950, 2201, 10)
    africa = np.interp(years, [1950, 2000, 2024, 2050, 2100, 2200], [9, 13, 18.4, 25, 37.4, 44])
    asia = np.interp(years, [1950, 2000, 2024, 2050, 2100, 2200], [55, 61, 59.2, 54, 45, 38])
    others = 100 - africa - asia
    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    ax.stackplot(years, asia, africa, others, labels=["Asia", "Africa", "Rest of world"],
                 colors=[BLUE, ORANGE, GREY], alpha=0.85)
    ax.axhline(50, color="white", lw=1.6, ls="--")
    ax.text(1952, 53, "median human lives in the most populous cumulative region",
            color="white", fontsize=8.5)
    ax.annotate("median human enters Africa\nin the 22nd century under the\nlong-run demographic scenario",
                xy=(2160, 50), xytext=(2090, 62), fontsize=9.5, color=DARK,
                arrowprops=dict(arrowstyle="->", color=DARK))
    ax.set_xlim(1950, 2200); ax.set_ylim(0, 100)
    ax.set_xlabel("Year"); ax.set_ylabel("Share of world population (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower left")
    ax.set_title("The middle 50% of humanity shifts south", color=NAVY, pad=12)
    ax.grid(axis="y", color=PALE, lw=0.8); ax.set_axisbelow(True)
    save_chart(fig, "fig6_middle50")


# ── Figure 7: Haiti collapse timeline ─────────────────────────────────────
def fig7():
    years = list(range(2000, 2026))
    gdp = [786, 766, 747, 615, 709, 786, 877, 1000, 1054, 1100, 1175, 1265, 1300, 1340, 1360, 1300, 1220, 1330, 1400, 1350, 1290, 1748, 1620, 1500, 1320, 1180]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.8, 7.6), sharex=True,
                                 gridspec_kw={"height_ratios": [1, 1.15], "hspace": 0.12})
    a1.plot(years, gdp, color=NAVY, lw=2.4)
    a1.fill_between(years, gdp, 0, color=NAVY, alpha=0.10)
    a1.set_ylabel("GDP per capita\n(current US$)")
    a1.spines[["top", "right"]].set_visible(False)
    a1.set_title("Haiti: the anatomy of a slow collapse", color=NAVY, pad=10)
    a1.annotate("2010 earthquake", xy=(2010, 1175), xytext=(2004, 1560), fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color=DARK))
    a1.annotate("2021 president\nassassinated", xy=(2021, 1290), xytext=(2016, 1580), fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color=DARK))
    a1.grid(axis="y", color=PALE, lw=0.8); a1.set_axisbelow(True)

    hy = list(range(2018, 2026))
    kills = [1000, 900, 1200, 1600, 2200, 4800, 5600, 5915]
    gang = [20, 25, 30, 50, 60, 80, 85, 90]
    a2.bar(hy, kills, 0.62, color=RED, alpha=0.85, label="Reported killings (BINUH/OHCHR)")
    a2.set_ylabel("Reported killings\nper year")
    a2.set_xlim(1999.5, 2025.5)
    a2.spines[["top", "right"]].set_visible(False)
    a2.grid(axis="y", color=PALE, lw=0.8); a2.set_axisbelow(True)
    a3 = a2.twinx()
    a3.plot(hy, gang, color=ORANGE, lw=2.6, marker="o", ms=4, label="Gang control of Port-au-Prince (%)")
    a3.set_ylabel("Gang control of\nPort-au-Prince (%)")
    a3.set_ylim(0, 100)
    a3.spines[["top"]].set_visible(False)
    lines1, labels1 = a2.get_legend_handles_labels()
    lines2, labels2 = a3.get_legend_handles_labels()
    a2.legend(lines1 + lines2, labels1 + labels2, frameon=False, loc="upper left", fontsize=8.5)
    save_chart(fig, "fig7_haiti_collapse")


# ── Figure 8: Nuclear military stockpiles ─────────────────────────────────
def fig8():
    states = ["North Korea", "Israel", "United Kingdom", "France", "India", "Pakistan", "China", "United States", "Russia"]
    stock = [50, 90, 225, 290, 180, 170, 600, 3708, 4380]
    y = np.arange(len(states))[::-1]
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    colors = [RED if s in ("Russia", "United States") else BLUE for s in states]
    ax.barh(y, stock, 0.6, color=colors)
    ax.set_yticks(y); ax.set_yticklabels(states, fontsize=9.5)
    ax.set_xlabel("Warheads in military stockpile (approx., January 2025)")
    ax.set_xlim(0, 4800)
    ax.spines[["top", "right"]].set_visible(False)
    for yi, v in zip(y, stock):
        ax.text(v + 60, yi, f"{v:,}", va="center", fontsize=8.5, color=DARK)
    ax.set_title("Advanced weapons: ~9,600 warheads in military stockpiles, modernizing not shrinking",
                 color=NAVY, pad=12)
    ax.grid(axis="x", color=PALE, lw=0.8); ax.set_axisbelow(True)
    save_chart(fig, "fig8_weapons_landscape")


# ── Figure 9: Conflict cascade network ────────────────────────────────────
def fig9():
    fig, ax = plt.subplots(figsize=(9.8, 6.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.6); ax.axis("off")
    nodes = [
        ("Climate stress", 1.5, 5.6, NAVY),
        ("Crop failure", 3.4, 5.6, GREEN),
        ("Water scarcity", 5.5, 5.6, BLUE),
        ("Energy shock", 7.6, 5.6, ORANGE),
        ("Price spike", 3.0, 3.6, ORANGE),
        ("Migration", 5.2, 3.6, BLUE),
        ("Political\ninstability", 7.4, 3.6, RED),
        ("Armed conflict", 3.4, 1.5, RED),
        ("Institutional\ncollapse", 6.4, 1.5, DARK),
    ]
    pos = {n[0]: (n[1], n[2]) for n in nodes}
    for name, x, y, c in nodes:
        ax.add_patch(Circle((x, y), 0.58, facecolor=c, edgecolor="white", lw=2, zorder=2))
        ax.text(x, y, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold", zorder=3)
    edges = [
        ("Climate stress", "Crop failure"), ("Climate stress", "Water scarcity"),
        ("Crop failure", "Price spike"), ("Water scarcity", "Price spike"),
        ("Energy shock", "Price spike"), ("Price spike", "Migration"),
        ("Price spike", "Political\ninstability"), ("Migration", "Political\ninstability"),
        ("Political\ninstability", "Armed conflict"), ("Armed conflict", "Institutional\ncollapse"),
        ("Institutional\ncollapse", "Armed conflict"), ("Climate stress", "Migration"),
    ]
    for a, b in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=13, lw=1.7, color=GREY,
                                     shrinkA=34, shrinkB=34, zorder=1))
    ax.text(5, 0.35, "Shocks rarely stay in one system: stress cascades from climate into markets,\n"
                     "migration, politics, and violence.",
            ha="center", va="center", fontsize=10.5, color=DARK, style="italic")
    ax.set_title("Figure 9: The Instability Cascade", color=NAVY, pad=12)
    save_chart(fig, "fig9_conflict_cascades")


# ── Figure 10: Collapse scenarios to 2300 ─────────────────────────────────
def fig10():
    t = np.linspace(2025, 2300, 300)
    managed = np.clip(58 * np.exp(-(t - 2025) / 160) + 30, 30, 62)
    trapped = np.clip(52 + 26 * (1 - np.exp(-(t - 2025) / 45)), 50, 80)
    cascade = np.clip(52 + 30 * (1 - np.exp(-(t - 2025) / 40)) + 0.08 * (t - 2025), 50, 98)
    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    ax.plot(t, managed, color=GREEN, lw=2.6, label="A · Managed adaptation")
    ax.plot(t, trapped, color=BLUE, lw=2.6, label="B · Trapped majority (unsafe plateau)")
    ax.plot(t, cascade, color=RED, lw=2.6, label="C · Cascade collapse → extinction")
    ax.set_xlabel("Year"); ax.set_ylabel("Civilizational stress index (0–100)")
    ax.set_xlim(2025, 2300); ax.set_ylim(0, 105)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    ax.set_title("Three long-run paths for a polycrisis century", color=NAVY, pad=12)
    ax.annotate("unsafe stabilization\n(centuries of attrition)", xy=(2190, 78.5), xytext=(2110, 88),
                fontsize=9.5, color=DARK, arrowprops=dict(arrowstyle="->", color=DARK))
    ax.annotate("extinction", xy=(2280, 96), xytext=(2230, 100),
                fontsize=9.5, color=RED, arrowprops=dict(arrowstyle="->", color=RED))
    ax.grid(axis="y", color=PALE, lw=0.8); ax.set_axisbelow(True)
    save_chart(fig, "fig10_collapse_scenarios")


if __name__ == "__main__":
    print("Generating figures…")
    fig1(); fig2(); fig3(); fig4(); fig5()
    fig6(); fig7(); fig8(); fig9(); fig10()
    print("Done.")
