import altair as alt
import streamlit as st

def users_recommended_intake_chart(df, layout_position=st):

    # Set max intake difference percentage to 100
    df.loc[df['Actual intake / Recommended intake (%)'] > 100, 'Actual intake / Recommended intake (%)'] = 100

    # Set graph title
    title = alt.TitleParams("Nutrient Intake Tracker", anchor="middle")

    # Set up the bar graph
    base = alt.Chart(df, title=title).mark_bar().encode(
        x=alt.X('Actual intake / Recommended intake (%):Q', title='percentage', scale=alt.Scale(domain=[0, 100], clamp=True)),
        y=alt.Y('Nutrient:O', title='').sort('x'),
        color = alt.Color('Actual intake / Recommended intake (%):Q', legend= None, scale=alt.Scale(scheme='goldgreen', domain=[0, 100]))
    ).properties(width=800)

    base.mark_bar() + base.mark_text(align='left', dx=2)

    # Show graph
    layout_position.altair_chart(base)



## Feel free to delete the codes below

# def user_historical_data_chart(df, layout_position=st):

#     # Set max intake difference percentage to 100
#     df.loc[df['actual_over_recommended_intake_percent'] > 100, 'actual_over_recommended_intake_percent'] = 100

#     # Set graph title
#     title = alt.TitleParams("Historical Nutrient Intake Tracker", anchor="middle")

#     # Set up the bar graph
#     base = alt.Chart(df, title=title).mark_bar().encode(
#         x=alt.X('actual_over_recommended_intake_percent:Q', title='percentage', scale=alt.Scale(domain=[0, 100], clamp=True)),
#         y=alt.Y('nutrient:O', title='').sort('x'),
#         color = alt.Color('actual_over_recommended_intake_percent:Q', legend= None, scale=alt.Scale(scheme='goldgreen', domain=[0, 100]))
#     ).properties(width=800)

#     base.mark_bar() + base.mark_text(align='left', dx=2)

#     # Show graph
#     layout_position.altair_chart(base)

# def user_historical_data_chart_line(df, layout_position=st):

#     # Set max intake difference percentage to 100
#     df.loc[df['actual_over_recommended_intake_percent'] > 100, 'actual_over_recommended_intake_percent'] = 100

#     # Set graph title
#     title = alt.TitleParams("Historical Nutrient Intake Tracker", anchor="middle")

#     # Set up the bar graph
#     base = alt.Chart(df, title=title).mark_bar().encode(
#         x=alt.X('actual_over_recommended_intake_percent:Q', title='percentage', scale=alt.Scale(domain=[0, 100], clamp=True)),
#         y=alt.Y('nutrient:O', title='').sort('x'),
#         color = alt.Color('actual_over_recommended_intake_percent:Q', legend= None, scale=alt.Scale(scheme='goldgreen', domain=[0, 100]))
#     ).properties(width=800)

#     base.mark_bar() + base.mark_text(align='left', dx=2)

#     # Show graph
#     layout_position.altair_chart(base)