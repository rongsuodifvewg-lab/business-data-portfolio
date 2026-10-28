from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "unzipped" / "online_shoppers_intention.csv"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 140, "axes.titlesize": 12, "axes.labelsize": 10})


def main():
    df = pd.read_csv(DATA)
    df["Revenue"] = df["Revenue"].astype(int)
    df["Weekend"] = df["Weekend"].astype(int)
    month_order = ["Feb", "Mar", "May", "June", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    summaries = {
        "overall": {
            "rows": int(len(df)),
            "conversion_rate": float(df["Revenue"].mean()),
            "buyers": int(df["Revenue"].sum()),
            "non_buyers": int((1 - df["Revenue"]).sum()),
        },
        "visitor_type": df.groupby("VisitorType", as_index=False).agg(
            sessions=("Revenue", "size"), buyers=("Revenue", "sum"), conversion_rate=("Revenue", "mean"),
            avg_page_values=("PageValues", "mean"), avg_exit_rate=("ExitRates", "mean"),
        ).to_dict(orient="records"),
        "weekend": df.groupby("Weekend", as_index=False).agg(
            sessions=("Revenue", "size"), buyers=("Revenue", "sum"), conversion_rate=("Revenue", "mean"),
        ).to_dict(orient="records"),
    }
    pd.DataFrame(summaries["visitor_type"]).to_csv(OUT / "visitor_type_summary.csv", index=False)
    pd.DataFrame(summaries["weekend"]).to_csv(OUT / "weekend_summary.csv", index=False)

    month_summary = (
        df.groupby("Month", as_index=False)
        .agg(sessions=("Revenue", "size"), buyers=("Revenue", "sum"), conversion_rate=("Revenue", "mean"), avg_page_values=("PageValues", "mean"))
    )
    month_summary["month_sort"] = month_summary["Month"].map({m: i for i, m in enumerate(month_order)})
    month_summary = month_summary.sort_values("month_sort").drop(columns="month_sort")
    month_summary.to_csv(OUT / "month_summary.csv", index=False)

    numeric_features = [
        "Administrative", "Administrative_Duration", "Informational", "Informational_Duration",
        "ProductRelated", "ProductRelated_Duration", "BounceRates", "ExitRates", "PageValues", "SpecialDay",
        "OperatingSystems", "Browser", "Region", "TrafficType", "Weekend",
    ]
    categorical_features = ["Month", "VisitorType"]
    features = numeric_features + categorical_features
    x_train, x_test, y_train, y_test = train_test_split(
        df[features], df["Revenue"], test_size=0.25, random_state=42, stratify=df["Revenue"]
    )

    numeric_pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    prep = ColumnTransformer([("num", numeric_pipe, numeric_features), ("cat", categorical_pipe, categorical_features)])
    model = Pipeline([("prep", prep), ("logit", LogisticRegression(max_iter=1500, class_weight="balanced"))])
    model.fit(x_train, y_train)
    pred = model.predict_proba(x_test)[:, 1]
    metrics = {
        "test_rows": int(len(x_test)),
        "roc_auc": float(roc_auc_score(y_test, pred)),
        "average_precision": float(average_precision_score(y_test, pred)),
        "brier_score": float(brier_score_loss(y_test, pred)),
        "note": "Predictive metrics describe ranking/calibration and do not establish causal effects.",
    }
    (OUT / "model_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    prep_fitted = model.named_steps["prep"]
    feature_names = prep_fitted.get_feature_names_out()
    coefficients = model.named_steps["logit"].coef_[0]
    coef = pd.DataFrame({"feature": feature_names, "coefficient": coefficients})
    coef["odds_ratio"] = np.exp(coef["coefficient"])
    coef["abs_coefficient"] = coef["coefficient"].abs()
    coef.sort_values("abs_coefficient", ascending=False).to_csv(OUT / "logit_coefficients.csv", index=False)

    # Add a simple behavior comparison for business interpretation.
    buyer_behavior = df.groupby("Revenue", as_index=False).agg(
        product_pages=("ProductRelated", "mean"),
        product_duration=("ProductRelated_Duration", "mean"),
        bounce_rate=("BounceRates", "mean"),
        exit_rate=("ExitRates", "mean"),
        page_values=("PageValues", "mean"),
    )
    buyer_behavior.to_csv(OUT / "buyer_behavior_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    v = pd.DataFrame(summaries["visitor_type"])
    ax.bar(v["VisitorType"], v["conversion_rate"] * 100, color=["#2D6A9F", "#D9864A", "#A8B5C2"])
    ax.set_ylabel("Conversion rate (%)")
    ax.set_title("Conversion rate by visitor type")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(OUT / "conversion_by_visitor_type.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.plot(month_summary["Month"], month_summary["conversion_rate"] * 100, marker="o", color="#2D6A9F")
    ax.set_ylabel("Conversion rate (%)")
    ax.set_title("Monthly conversion trend")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(OUT / "conversion_by_month.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    b = buyer_behavior.copy()
    labels = ["Non-buyer", "Buyer"]
    x = np.arange(2)
    width = 0.22
    for i, (col, label) in enumerate([
        ("product_pages", "Product pages"),
        ("bounce_rate", "Bounce rate"),
        ("exit_rate", "Exit rate"),
        ("page_values", "Page values"),
    ]):
        vals = b[col].to_numpy(dtype=float)
        scale = vals / (vals.max() if vals.max() else 1)
        ax.bar(x + (i - 1.5) * width, scale, width=width, label=label)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Within-metric normalized level")
    ax.set_title("Behavior profile: buyers vs non-buyers")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "buyer_behavior_profile.png", bbox_inches="tight")
    plt.close(fig)

    metadata = {
        "source": "https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset",
        "rows": int(len(df)),
        "columns": list(df.columns),
        "target": "Revenue",
        "causal_boundary": "No treatment assignment; results are descriptive/predictive and not causal.",
    }
    (OUT / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
