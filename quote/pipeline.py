"""Sales pipeline KPIs from a CRM opportunity export."""
import pandas as pd

# Probability that a deal in this stage will be won (used for the weighted pipeline).
STAGE_PROB = {"Qualification": 0.2, "Proposal": 0.5, "Negotiation": 0.75, "Won": 1.0, "Lost": 0.0}
OPEN_STAGES = ["Qualification", "Proposal", "Negotiation"]


def load_crm(path):
    df = pd.read_csv(path, parse_dates=["created", "closed"])
    unknown = set(df["stage"]) - set(STAGE_PROB)
    if unknown:
        raise ValueError(f"Unknown CRM stages: {sorted(unknown)}")
    return df


def kpis(df):
    closed = df[df["stage"].isin(["Won", "Lost"])]
    won = closed[closed["stage"] == "Won"]
    open_ = df[df["stage"].isin(OPEN_STAGES)]
    cycle = (won["closed"] - won["created"]).dt.days
    return {
        "win_rate": round(len(won) / len(closed), 3) if len(closed) else 0.0,
        "won_value_czk": int(won["value_czk"].sum()),
        "open_pipeline_czk": int(open_["value_czk"].sum()),
        "weighted_pipeline_czk": int((open_["value_czk"] * open_["stage"].map(STAGE_PROB)).sum()),
        "avg_sales_cycle_days": round(float(cycle.mean()), 1) if len(cycle) else None,
    }


def by_owner(df):
    df = df.assign(weighted=df["value_czk"] * df["stage"].map(STAGE_PROB))
    return (df.groupby("owner")
              .agg(deals=("opportunity_id", "count"),
                   won=("stage", lambda s: (s == "Won").sum()),
                   pipeline_czk=("weighted", "sum"))
              .reset_index())
