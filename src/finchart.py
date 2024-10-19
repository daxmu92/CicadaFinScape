import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from palettable.colorbrewer.qualitative import Pastel1_9, Set3_12, Pastel2_8, Paired_12

unsaturated_colors = px.colors.qualitative.Pastel
morandi_like_colors = Pastel1_9.hex_colors[1:] + Pastel1_9.hex_colors[:1] + Pastel2_8.hex_colors


def allocation_pie(df: pd.DataFrame) -> go.Figure:
    colors = morandi_like_colors + unsaturated_colors
    df = df.sort_values(by="NET_WORTH", ascending=False)
    labels = [f"{a}-{s}" if a != s else s for a, s in zip(df["ACCOUNT"], df["SUBACCOUNT"])]
    fig = go.Figure(
        go.Pie(labels=labels,
               values=df["NET_WORTH"],
               textposition='inside',
               textinfo='label+value+percent',
               hoverinfo='label+value+percent',
               showlegend=True,
               marker=dict(colors=colors)))
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        width=400,
        height=600,
    )
    fig.update_traces(textfont_size=12)
    return fig


def profit_bar(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values(by="PROFIT", ascending=True)
    df = df[df["PROFIT"] != 0]
    colors = morandi_like_colors + unsaturated_colors
    # colors = Paired_12.hex_colors

    names = df["ACCOUNT"] + "-" + df["SUBACCOUNT"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["PROFIT"],
            y=names,
            text=df["PROFIT"].apply(lambda x: f"¥{x:,.0f}"),
            textposition='outside',
            textfont=dict(size=10),
            hoverinfo='y+text',
            name="profit",
            orientation='h',
            width=0.6,
            marker=dict(color=colors[:len(df)][::-1]),
            showlegend=False,
        ))

    fig.update_layout(barmode='group',
                      bargap=0.05,
                      bargroupgap=0.02,
                      xaxis_title="Profit",
                      yaxis_title="Asset",
                      margin=dict(l=50, r=50, t=40, b=20),
                      width=1000,
                      height=600,
                      uniformtext_minsize=8,
                      uniformtext_mode='hide',
                      showlegend=False,
                      yaxis=dict(tickmode='linear', tick0=0, dtick=1, tickfont=dict(size=12)))

    return fig


def io_flow_chart(tran_df: pd.DataFrame, total_inflow: float) -> tuple[go.Figure, dict]:
    total_income = tran_df[tran_df["TYPE"] == "INCOME"]["VALUE"].sum()
    tracked_outlay = tran_df[tran_df["TYPE"] == "OUTLAY"]["VALUE"].sum()
    total_outlay = total_income - total_inflow
    untracked_outlay = total_outlay - tracked_outlay

    income_categories = tran_df[tran_df["TYPE"] == "INCOME"].groupby("CAT")["VALUE"].sum().sort_values(ascending=False)
    outlay_categories = tran_df[tran_df["TYPE"] == "OUTLAY"].groupby("CAT")["VALUE"].sum().sort_values(ascending=False)

    categories = ['Income', 'Tracked Outlay', 'Untracked Outlay', 'Net']
    values = [total_income, -tracked_outlay, -untracked_outlay, total_inflow]

    # Create the main waterfall chart
    unsaturated_colors = Pastel2_8.hex_colors
    unsaturated_red = Pastel1_9.hex_colors[0]
    unsaturated_blue = Pastel1_9.hex_colors[1]
    unsaturated_green = Pastel1_9.hex_colors[2]
    width = 0.7
    fig = go.Figure(
        go.Waterfall(
            name="Waterfall",
            orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=categories,
            textposition="outside",
            text=[f"¥{x:,.0f}" for x in values],
            y=values,
            connector={"line": {
                "color": "rgb(63, 63, 63)"
            }},
            increasing={"marker": {
                "color": unsaturated_blue
            }},  # Unsaturated green for income
            decreasing={"marker": {
                "color": unsaturated_red
            }},  # Unsaturated red for outlay
            totals={"marker": {
                "color": unsaturated_green
            }},  # Unsaturated blue for net
            width=width))

    # Add income breakdown
    for i, (category, value) in enumerate(income_categories.items()):
        fig.add_trace(
            go.Bar(
                x=['Income'],
                y=[value],
                name=category,
                marker_color=unsaturated_colors[i % len(unsaturated_colors)],  # Use different colors for each category
                text=f"¥{value:,.0f}",
                textposition='inside',
                width=width,
            ))

    # Add outlay breakdown, from top to bottom
    cumulative_outlay = 0
    for i, (category, value) in enumerate(outlay_categories.items()):
        fig.add_trace(
            go.Bar(
                x=['Tracked Outlay'],
                y=[-value],  # Start from the top (total income)
                base=[total_income - cumulative_outlay],  # Adjust the base to stack from top
                name=category,
                marker_color=unsaturated_colors[i + len(income_categories) % len(unsaturated_colors)],
                text=f"¥{value:,.0f}",
                textposition='inside',
                width=width,
            ))
        cumulative_outlay += value

    # Update layout
    fig.update_layout(
        barmode='stack',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(
            title='Amount (¥)',
            gridcolor='lightgray',
            zerolinecolor='lightgray',
        ),
        xaxis=dict(
            title='Categories',
            tickangle=0,
        ),
        margin=dict(l=80, r=80, t=20, b=20),
        height=450,
    )

    config = {'displayModeBar': False}
    return fig, config


def asset_line(df: pd.DataFrame, kind: str) -> go.Figure:
    fig = px.line(df, x="DATE", y=kind, line_shape="spline")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=kind,
        # Hide plotly buttons
        updatemenus=[],
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),  # Adjust top margin
        height=400  # Adjust overall height of the chart
    )
    return fig
