import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


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
    unsaturated_colors = px.colors.qualitative.Pastel
    unsaturated_blue = "#7f7fbf"
    unsaturated_green = "#7fbf7f"
    unsaturated_red = "#cf6f6f"
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
