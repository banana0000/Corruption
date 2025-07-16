from dash import Dash, dcc
import dash_ag_grid as dag
import plotly.express as px
import pandas as pd

df = pd.read_csv("https://raw.githubusercontent.com/plotly/Figure-Friday/refs/heads/main/2025/week-28/CPI2024.csv")

fig = px.choropleth(df, color="Rank", locations="ISO3", hover_name="Country / Territory",
                    title="Ranking of Corruption Perceptions Index 2024")
fig.update_layout(margin={"r":0,"t":30,"l":0,"b":10})


grid = dag.AgGrid(
    rowData=df.to_dict("records"),
    columnDefs=[{"field": i, 'filter': True, 'sortable': True} for i in df.columns],
    dashGridOptions={"pagination": True},
    # columnSize="sizeToFit"
)

app = Dash()
app.layout = [
    grid,
    dcc.Graph(figure=fig)
]


if __name__ == "__main__":
    app.run(debug=False)

