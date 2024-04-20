import textwrap
import numpy as np
import altair as alt
import streamlit as st
import pandas as pd

def users_recommended_intake_chart(df, layout_position=st):
    # Cap intake values at 100
    df['Intake Display'] = df['Actual intake / Recommended intake (%)'].clip(upper=100)

    # Set graph title
    title = alt.TitleParams("Nutrient Intake Tracker", anchor="middle")

    # Set up the bar graph
    bar_chart = alt.Chart(df, title=title).mark_bar().encode(
        x=alt.X('Intake Display:Q', title='Intake Percentage', scale=alt.Scale(domain=[0, 100], clamp=True)),
        y=alt.Y('Nutrient:O', title='Nutrients').sort('x'),
        color=alt.Color('Intake Display:Q', legend=None, scale=alt.Scale(scheme='goldgreen')),
        tooltip=[
            alt.Tooltip('Nutrient:N', title='Nutrient:'),
            alt.Tooltip('Actual intake / Recommended intake (%):Q', title='Actual Intake Percentage:')
        ]
    ).properties(width=800)

    # Show graph in the Streamlit layout position
    layout_position.altair_chart(bar_chart)

def user_historical_square_heatmap(df, layout_position):
    # Convert 'record_date' to datetime and extract 'dd-mm' format for plotting
    df['record_date'] = pd.to_datetime(df['record_date'])
    df['day_month'] = df['record_date'].dt.strftime('%d-%m')

    # Only keep rows where 'nutrient' is not null to ensure no null nutrient entries are created
    df_clean = df.dropna(subset=['nutrient'])

    # Ensure all dates are represented in the data, even those without data points
    date_range = pd.date_range(df_clean['record_date'].min(), df_clean['record_date'].max())
    all_dates = pd.DataFrame(date_range, columns=['record_date'])
    all_dates['day_month'] = all_dates['record_date'].dt.strftime('%d-%m')

    # Merge the complete date range with the cleaned data on 'day_month' using 'outer' join to keep all dates
    df_merged = pd.merge(all_dates, df_clean, on='day_month', how='outer')

    # Drop rows where both nutrient and actual_over_recommended_intake_percent are null
    df_merged = df_merged.dropna(subset=['nutrient', 'actual_over_recommended_intake_percent'], how='all')

    # Cap values at 100 for coloring and fill missing entries
    df_merged['capped_intake_percent'] = df_merged['actual_over_recommended_intake_percent'].clip(upper=100).fillna(0)

    # Define categories based on the original nutrient data to avoid introducing 'null' or '-1' categories
    nutrient_categories = pd.Categorical(df_clean['nutrient'].unique())
    df_merged['nutrient'] = pd.Categorical(df_merged['nutrient'], categories=nutrient_categories)

    # Create the square heatmap plot
    square_heatmap = alt.Chart(df_merged).mark_rect(
        stroke='black',  # Black border around each square
        strokeWidth=0.5  # Border width
    ).encode(
        x=alt.X('day_month:O', title='Date', axis=alt.Axis(labelAngle=270), sort=all_dates['day_month'].tolist()),  # Sorted by date
        y=alt.Y('nutrient:N', title='Nutrient', sort='ascending'),
        color=alt.Color('capped_intake_percent:Q', 
                    scale=alt.Scale(domain=[0, 100], scheme='goldgreen'),
                    title=textwrap.wrap('Recommended Intake Achieved (%)', width=20)),  # Custom color legend title
        tooltip=[
            alt.Tooltip('nutrient', title='Nutrient:'),
            alt.Tooltip('day_month', title='Date:'),
            alt.Tooltip('actual_over_recommended_intake_percent', title='Intake Percentage:')
        ]
    ).properties(
        width=1000,
        height=800,
        title=alt.TitleParams('Historical Nutrient Intake Tracker', anchor='middle')
    ).configure_view(
        strokeWidth=0
    )

    # Show the chart in the specified layout position
    layout_position.altair_chart(square_heatmap)

