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

    # Keep a separate list of unique nutrients
    unique_nutrients = df['nutrient'].dropna().unique()

    # Ensure all dates are represented in the data, even those without data points
    date_range = pd.date_range(start=df['record_date'].min(), end=df['record_date'].max())
    all_dates_df = pd.DataFrame(date_range, columns=['record_date'])
    all_dates_df['day_month'] = all_dates_df['record_date'].dt.strftime('%d-%m')

    # Merge the complete date range with the original data
    df_merged = pd.merge(all_dates_df, df, on='day_month', how='left')

    # Ensure nutrient categories after merge do not contain nulls
    df_merged['nutrient'] = pd.Categorical(df_merged['nutrient'], categories=unique_nutrients)

    # Cap values at 100 for coloring and use NaN for days without data
    df_merged['actual_over_recommended_intake_percent'] = df_merged['actual_over_recommended_intake_percent'].clip(upper=100)

    # Create the square heatmap plot
    square_heatmap = alt.Chart(df_merged).mark_rect().encode(
        x=alt.X('day_month:O', axis=alt.Axis(labelAngle=270), title='Date', sort=all_dates_df['day_month'].tolist()),
        y=alt.Y('nutrient:N', title='Nutrient', sort='ascending'),
        color=alt.condition(
            alt.datum.actual_over_recommended_intake_percent >= 1,  # Apply color only for values starting from 1
            alt.Color('actual_over_recommended_intake_percent:Q',
                      title='Intake Percentage', 
                      scale=alt.Scale(domain=[1, 100], scheme='goldgreen'),
                      legend=alt.Legend(orient='right', titleLimit=0, gradientLength=370, gradientThickness=20)  # Adjust legend size
            ),
            alt.value(None)  # Do not color boxes with values below 1
        ),
        tooltip=[
            alt.Tooltip('day_month', title='Date'),
            alt.Tooltip('nutrient', title='Nutrient'),
            alt.Tooltip('actual_over_recommended_intake_percent', title='Intake Percentage')
        ]
    ).properties(
        width=1000,
        height=600,
        title=alt.TitleParams(
            text="Historical Nutrient Intake Tracker",  # Title text
            anchor='middle'  # Center alignment
        )
    ).configure_view(
        strokeWidth=0
    )

    # Display the chart in the specified layout position
    layout_position.altair_chart(square_heatmap)


