"""Executive Portfolio Health Dashboard (Streamlit).

Consolidates status, metrics, risks, and roadmap data across multiple
programs into a single leadership view. Uses synthetic data.

Run:  streamlit run app.py
Optional: set OPENAI_API_KEY to enable AI-generated summaries.
"""

import os

import altair as alt
import pandas as pd
import streamlit as st

from data import MILESTONES, PROGRAMS, RISKS, TODAY, health_scores

st.set_page_config(page_title="Executive Portfolio Health", layout="wide")

RAG_COLORS = {"Green": "#22c55e", "Amber": "#f59e0b", "Red": "#ef4444"}
SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
scored = health_scores(PROGRAMS, RISKS)

st.sidebar.header("Filters")
lines = st.sidebar.multiselect(
    "Service line",
    sorted(scored["service_line"].unique()),
    default=sorted(scored["service_line"].unique()),
)
programs = scored[scored["service_line"].isin(lines)]
risks = RISKS[RISKS["program"].isin(programs["program"])]
milestones = MILESTONES[MILESTONES["program"].isin(programs["program"])]
st.sidebar.caption("All data on this dashboard is synthetic.")

# ---------------------------------------------------------------------------
# Header and KPIs
# ---------------------------------------------------------------------------
st.title("Executive Portfolio Health")
st.caption(f"Status as of {TODAY:%B %d, %Y}  |  Synthetic data for demonstration")

if programs.empty:
    st.warning("Select at least one service line.")
    st.stop()

high_open = int((risks["severity"] == "High").sum())
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Programs", len(programs))
c2.metric("On track (Green)", f"{(programs['status'] == 'Green').mean():.0%}")
c3.metric("Annual value", f"${programs['annual_value'].sum() / 1e6:.1f}M")
c4.metric("Hours saved / month", f"{programs['hours_saved_mo'].sum():,}")
c5.metric("Open high risks", high_open)

# ---------------------------------------------------------------------------
# Program health table
# ---------------------------------------------------------------------------
st.subheader("Program health")

table = programs[
    ["program", "service_line", "owner", "status", "health", "pct_complete",
     "burn_pct", "slip_days", "annual_value", "adoption"]
].rename(columns={
    "program": "Program", "service_line": "Service line", "owner": "Owner",
    "status": "RAG", "health": "Health score", "pct_complete": "% complete",
    "burn_pct": "% budget used", "slip_days": "Slip (days)",
    "annual_value": "Annual value ($)", "adoption": "Adoption %",
})


def color_rag(value):
    return f"background-color: {RAG_COLORS.get(value, 'white')}; color: white; font-weight: 600"


st.dataframe(
    table.style.map(color_rag, subset=["RAG"]).format({"Annual value ($)": "${:,.0f}"}),
    hide_index=True,
    width="stretch",
)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Progress vs. budget used")
    long = programs.melt(
        id_vars="program", value_vars=["pct_complete", "burn_pct"],
        var_name="measure", value_name="percent",
    )
    long["measure"] = long["measure"].map(
        {"pct_complete": "% complete", "burn_pct": "% budget used"}
    )
    st.altair_chart(
        alt.Chart(long).mark_bar().encode(
            y=alt.Y("program:N", title=None, sort=None),
            x=alt.X("percent:Q", title="Percent", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("measure:N", title=None),
            yOffset="measure:N",
            tooltip=["program", "measure", "percent"],
        ).properties(height=320),
        width="stretch",
    )

with right:
    st.subheader("Roadmap")
    gantt = alt.Chart(milestones).mark_bar(cornerRadius=3).encode(
        y=alt.Y("program:N", title=None),
        x=alt.X("start:T", title=None),
        x2="end:T",
        color=alt.Color("milestone:N", legend=None),
        tooltip=["program", "milestone", "start", "end"],
    )
    today_rule = alt.Chart(pd.DataFrame({"d": [TODAY]})).mark_rule(
        color="red", strokeDash=[4, 4]
    ).encode(x="d:T")
    st.altair_chart((gantt + today_rule).properties(height=320), width="stretch")
    st.caption("Dashed line = today")

# ---------------------------------------------------------------------------
# Risks and dependencies
# ---------------------------------------------------------------------------
st.subheader("Risks and dependencies")
risk_view = risks.assign(order=risks["severity"].map(SEVERITY_ORDER)).sort_values("order")
st.dataframe(
    risk_view.drop(columns="order").rename(columns={
        "program": "Program", "risk": "Risk", "severity": "Severity",
        "owner": "Owner", "depends_on": "Depends on",
    }),
    hide_index=True,
    width="stretch",
)

# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------
st.subheader("Executive summary")


def build_context() -> str:
    lines = []
    for _, p in programs.iterrows():
        lines.append(
            f"- {p['program']} ({p['service_line']}): {p['status']}, health {p['health']}, "
            f"{p['pct_complete']}% complete, {p['burn_pct']}% budget used, "
            f"{p['slip_days']} days slip, ${p['annual_value']:,.0f} annual value, "
            f"{p['adoption']}% adoption"
        )
    lines.append("Risks:")
    for _, r in risks[risks["severity"] == "High"].iterrows():
        dep = f" (depends on {r['depends_on']})" if r["depends_on"] else ""
        lines.append(f"- HIGH: {r['program']}: {r['risk']}{dep}")
    return "\n".join(lines)


def template_summary() -> str:
    worst = programs.sort_values("health").iloc[0]
    greens = int((programs["status"] == "Green").sum())
    return (
        f"{greens} of {len(programs)} programs are on track. The portfolio delivers an "
        f"estimated ${programs['annual_value'].sum() / 1e6:.1f}M in annual value and "
        f"{programs['hours_saved_mo'].sum():,} hours saved per month. "
        f"The program needing the most attention is {worst['program']} "
        f"({worst['status']}, {worst['slip_days']} days behind, "
        f"{worst['burn_pct']}% of budget used at {worst['pct_complete']}% complete). "
        f"There are {high_open} open high-severity risks, several tied to the data "
        f"platform migration, which is the key cross-program dependency."
    )


def ai_summary(context: str) -> str:
    from openai import OpenAI  # imported lazily so the app runs without it

    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You write concise executive summaries of a technology program "
                "portfolio for senior leadership. Lead with overall health, then the "
                "biggest risks and cross-program dependencies, then one recommended "
                "action. Use plain business language, under 150 words, no jargon."
            )},
            {"role": "user", "content": context},
        ],
    )
    return resp.choices[0].message.content


if st.button("Generate executive summary"):
    if os.getenv("OPENAI_API_KEY"):
        try:
            with st.spinner("Generating..."):
                st.write(ai_summary(build_context()))
            st.caption("AI-generated from the data above.")
        except Exception as exc:
            st.error(f"AI summary failed ({exc}). Showing the template summary instead.")
            st.write(template_summary())
    else:
        st.write(template_summary())
        st.caption("Template summary. Set OPENAI_API_KEY to enable AI-generated summaries.")
