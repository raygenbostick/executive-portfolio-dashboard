"""Synthetic portfolio data and health scoring for the executive dashboard.

All programs, people, and numbers are fictional.
"""

import pandas as pd

TODAY = pd.Timestamp("2026-10-07")

PROGRAMS = pd.DataFrame(
    [
        # name, service_line, owner, budget, spend, pct_complete, slip_days, annual_value, hours_saved_mo, adoption
        ("Data Platform Migration", "Data & Analytics", "A. Rivera", 2_400_000, 1_900_000, 72, 18, 1_800_000, 900, 64),
        ("GenAI Customer Assistant", "AI", "J. Patel", 1_200_000, 550_000, 48, 0, 2_100_000, 1_400, 41),
        ("Cloud Cost Optimization", "Cloud", "M. Chen", 800_000, 500_000, 65, 3, 1_300_000, 300, 88),
        ("BI Self-Service Rollout", "BI", "S. Okafor", 1_000_000, 820_000, 60, 25, 700_000, 1_100, 52),
        ("Data Governance & Quality", "Data & Analytics", "L. Nguyen", 600_000, 300_000, 55, 0, 450_000, 250, 70),
        ("Customer 360 Analytics", "BI", "D. Brooks", 1_500_000, 1_100_000, 58, 12, 1_600_000, 600, 47),
    ],
    columns=[
        "program", "service_line", "owner", "budget", "spend", "pct_complete",
        "slip_days", "annual_value", "hours_saved_mo", "adoption",
    ],
)

RISKS = pd.DataFrame(
    [
        ("Data Platform Migration", "Legacy ETL cutover slips past freeze window", "High", "A. Rivera", "Customer 360 Analytics"),
        ("Data Platform Migration", "Key engineer leaving mid-program", "Medium", "A. Rivera", ""),
        ("GenAI Customer Assistant", "Model output quality below target in edge cases", "Medium", "J. Patel", ""),
        ("GenAI Customer Assistant", "Security review of third-party API pending", "High", "J. Patel", "Data Governance & Quality"),
        ("Cloud Cost Optimization", "Reserved-instance commitments lock in capacity", "Low", "M. Chen", ""),
        ("BI Self-Service Rollout", "Dashboards depend on migrated datasets", "High", "S. Okafor", "Data Platform Migration"),
        ("BI Self-Service Rollout", "Low training attendance in two business units", "Medium", "S. Okafor", ""),
        ("Data Governance & Quality", "Data owners not yet named for 3 domains", "Medium", "L. Nguyen", ""),
        ("Customer 360 Analytics", "Source system access delayed", "High", "D. Brooks", "Data Platform Migration"),
        ("Customer 360 Analytics", "Overlapping scope with BI rollout", "Low", "D. Brooks", "BI Self-Service Rollout"),
    ],
    columns=["program", "risk", "severity", "owner", "depends_on"],
)

MILESTONES = pd.DataFrame(
    [
        ("Data Platform Migration", "Phase 2 migration", "2026-08-01", "2026-11-30"),
        ("Data Platform Migration", "Legacy decommission", "2026-12-01", "2027-02-28"),
        ("GenAI Customer Assistant", "Pilot with 2 business units", "2026-09-01", "2026-12-15"),
        ("GenAI Customer Assistant", "Broader rollout", "2027-01-05", "2027-04-30"),
        ("Cloud Cost Optimization", "Rightsizing wave 2", "2026-09-15", "2026-11-15"),
        ("BI Self-Service Rollout", "Training and certification", "2026-09-01", "2026-12-20"),
        ("BI Self-Service Rollout", "Dataset catalog launch", "2027-01-10", "2027-03-31"),
        ("Data Governance & Quality", "Data ownership model", "2026-10-01", "2026-12-31"),
        ("Customer 360 Analytics", "Unified customer model", "2026-08-15", "2027-01-31"),
        ("Customer 360 Analytics", "Executive reporting layer", "2027-02-01", "2027-05-15"),
    ],
    columns=["program", "milestone", "start", "end"],
)
MILESTONES["start"] = pd.to_datetime(MILESTONES["start"])
MILESTONES["end"] = pd.to_datetime(MILESTONES["end"])


def health_scores(programs: pd.DataFrame, risks: pd.DataFrame) -> pd.DataFrame:
    """Add budget burn, health score (0-100), and RAG status to each program.

    Score = 100, minus a penalty for spending ahead of progress, minus
    schedule slip, minus open high-severity risks.
    """
    df = programs.copy()
    df["burn_pct"] = (df["spend"] / df["budget"] * 100).round(1)
    overspend = (df["burn_pct"] - df["pct_complete"]).clip(lower=0)
    high_risks = (
        risks[risks["severity"] == "High"].groupby("program").size()
        .reindex(df["program"]).fillna(0).to_numpy()
    )
    score = 100 - 1.2 * overspend - 1.0 * df["slip_days"] - 6 * high_risks
    df["health"] = score.clip(0, 100).round(0).astype(int)
    df["status"] = pd.cut(
        df["health"], bins=[-1, 59, 79, 100], labels=["Red", "Amber", "Green"]
    ).astype(str)
    df["high_risks"] = high_risks.astype(int)
    return df
