"""Chart functions with one consistent style (Plotly, dark 'night road' theme).

Maps use Plotly's built-in geo projection (no online map tiles), so they render offline and on any host.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from utils.prep import AGE_ORDER, LOCKDOWNS
from utils.style import AMBER, BG, BORDER, GREY, MUTED, RED, SURFACE, TEXT

FONT = "Roboto, sans-serif"
SOURCE_NOTE = "Source: ONISR, BAAC 2019–2024 (data.gouv.fr)"
HEAT_SCALE = [[0, "#1D2230"], [0.35, "#6B4A12"], [0.7, AMBER], [1, RED]]


def _style(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    """Shared look: title + source as subtitle, transparent background, readable grid."""
    fig.update_layout(
        title=dict(text=title, font=dict(family="Plus Jakarta Sans, sans-serif", size=17, color=TEXT),
                   subtitle=dict(text=SOURCE_NOTE, font=dict(size=11, color=MUTED)), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=TEXT, size=13), height=height,
        margin=dict(l=10, r=10, t=95, b=40),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(family=FONT, color=TEXT)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER)
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER)
    return fig


def _pad_x(fig: go.Figure, values, factor: float = 1.2) -> None:
    """Leave room on the right of horizontal bars so value labels are not clipped."""
    vals = pd.to_numeric(pd.Series(values), errors="coerce")
    top = float(vals.max()) if vals.notna().any() else 1.0
    fig.update_xaxes(range=[0, top * factor if top > 0 else 1])


# ---------------------------------------------------------------- overview
def trend_chart(m: pd.DataFrame, baseline: float) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=m["month"], y=m["accidents"], name="Accidents per month", marker_color=GREY, opacity=0.55,
                hovertemplate="%{x|%b %Y}<br>%{y:,} accidents<extra></extra>")
    fig.add_scatter(x=m["month"], y=m["lethality"], name="Lethality (killed per 100 victims)", yaxis="y2",
                    mode="lines+markers", line=dict(color=RED, width=2.5), marker=dict(size=4),
                    customdata=m[["killed", "victims"]],
                    hovertemplate="%{x|%b %Y}<br>Lethality %{y:.2f}<br>%{customdata[0]:,} killed / "
                                  "%{customdata[1]:,} victims<extra></extra>")
    lo, hi = m["month"].min(), m["month"].max()
    for i, (start, end) in enumerate(LOCKDOWNS):
        s, e = pd.Timestamp(start), pd.Timestamp(end)
        if e >= lo and s <= hi:
            fig.add_vrect(x0=s, x1=e, fillcolor=AMBER, opacity=0.15, line_width=0,
                          annotation_text="Lockdowns" if i == 0 else "", annotation_position="top left",
                          annotation_font_color=AMBER)
    fig.add_hline(y=baseline, yref="y2", line=dict(color=RED, dash="dot", width=1), opacity=0.45,
                  annotation_text=f"national average {baseline:.2f}", annotation_font_color=RED,
                  annotation_position="bottom left")
    fig.update_layout(yaxis=dict(title="Accidents per month", rangemode="tozero"),
                      yaxis2=dict(title="Killed per 100 victims", overlaying="y", side="right",
                                  rangemode="tozero", showgrid=False, color=RED),
                      xaxis=dict(title=None), bargap=0.15)
    return _style(fig, "Crashes fell during lockdowns, lethality did not", height=470)


# ---------------------------------------------------------------- H1
def heatmap(g: pd.DataFrame) -> go.Figure:
    pivot = g.pivot(index="weekday", columns="hour", values="lethality")
    vic = g.pivot(index="weekday", columns="hour", values="victims").reindex_like(pivot)
    kil = g.pivot(index="weekday", columns="hour", values="killed").reindex_like(pivot)
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=[int(h) for h in pivot.columns], y=[str(d) for d in pivot.index],
        colorscale=HEAT_SCALE,
        colorbar=dict(title=dict(text="Killed per<br>100 victims", font=dict(size=11)), thickness=12),
        customdata=np.dstack([vic.values.astype(float), kil.values.astype(float)]),
        hovertemplate="%{y}, %{x}h<br>Lethality %{z:.1f}<br>%{customdata[1]:,.0f} killed / "
                      "%{customdata[0]:,.0f} victims<extra></extra>", xgap=2, ygap=2))
    fig.update_yaxes(autorange="reversed", title=None, showgrid=False)
    fig.update_xaxes(title="Hour of the crash", showgrid=False, tickmode="array",
                     tickvals=list(range(0, 24, 3)), ticktext=[f"{h}h" for h in range(0, 24, 3)])
    return _style(fig, "Lethality by hour and weekday", height=420)


def light_bars(s: pd.DataFrame, baseline: float) -> go.Figure:
    s = s[s["light"] != "Unknown"].sort_values("lethality")
    colors = [RED if "Night" in str(x) else GREY for x in s["light"]]
    labels = s["light"].astype(str).str.replace("Night, ", "Night: ", regex=False)
    fig = go.Figure(go.Bar(
        x=s["lethality"], y=labels, orientation="h", marker_color=colors,
        text=s["lethality"].map(lambda x: f"{x:.1f}"), textposition="outside", cliponaxis=False,
        customdata=s[["killed", "victims", "pct_accidents"]],
        hovertemplate="%{y}<br>Lethality %{x:.2f}<br>%{customdata[0]:,} killed / %{customdata[1]:,} victims"
                      "<br>%{customdata[2]:.1f}% of accidents<extra></extra>"))
    fig.add_vline(x=baseline, line=dict(color=MUTED, dash="dot", width=1), opacity=0.45, annotation_text="avg",
                  annotation_font_color=MUTED, annotation_position="top")
    _pad_x(fig, s["lethality"])
    fig.update_xaxes(title="Killed per 100 victims")
    fig.update_yaxes(title=None)
    return _style(fig, "Lethality by lighting", height=420)


# ---------------------------------------------------------------- H2
def day_type_bars(d: pd.DataFrame) -> go.Figure:
    ordinary = d.loc[d["day_type"] == "Ordinary day", "killed_per_day"]
    ref = float(ordinary.iloc[0]) if len(ordinary) else None
    d = d.sort_values("killed_per_day")
    colors = [GREY if t == "Ordinary day" else (RED if ref and v > ref else AMBER)
              for t, v in zip(d["day_type"], d["killed_per_day"])]
    fig = go.Figure(go.Bar(
        x=d["killed_per_day"], y=d["day_type"], orientation="h", marker_color=colors,
        text=[f"{v:.1f}   (n = {int(n)} days)" for v, n in zip(d["killed_per_day"], d["days"])],
        textposition="outside", cliponaxis=False,
        customdata=d[["accidents_per_day", "lethality"]],
        hovertemplate="%{y}<br>%{x:.2f} killed per day<br>%{customdata[0]:.0f} accidents per day"
                      "<br>Lethality %{customdata[1]:.2f}<extra></extra>"))
    if ref:
        fig.add_vline(x=ref, line=dict(color=TEXT, dash="dot", width=1), opacity=0.45, annotation_text="ordinary day",
                      annotation_font_color=TEXT, annotation_position="top")
    _pad_x(fig, d["killed_per_day"], 1.35)
    fig.update_xaxes(title="People killed per day (average)")
    fig.update_yaxes(title=None)
    return _style(fig, "Deaths per day: festive days vs an ordinary day", height=420)


# ---------------------------------------------------------------- H3
def road_share(r: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(y=r["road"].astype(str), x=r["pct_accidents"], name="% of accidents", orientation="h",
                marker_color=GREY, hovertemplate="%{y}<br>%{x:.1f}% of accidents<extra></extra>")
    fig.add_bar(y=r["road"].astype(str), x=r["pct_killed"], name="% of people killed", orientation="h",
                marker_color=RED, customdata=r[["lethality", "killed"]],
                text=r["lethality"].map(lambda x: f"lethality {x:.1f}"), textposition="outside", cliponaxis=False,
                hovertemplate="%{y}<br>%{x:.1f}% of deaths (%{customdata[1]:,})<br>"
                              "Lethality %{customdata[0]:.2f}<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.25)
    _pad_x(fig, pd.concat([r["pct_accidents"], r["pct_killed"]]), 1.25)
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_xaxes(title="Share of the total (%)", ticksuffix="%")
    return _style(fig, "Share of crashes vs share of deaths, by road type", height=450)


# ---------------------------------------------------------------- H4
def age_shares(a: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=a["age_group"].astype(str), y=a["pct_victims"], name="% of victims", marker_color=GREY,
                hovertemplate="Age %{x}<br>%{y:.1f}% of victims<extra></extra>")
    fig.add_bar(x=a["age_group"].astype(str), y=a["pct_killed"], name="% of people killed", marker_color=RED,
                hovertemplate="Age %{x}<br>%{y:.1f}% of deaths<extra></extra>")
    fig.update_layout(barmode="group")
    fig.update_xaxes(title="Age group", categoryorder="array", categoryarray=AGE_ORDER)
    fig.update_yaxes(title="Share of the total (%)", ticksuffix="%")
    return _style(fig, "Who gets hurt vs who gets killed", height=420)


def age_lethality(a: pd.DataFrame, baseline: float) -> go.Figure:
    colors = [RED if x > baseline else GREY for x in a["lethality"]]
    fig = go.Figure(go.Bar(
        x=a["age_group"].astype(str), y=a["lethality"], marker_color=colors,
        text=a["lethality"].map(lambda x: f"{x:.1f}"), textposition="outside", cliponaxis=False,
        customdata=a[["killed", "victims"]],
        hovertemplate="Age %{x}<br>Lethality %{y:.2f}<br>%{customdata[0]:,} killed / "
                      "%{customdata[1]:,} victims<extra></extra>"))
    fig.add_hline(y=baseline, line=dict(color=MUTED, dash="dot", width=1), opacity=0.45, annotation_text="national average",
                  annotation_font_color=MUTED, annotation_position="top left")
    top = float(a["lethality"].max()) if len(a) else 1
    fig.update_yaxes(title="Killed per 100 victims", range=[0, max(top, baseline) * 1.2])
    fig.update_xaxes(title="Age group", categoryorder="array", categoryarray=AGE_ORDER)
    return _style(fig, "Chance of dying once hurt, by age (red = above average)", height=420)


# ---------------------------------------------------------------- H6 maps (offline geo projection)
def _geo_layout(fig: go.Figure) -> None:
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)",
                    projection_type="mercator")
    fig.update_layout(margin=dict(l=0, r=0, t=95, b=0))


def choropleth(d: pd.DataFrame, geojson: dict, metric: str) -> go.Figure:
    d = d[~d["dep"].str.startswith(("97", "98"))].copy()
    if metric == "lethality":
        d["value"] = d["lethality"].where(d["reliable"])
        title, cbar = "Lethality by département", "Killed per<br>100 victims"
    else:
        d["value"] = d["killed"]
        title, cbar = "People killed by département", "People<br>killed"
    fig = go.Figure(go.Choropleth(
        geojson=geojson, locations=d["dep"], featureidkey="properties.code", z=d["value"], colorscale=HEAT_SCALE,
        marker_line_color=BG, marker_line_width=0.6,
        colorbar=dict(title=dict(text=cbar, font=dict(size=11)), thickness=12),
        customdata=d[["name", "accidents", "victims", "killed", "lethality"]],
        hovertemplate="<b>%{customdata[0]}</b> (%{location})<br>%{customdata[1]:,.0f} accidents<br>"
                      "%{customdata[3]:,} killed / %{customdata[2]:,} victims<br>"
                      "Lethality %{customdata[4]:.2f}<extra></extra>"))
    _style(fig, title, height=600)
    _geo_layout(fig)
    return fig


def fatal_points(p: pd.DataFrame, geojson: dict) -> go.Figure:
    codes = [f["properties"]["code"] for f in geojson["features"]]
    fig = go.Figure(go.Choropleth(geojson=geojson, locations=codes, featureidkey="properties.code",
                                  z=[0] * len(codes), colorscale=[[0, SURFACE], [1, SURFACE]], showscale=False,
                                  marker_line_color=BORDER, marker_line_width=0.6, hoverinfo="skip"))
    fig.add_trace(go.Scattergeo(
        lat=p["lat"], lon=p["lon"], mode="markers",
        marker=dict(size=2.5 + 1.5 * p["n_killed"].clip(upper=4), color=RED, opacity=0.45, line_width=0),
        customdata=p[["date_str", "road_type", "n_killed", "light"]],
        hovertemplate="%{customdata[0]}<br>%{customdata[1]}, %{customdata[3]}<br>"
                      "%{customdata[2]} killed<extra></extra>"))
    _style(fig, f"Every fatal crash in mainland France ({len(p):,} locations)", height=600)
    _geo_layout(fig)
    return fig


def ranking(d: pd.DataFrame, n: int = 10) -> go.Figure:
    d = d[d["reliable"]].sort_values("lethality")
    sel = pd.concat([d.head(n), d.tail(n)]).drop_duplicates("dep")
    colors = [RED if x >= sel["lethality"].median() else GREY for x in sel["lethality"]]
    fig = go.Figure(go.Bar(
        x=sel["lethality"], y=sel["name"] + " (" + sel["dep"] + ")", orientation="h", marker_color=colors,
        text=sel["lethality"].map(lambda x: f"{x:.1f}"), textposition="outside", cliponaxis=False,
        customdata=sel[["killed", "victims"]],
        hovertemplate="%{y}<br>Lethality %{x:.2f}<br>%{customdata[0]:,} killed / %{customdata[1]:,} victims"
                      "<extra></extra>"))
    _pad_x(fig, sel["lethality"], 1.15)
    fig.update_xaxes(title="Killed per 100 victims")
    fig.update_yaxes(title=None, tickfont=dict(size=11))
    return _style(fig, "Lethality ranking (lowest and highest 10)", height=600)


# ---------------------------------------------------------------- data quality
def missingness_bars(m: pd.DataFrame) -> go.Figure:
    m = m[m["unknown_pct"] > 0].sort_values("unknown_pct").tail(15)
    labels = m["table"] + "." + m["column"]
    fig = go.Figure(go.Bar(x=m["unknown_pct"], y=labels, orientation="h", marker_color=AMBER,
                           text=m["unknown_pct"].map(lambda x: f"{x:.1f}%"), textposition="outside",
                           cliponaxis=False, hovertemplate="%{y}<br>%{x:.2f}% not recorded<extra></extra>"))
    _pad_x(fig, m["unknown_pct"], 1.15)
    fig.update_xaxes(title="Share of rows not recorded (empty or code -1), %", ticksuffix="%")
    fig.update_yaxes(title=None)
    return _style(fig, "Raw columns with the most missing values (top 15)", height=500)
