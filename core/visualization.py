import numpy as np
import altair as alt
import streamlit as st
import pandas as pd

def users_recommended_intake_chart(df, layout_position=st):
    # Set max intake difference percentage to 100
    #df.loc[df['Actual intake / Recommended intake (%)'] > 100, 'Actual intake / Recommended intake (%)'] = 100
    df['Intake Display'] = df['Actual intake / Recommended intake (%)'].clip(upper=100)

    # Set graph title
    title = alt.TitleParams("Nutrient Intake Tracker", anchor="middle")

    # Set up the bar graph
    base = alt.Chart(df, title=title).mark_bar().encode(
        x=alt.X('Intake Display:Q', title='Intake Percentage', scale=alt.Scale(domain=[0, 100], clamp=True)),
        y=alt.Y('Nutrient:O', title='Nutrients').sort('x'),
          color=alt.condition(
            alt.datum['Actual intake / Recommended intake (%)'] > 100,  # Condition for values greater than 100
            alt.value('red'),  # Apply red color
            alt.Color('Actual intake / Recommended intake (%):Q', legend= None, scale=alt.Scale(scheme='goldgreen', domain=[0, 100]))  # Else use steelblue color
        )
        #color = alt.Color('Actual intake / Recommended intake (%):Q', legend= None, scale=alt.Scale(scheme='goldgreen', domain=[0, 100]))
    ).properties(width=800)

    base.mark_bar() + base.mark_text(align='left', dx=2)

    # Show graph
    layout_position.altair_chart(base)

def user_historical_hexbin_chart(df, layout_position):
    # Convert 'record_date' to datetime and extract 'dd-mm' format for plotting
    df['day_month'] = pd.to_datetime(df['record_date']).dt.strftime('%d-%m')
    df['day'] = pd.to_datetime(df['record_date']).dt.day
    df['month'] = pd.to_datetime(df['record_date']).dt.month

    # Assign a numeric index to each nutrient for the y-axis positioning
    df['nutrient_index'] = df['nutrient'].astype('category').cat.codes

    # Define hexagon size and shape
    hex_size = 112  # Adjust the size of the hexagons here
    hex_shape = "M0,-2.3094010768L2,-1.1547005384 2,1.1547005384 0,2.3094010768 -2,1.1547005384 -2,-1.1547005384Z"

    # Calculate x and y positions for hexbins with an offset for a staggered layout
    df['x_pos'] = df['day'] + (df['month'] - 1) * 31
    df['x_offset'] = df['x_pos'] + (df['nutrient_index'] % 2) * 0.5

    # Create the hexbin plot
    hexbin = alt.Chart(df).mark_point(
        size=hex_size,
        shape=hex_shape,
        filled=True,
    ).encode(
        x=alt.X('record_date:T',
                title='Date',
                axis=alt.Axis(labelAngle=270, format='%Y-%m-%d'),
                scale=alt.Scale(zero=False)),
        y=alt.Y('nutrient:N',
                title='Nutrient',
                scale=alt.Scale(zero=False)),
        color=alt.Color('actual_over_recommended_intake_percent:Q',
                        title='Percentage Achieved',
                        scale=alt.Scale(domain=[0, 100],
                                        scheme='goldgreen')),
        tooltip=['nutrient', 'day_month', 'actual_over_recommended_intake_percent']
    ).properties(
        width=1000,
        height=700,
        # Centering the title
        title=alt.TitleParams(
            text="Historical Nutrient Intake Tracker",
            align="center"
        )
    ).configure_view(
        strokeWidth=0
    )

    # Show the chart in the specified layout position
    layout_position.altair_chart(hexbin)







#def user_historical_data_chart(df, layout_position=st):
    # Clip values at 100% for visualization
#    df['actual_over_recommended_intake_percent'] = df['actual_over_recommended_intake_percent'].clip(upper=100)

    # Set graph title
#    title = alt.TitleParams("Historical Nutrient Intake Tracker", anchor="middle")

    # Set up the heatmap
 #   heatmap = alt.Chart(df, title=title).mark_rect().encode(
  #      x=alt.X('record_date:O', title='Date', scale=alt.Scale(domain=(df['record_date'].min(), df['record_date'].max()))),
   #     y=alt.Y('nutrient:O', title='Nutrient', sort='-x'),
    #    color=alt.Color('actual_over_recommended_intake_percent:Q', 
     #                   title='Percentage Achieved', 
      #                  scale=alt.Scale(domain=[0, 100], scheme='goldgreen'))
  #  ).properties(width=800, height=400)

    # Show graph in the specified layout position
   # layout_position.altair_chart(heatmap)





#---------------------------------------------------------------------------
## Place holder for dish recommender:

#def users_recommended_with_dish_chart(df, layout_position=st):
    # Assuming 'dish_intake_increase' is the column with the amount added by the new dish
    # Create a new column for the stacked value
#    df['Total Intake with Dish'] = df['Actual intake'] + df['dish_intake_increase']
#    df['Total Intake with Dish (%)'] = (df['Total Intake with Dish'] / df['Recommended intake']) * 100

    # Clip the values at 100% for visualization
#    df['Total Intake with Dish (%)'] = df['Total Intake with Dish (%)'].clip(upper=100)

    # Set graph title
#    title = alt.TitleParams("Nutrient Intake Tracker with Dish Recommendation", anchor="middle")

    # Base chart for actual intake
#    base_actual = alt.Chart(df).mark_bar().encode(
#        x=alt.X('Actual intake / Recommended intake (%):Q', title='Percentage'),
#        y=alt.Y('Nutrient:O', sort='-x'),
#        color=alt.value('steelblue')  # Use a fixed color for actual intake
#   )

    # Added intake from dish
#    base_dish = alt.Chart(df).mark_bar().encode(
#        x=alt.X('Total Intake with Dish (%):Q'),
#        y='Nutrient:O',
#        color=alt.value('goldenrod')  # Use a fixed color for intake increase from dish
#    )

    # Combined chart
#    chart = alt.layer(base_actual, base_dish).resolve_scale(x='independent').properties(
#        title=title,
#        width=800
#   )

    # Display the stacked bar chart
#    layout_position.altair_chart(chart)
#---------------------------------------------------------------------------

## Feel free to delete the codes below



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

#df = pd.read_csv("anika_sample.csv")
#user_historical_data_chart(df)