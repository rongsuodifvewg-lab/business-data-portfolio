from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "criteo_sample_5000.csv"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 140, "axes.titlesize": 12, "axes.labelsize": 10})


def diff_ci(treatment, control, z=1.96):
    p_t, p_c = treatment.mean(), control.mean()
    diff = p_t - p_c
    se = np.sqrt(p_t * (1 - p_t) / len(treatment) + p_c * (1 - p_c) / len(control))
    return float(diff), float(diff - z * se), float(diff + z * se)


def main():
    df = pd.read_csv(DATA)
    feature_cols = [c for c in df.columns if c.startswith("f")]
    required = set(feature_cols + ["treatment", "conversion", "visit", "exposure"])
    if not required.issubset(df.columns):
        raise ValueError(f"Criteo fields missing: {sorted(required - set(df.columns))}")
    for col in ["treatment", "conversion", "visit", "exposure"]:
        df[col] = df[col].astype(int)

    rows = []
    for treatment_value, label in [(0, "control"), (1, "treatment")]:
        g = df[df["treatment"] == treatment_value]
        rows.append({
            "group": label,
            "n": len(g),
            "treatment_rate": g["treatment"].mean(),
            "visit_rate": g["visit"].mean(),
            "conversion_rate": g["conversion"].mean(),
            "exposure_rate": g["exposure"].mean(),
        })
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "treatment_summary.csv", index=False)
    control = df[df["treatment"] == 0]
    treated = df[df["treatment"] == 1]
    effects = []
    for outcome in ["visit", "conversion", "exposure"]:
        diff, low, high = diff_ci(treated[outcome], control[outcome])
        effects.append({"outcome": outcome, "treatment_rate": treated[outcome].mean(), "control_rate": control[outcome].mean(), "lift_pp": diff * 100, "ci_low_pp": low * 100, "ci_high_pp": high * 100})
    effects_df = pd.DataFrame(effects)
    effects_df.to_csv(OUT / "average_treatment_effects.csv", index=False)

    # T-learner: separately model treated and control outcomes, then estimate
    # p(y|x,t=1)-p(y|x,t=0). The small sample makes this a diagnostic ranking only.
    target = "visit"
    x = df[feature_cols]
    treated_model = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(max_iter=1200, class_weight="balanced", C=0.5)),
    ])
    control_model = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(max_iter=1200, class_weight="balanced", C=0.5)),
    ])
    treated_model.fit(x[df["treatment"] == 1], df.loc[df["treatment"] == 1, target])
    control_model.fit(x[df["treatment"] == 0], df.loc[df["treatment"] == 0, target])
    df["pred_p_treat"] = treated_model.predict_proba(x)[:, 1]
    df["pred_p_control"] = control_model.predict_proba(x)[:, 1]
    df["pred_uplift"] = df["pred_p_treat"] - df["pred_p_control"]
    df["uplift_decile"] = pd.qcut(df["pred_uplift"].rank(method="first"), 10, labels=False, duplicates="drop")
    df["uplift_decile"] = 10 - df["uplift_decile"]

    decile_rows = []
    for decile, g in df.groupby("uplift_decile", sort=True):
        t = g[g["treatment"] == 1][target]
        c = g[g["treatment"] == 0][target]
        diff = t.mean() - c.mean() if len(t) and len(c) else np.nan
        decile_rows.append({
            "uplift_decile": int(decile),
            "n": len(g),
            "predicted_uplift_mean": g["pred_uplift"].mean(),
            "treated_n": len(t),
            "control_n": len(c),
            "observed_visit_lift_pp": diff * 100,
            "observed_treatment_visit_rate": t.mean() if len(t) else np.nan,
            "observed_control_visit_rate": c.mean() if len(c) else np.nan,
        })
    deciles = pd.DataFrame(decile_rows).sort_values("uplift_decile")
    deciles.to_csv(OUT / "uplift_deciles.csv", index=False)

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.bar(summary["group"], summary["visit_rate"] * 100, color=["#A8B5C2", "#2D6A9F"])
    ax.set_ylabel("Visit rate (%)")
    ax.set_title("Visit rate by treatment assignment")
    fig.tight_layout()
    fig.savefig(OUT / "visit_rate_by_treatment.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.plot(deciles["uplift_decile"], deciles["observed_visit_lift_pp"], marker="o", color="#2D6A9F")
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Predicted uplift decile (1 = highest predicted uplift)")
    ax.set_ylabel("Observed visit lift (pp)")
    ax.set_title("Uplift ranking diagnostic on sampled data")
    fig.tight_layout()
    fig.savefig(OUT / "uplift_decile_curve.png", bbox_inches="tight")
    plt.close(fig)

    feature_stats = df[feature_cols].describe().T.reset_index().rename(columns={"index": "feature"})
    feature_stats.to_csv(OUT / "feature_summary.csv", index=False)
    metadata = {
        "rows_analyzed": int(len(df)),
        "features": feature_cols,
        "target_for_uplift_model": target,
        "source": "https://ailab.criteo.com/criteo-uplift-prediction-dataset/",
        "sample_warning": "Results are computed on a 5,000-row deterministic index sample retrieved from the dataset viewer, not on the full 13,979,592-row dataset.",
        "model": "T-learner with separate treated/control logistic regressions; decile comparison is diagnostic, not a production targeting policy.",
    }
    (OUT / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(effects_df.to_string(index=False))


if __name__ == "__main__":
    main()
