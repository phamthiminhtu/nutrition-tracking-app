import altair as alt
import streamlit as st

def nutrient_intake_vs_recommended_horizontal_bar_chart(df):

    # Set max intake difference percentage to 100
    df.loc[df['intake_diff_percent'] > 100, 'intake_diff_percent'] = 100

    # Set graph title
    title = alt.TitleParams("Nutrient Intake Tracker", anchor="middle")

    # Set up the bar graph
    base = alt.Chart(df, title=title).mark_bar().encode(
        x=alt.X('intake_diff_percent:Q', title='percentage', scale=alt.Scale(domain=[0, 100], clamp=True)),
        y=alt.Y('nutrient:O', title='').sort('-x'),
        color = alt.Color('intake_diff_percent:Q', legend= None, scale=alt.Scale(scheme='goldgreen', domain=[0, 100]))
    ).properties(width=800)

    base.mark_bar() + base.mark_text(align='left', dx=2)

    # Show graph
    st.altair_chart(base)