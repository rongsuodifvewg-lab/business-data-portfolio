from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "hillstrom.csv"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 140, "axes.titlesize": 12, "axes.labelsize": 10})


def proportion_ci(successes, n, z=1.96):
    p = successes / n
    se = np.sqrt(max(p * (1 - p) / n, 0))
    return p - z * se, p + z * se


def bootstrap_mean_diff(treated, control, reps=1200, seed=42):
    rng = np.random.default_rng(seed)
    treated = np.asarray(treated, dtype=float)
    control = np.asarray(control, dtype=float)
    diffs = np.empty(reps)
    for i in range(reps):
        diffs[i] = rng.choice(treated, len(treated), replace=True).mean() - rng.choice(control, len(control), replace=True).mean()
    return float(diffs.mean()), np.quantile(diffs, [0.025, 0.975])


def main():
    df = pd.read_csv(DATA)
    expected = {"segment", "visit", "conversion", "spend", "history_segment", "history", "recency", "channel", "newbie"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["visit"] = df["visit"].astype(int)
    df["conversion"] = df["conversion"].astype(int)
    df["spend"] = df["spend"].astype(float)
    control_name = "No E-Mail"
    groups = ["No E-Mail", "Mens E-Mail", "Womens E-Mail"]

    group_rows = []
    effect_rows = []
    for group in groups:
        g = df[df["segment"] == group]
        visit_low, visit_high = proportion_ci(g["visit"].sum(), len(g))
        conv_low, conv_high = proportion_ci(g["conversion"].sum(), len(g))
        group_rows.append({
            "segment": group,
            "n": len(g),
            "visit_rate": g["visit"].mean(),
            "visit_ci_low": visit_low,
            "visit_ci_high": visit_high,
            "conversion_rate": g["conversion"].mean(),
            "conversion_ci_low": conv_low,
            "conversion_ci_high": conv_high,
            "avg_spend": g["spend"].mean(),
            "total_spend": g["spend"].sum(),
        })
        if group == control_name:
            continue
        control = df[df["segment"] == control_name]
        visit_diff = g["visit"].mean() - control["visit"].mean()
        conv_diff = g["conversion"].mean() - control["conversion"].mean()
        spend_diff, spend_ci = bootstrap_mean_diff(g["spend"].values, control["spend"].values)
        _, visit_p = stats.ttest_ind(g["visit"], control["visit"], equal_var=False)
        _, conv_p = stats.ttest_ind(g["conversion"], control["conversion"], equal_var=False)
        _, spend_p = stats.ttest_ind(g["spend"], control["spend"], equal_var=False)
        effect_rows.append({
            "treatment": group,
            "control": control_name,
            "treatment_n": len(g),
            "control_n": len(control),
            "visit_lift_pp": visit_diff * 100,
            "conversion_lift_pp": conv_diff * 100,
            "spend_lift_per_customer": spend_diff,
            "spend_ci_low": spend_ci[0],
            "spend_ci_high": spend_ci[1],
            "visit_p_value": visit_p,
            "conversion_p_value": conv_p,
            "spend_p_value": spend_p,
        })

    group_summary = pd.DataFrame(group_rows)
    effects = pd.DataFrame(effect_rows)
    group_summary.to_csv(OUT / "group_summary.csv", index=False)
    effects.to_csv(OUT / "effect_vs_control.csv", index=False)

    # Pre-treatment balance check: standardized mean differences (SMD).
    # Values below |0.1| are commonly treated as a reasonable balance signal.
    balance_rows = []
    control = df[df["segment"] == control_name]
    numeric_balance = ["recency", "history", "mens", "womens", "newbie"]
    for treatment in ["Mens E-Mail", "Womens E-Mail"]:
        treated_balance = df[df["segment"] == treatment]
        for col in numeric_balance:
            mt, mc = treated_balance[col].mean(), control[col].mean()
            vt, vc = treated_balance[col].var(ddof=1), control[col].var(ddof=1)
            pooled = np.sqrt((vt + vc) / 2)
            balance_rows.append({"treatment": treatment, "variable": col, "level": "__all__", "smd": (mt - mc) / pooled if pooled else 0.0})
        for col in ["history_segment", "zip_code", "channel"]:
            levels = sorted(set(treated_balance[col].astype(str)) | set(control[col].astype(str)))
            for level in levels:
                pt = (treated_balance[col].astype(str) == level).mean()
                pc = (control[col].astype(str) == level).mean()
                pooled = np.sqrt((pt * (1 - pt) + pc * (1 - pc)) / 2)
                balance_rows.append({"treatment": treatment, "variable": col, "level": level, "smd": (pt - pc) / pooled if pooled else 0.0})
    balance = pd.DataFrame(balance_rows)
    balance.to_csv(OUT / "balance_check.csv", index=False)

    subgroup_rows = []
    control = df[df["segment"] == control_name]
    for subgroup in ["history_segment", "newbie", "channel"]:
        levels = df[subgroup].dropna().unique()
        for level in levels:
            c = control[control[subgroup] == level]
            if len(c) < 100:
                continue
            for treatment in ["Mens E-Mail", "Womens E-Mail"]:
                t = df[(df["segment"] == treatment) & (df[subgroup] == level)]
                if len(t) < 100:
                    continue
                subgroup_rows.append({
                    "subgroup": subgroup,
                    "level": str(level),
                    "treatment": treatment,
                    "n_treatment": len(t),
                    "n_control": len(c),
                    "conversion_lift_pp": (t["conversion"].mean() - c["conversion"].mean()) * 100,
                    "spend_lift_per_customer": t["spend"].mean() - c["spend"].mean(),
                })
    subgroups = pd.DataFrame(subgroup_rows)
    subgroups.to_csv(OUT / "subgroup_effects.csv", index=False)

    # Business scenario: revenue is spend; margin and email cost are explicit assumptions.
    scenarios = []
    for margin in [0.20, 0.40, 0.60]:
        for email_cost in [0.01, 0.05, 0.10]:
            for row in effect_rows:
                incremental_profit = row["spend_lift_per_customer"] * margin - email_cost
                scenarios.append({
                    "treatment": row["treatment"],
                    "gross_margin": margin,
                    "email_cost_per_customer": email_cost,
                    "incremental_profit_per_customer": incremental_profit,
                    "roi_on_email_cost": incremental_profit / email_cost,
                    "recommendation": "scale candidate" if incremental_profit > 0 else "do not scale under assumption",
                })
    pd.DataFrame(scenarios).to_csv(OUT / "economic_scenarios.csv", index=False)

    fig, ax = plt.subplots(figsize=(6.8, 3.7))
    plot_df = group_summary.copy()
    ax.bar(plot_df["segment"], plot_df["conversion_rate"] * 100, color=["#A8B5C2", "#2D6A9F", "#D9864A"])
    ax.set_ylabel("Conversion rate (%)")
    ax.set_title("Conversion rate by randomized email treatment")
    ax.tick_params(axis="x", rotation=12)
    fig.tight_layout()
    fig.savefig(OUT / "conversion_by_treatment.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 4.1))
    plot = subgroups[subgroups["subgroup"] == "history_segment"].copy()
    if not plot.empty:
        pivot = plot.pivot(index="level", columns="treatment", values="conversion_lift_pp")
        pivot.plot(kind="bar", ax=ax, color=["#2D6A9F", "#D9864A"])
        ax.axhline(0, color="#333333", linewidth=0.8)
        ax.set_ylabel("Conversion lift vs no email (pp)")
        ax.set_xlabel("Historical spending segment")
        ax.set_title("Heterogeneous conversion lift by customer value")
        ax.legend(title="Treatment", frameon=False)
        ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(OUT / "conversion_lift_by_history_segment.png", bbox_inches="tight")
    plt.close(fig)

    scenario_df = pd.DataFrame(scenarios)
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    for treatment, color in [("Mens E-Mail", "#2D6A9F"), ("Womens E-Mail", "#D9864A")]:
        d = scenario_df[(scenario_df["treatment"] == treatment) & (scenario_df["gross_margin"] == 0.40)]
        ax.plot(d["email_cost_per_customer"], d["incremental_profit_per_customer"], marker="o", label=treatment, color=color)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Email cost per customer")
    ax.set_ylabel("Incremental profit per customer")
    ax.set_title("Economic sensitivity at 40% gross margin")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "profit_sensitivity.png", bbox_inches="tight")
    plt.close(fig)

    metadata = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "treatment_groups": {k: int(v) for k, v in df["segment"].value_counts().to_dict().items()},
        "source": "http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv",
        "assumptions": {"gross_margin_scenarios": [0.20, 0.40, 0.60], "email_cost_scenarios": [0.01, 0.05, 0.10]},
    }
    (OUT / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(effects.to_string(index=False))


if __name__ == "__main__":
    main()
