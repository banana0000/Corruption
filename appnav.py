import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# --- Adatok és alapbeállítások ---
df = pd.read_csv("CPI-historical.csv")
all_years = sorted(df["Year"].unique())
all_regions = sorted(df["Region"].dropna().unique())
all_countries = sorted(df["Country / Territory"].dropna().unique())
latest_year = max(all_years)

region_names = {
    "WE/EU": "Western Europe / European Union", "AP": "Asia Pacific",
    "AME": "Americas", "SSA": "Sub-Saharan Africa",
    "MENA": "Middle East & North Africa", "ECA": "Eastern Europe & Central Asia"
}
color_scales = {
    "Plasma": px.colors.sequential.Plasma, "Viridis": px.colors.sequential.Viridis,
    "Cividis": px.colors.sequential.Cividis, "Turbo": px.colors.sequential.Turbo,
    "Magma": px.colors.sequential.Magma
}
KPI_FIELDS = ["Country / Territory", "CPI score"]

# --- Segédfüggvények ---
def kpi_box(label, value, color="#fff"):
    return html.Div([
        html.Div(label, style={"fontSize": "1.05rem", "color": "#aaa", "marginBottom": "0.2rem"}),
        html.Div(str(value), style={"fontSize": "1.35rem", "color": color, "fontWeight": "bold"})
    ], style={
        "backgroundColor": "#222", "borderRadius": "12px", "padding": "1.1rem", "margin": "0.3rem",
        "boxSizing": "border-box", "flex": "1 1 200px", "minWidth": "200px",
        "boxShadow": "0 2px 8px #0002", "textAlign": "center",
    })

def kpi_panel_row(country, year, df, region=None):
    row = df[(df["Country / Territory"] == country) & (df["Year"] == year)]
    kpis = []
    region_label = region_names.get(region, region) if region else "-"
    kpis.append(kpi_box("Region", region_label, color="#0af"))
    if row.empty:
        for field in KPI_FIELDS: kpis.append(kpi_box(field, "-"))
        kpis.append(kpi_box("World rank", "-")); kpis.append(kpi_box("Region rank", "-"))
    else:
        row = row.iloc[0]; region = row["Region"]
        world_df = df[df["Year"] == year].sort_values("CPI score", ascending=False)
        world_rank = world_df.reset_index(drop=True).reset_index().set_index("Country / Territory").loc[country, "index"] + 1
        world_total = world_df.shape[0]
        region_df = world_df[world_df["Region"] == region]
        region_rank = region_df.reset_index(drop=True).reset_index().set_index("Country / Territory").loc[country, "index"] + 1
        region_total = region_df.shape[0]
        for field in KPI_FIELDS:
            val = row[field] if field in row else "-"
            if field == "CPI score": kpis.append(kpi_box(field, val, color="#0ff"))
            else: kpis.append(kpi_box(field, val))
        kpis.append(kpi_box("World rank", f"{world_rank} / {world_total}"))
        kpis.append(kpi_box("Region rank", f"{region_rank} / {region_total}"))
    return html.Div(kpis, style={"display": "flex", "flexWrap": "wrap", "alignItems": "stretch", "margin": "0.5rem 0 1.2rem 0", "width": "100%"})

def color_scale_legend(scale_name):
    colors = color_scales[scale_name]
    n = len(colors)
    return html.Div([
        html.Div("Color scale:", style={"color": "#fff", "fontSize": "0.9rem", "marginBottom": "0.2rem"}),
        html.Div([html.Div(style={"display": "inline-block", "width": f"{100/n}%", "height": "18px", "backgroundColor": color}) for color in colors], style={"width": "100%", "display": "flex", "borderRadius": "4px", "overflow": "hidden", "boxShadow": "0 0 2px #333"}),
        html.Div([html.Span("Low", style={"color": "#fff", "fontSize": "0.8rem", "float": "left"}), html.Span("High", style={"color": "#fff", "fontSize": "0.8rem", "float": "right"})], style={"width": "100%", "marginTop": "2px", "clear": "both"})
    ], style={"width": "50%", "margin": "0 auto 1rem auto"})

def get_line_color(selected_scale):
    scale = color_scales[selected_scale]
    idx = int(len(scale) * 0.7) if len(scale) > 4 else len(scale) // 2
    return [scale[idx]]

def create_ranking_barchart(dff, region, selected_scale, year):
    title_text = f"CPI {year} Ranking: {region_names.get(region, region) if region else 'World'}"
    chart_df = dff.sort_values("CPI score", ascending=True)
    fig = px.bar(chart_df, x="CPI score", y="Country / Territory", orientation='h', title=title_text, color="CPI score", color_continuous_scale=color_scales[selected_scale], range_color=(df["CPI score"].min(), df["CPI score"].max()), text="CPI score")
    fig.update_layout(template="plotly_dark", plot_bgcolor="#111", paper_bgcolor="#111", font_color="#fff", margin=dict(l=10, r=10, t=40, b=10), yaxis_title=None, xaxis_title="CPI Score", coloraxis_showscale=False, height=max(600, len(chart_df) * 25))
    fig.update_traces(textposition='outside')
    return dcc.Graph(figure=fig, config={"displayModeBar": False})

# --- Layout függvény a fő dashboardnak ---
def create_dashboard_layout():
    return dbc.Container([
        dbc.Row([dbc.Col(html.H1("CPI Time Series Dashboard", className="text-center text-light mb-4"), width=12)]),
        dbc.Row([dbc.Col(html.Div(id="kpi-panel", style={"width": "100%"}), width=12)], className="mb-2"),
        dbc.Row([
            dbc.Col([dbc.Label("Region", className="text-light"), dbc.Select(id="region-select", options=[{"label": "All regions", "value": "all"}] + [{"label": region_names.get(r, r), "value": r} for r in all_regions], value="all", className="bg-dark text-light")], lg=4, md=6, xs=12, className="mb-2"),
            dbc.Col([dbc.Label("Country", className="text-light"), dbc.Select(id="country-select", options=[{"label": "All countries", "value": "all"}] + [{"label": c, "value": c} for c in all_countries], value="all", className="bg-dark text-light")], lg=4, md=6, xs=12, className="mb-2"),
            dbc.Col([dbc.Label("Map color scale", className="text-light"), dbc.RadioItems(id="color-scale-select", options=[{"label": k, "value": k} for k in color_scales.keys()], value="Plasma", inline=True, className="text-light")], lg=4, md=12, xs=12, className="mb-2"),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([html.Div(id="color-legend-div"), dcc.Graph(id="map-chart", config={"displayModeBar": False}, style={"height": "550px"})], lg=7, xs=12),
            dbc.Col([dcc.Graph(id="line-chart", config={"displayModeBar": False}, style={"height": "550px"})], lg=5, xs=12, className="mt-4 mt-lg-0"),
        ], align="start", justify="between"),
    ], fluid=True, style={"padding": "20px"})

# --- Layout függvény a ranking oldalnak ---
def create_ranking_layout():
    return dbc.Container([
        dbc.Row([dbc.Col(html.H1("Country Rankings", className="text-center text-light mb-4"), width=12)]),
        dbc.Row([
            dbc.Col([dbc.Label("Region", className="text-light"), dbc.Select(id="ranking-region-select", options=[{"label": "World", "value": "all"}] + [{"label": region_names.get(r, r), "value": r} for r in all_regions], value="all", className="bg-dark text-light")], lg=4, md=12, className="mb-3"),
            dbc.Col([dbc.Label("Color scale", className="text-light"), dbc.RadioItems(id="ranking-color-scale-select", options=[{"label": k, "value": k} for k in color_scales.keys()], value="Plasma", inline=True, className="text-light")], lg=8, md=12, className="mb-3"),
        ], justify="center"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Show", className="text-light"),
                dbc.RadioItems(id="ranking-mode-select", options=[
                    {"label": "All", "value": "all"}, {"label": "Top", "value": "top"}, {"label": "Bottom", "value": "bottom"},
                ], value="all", inline=True, className="text-light")
            ], lg=4, md=6, className="mb-3"),
            dbc.Col([
                dbc.Label("Number of countries", className="text-light"),
                dbc.Input(id="ranking-n-input", type="number", min=5, max=50, step=5, value=10, disabled=True)
            ], lg=3, md=6, className="mb-3"),
        ], justify="center", className="mb-4"),
        dbc.Row([dbc.Col(html.Div(id="ranking-chart-div"), width=12)])
    ], fluid=True, style={"padding": "20px"})

# --- App inicializálása a többoldalas működéshez szükséges beállítással ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
                suppress_callback_exceptions=True)
server = app.server

# --- Fő elrendezés navigációval és tartalom konténerrel ---
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Dashboard", href="/")),
            dbc.NavItem(dbc.NavLink("Ranking", href="/ranking")),
        ],
        brand="CPI Explorer",
        brand_href="/",
        color="primary",
        dark=True,
        className="mb-3"
    ),
    html.Div(id="page-content", style={"backgroundColor": "#000"})
])

# --- Router callback, ami betölti a megfelelő oldalt ---
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/ranking":
        return create_ranking_layout()
    else:
        return create_dashboard_layout()

# --- Callback a Dashboard oldalhoz ---
@app.callback(
    Output("map-chart", "figure"), Output("line-chart", "figure"),
    Output("color-legend-div", "children"), Output("kpi-panel", "children"),
    Output("country-select", "options"), Output("country-select", "value"),
    Input("country-select", "value"), Input("region-select", "value"),
    Input("color-scale-select", "value"), Input("map-chart", "clickData"),
)
def update_dashboard(selected_country_dropdown, selected_region, selected_scale, map_click):
    ctx = dash.callback_context; triggered_id = ctx.triggered_id
    if selected_region == "all":
        country_options = [{"label": "All countries", "value": "all"}] + [{"label": c, "value": c} for c in all_countries]
        country_value = selected_country_dropdown if selected_country_dropdown in all_countries or selected_country_dropdown == "all" else "all"
    else:
        region_countries = sorted(df[df["Region"] == selected_region]["Country / Territory"].dropna().unique())
        country_options = [{"label": "All countries", "value": "all"}] + [{"label": c, "value": c} for c in region_countries]
        country_value = selected_country_dropdown if selected_country_dropdown in region_countries else "all"
    selected_year = latest_year; dff_full_year = df[df["Year"] == selected_year]
    dff_map = dff_full_year; map_title = f"CPI {selected_year} - World"; region_context = None
    if country_value != "all":
        dff_map = dff_full_year[dff_full_year["Country / Territory"] == country_value]
        map_title = f"CPI {selected_year}: {country_value}"; region_context = dff_map.iloc[0]["Region"]
    elif selected_region != "all":
        dff_map = dff_full_year[dff_full_year["Region"] == selected_region]
        map_title = f"CPI {selected_year} - {region_names.get(selected_region)}"; region_context = selected_region
    map_fig = px.choropleth(dff_map, locations="ISO3", color="CPI score", hover_name="Country / Territory", color_continuous_scale=color_scales[selected_scale], range_color=(df["CPI score"].min(), df["CPI score"].max()), title=map_title)
    map_fig.update_geos(showcoastlines=False, showland=True, fitbounds="locations", showcountries=False, showframe=False)
    map_fig.update_layout(template="plotly_dark", plot_bgcolor="#000", paper_bgcolor="#000", font_color="#fff", margin=dict(l=10, r=10, t=40, b=10), coloraxis_showscale=False)
    country_for_line_chart = country_value
    if triggered_id == "map-chart" and map_click: country_for_line_chart = map_click["points"][0]["hovertext"]
    line_color = get_line_color(selected_scale); kpi_panel = html.Div()
    if country_for_line_chart != "all":
        dff_line = df[df["Country / Territory"] == country_for_line_chart]
        title = f"CPI Score Over Time: {country_for_line_chart}"
        line_fig = px.line(dff_line, x="Year", y="CPI score", markers=True, title=title, line_shape="spline", color_discrete_sequence=line_color)
        kpi_region = df.loc[df["Country / Territory"] == country_for_line_chart, "Region"].iloc[0]
        kpi_panel = kpi_panel_row(country_for_line_chart, selected_year, df, region=kpi_region)
    else:
        if region_context:
            dff_line = df[df["Region"] == region_context].groupby("Year").agg({"CPI score": "mean"}).reset_index()
            title = f"CPI Score: {region_names.get(region_context, region_context)} (average)"
        else:
            dff_line = df.groupby("Year").agg({"CPI score": "mean"}).reset_index()
            title = "CPI Score Over Time: World Average"
        line_fig = px.line(dff_line, x="Year", y="CPI score", markers=True, title=title, line_shape="spline", color_discrete_sequence=line_color)
    line_fig.update_traces(line=dict(width=4))
    line_fig.update_layout(template="plotly_dark", plot_bgcolor="#111", paper_bgcolor="#111", font_color="#fff", margin=dict(l=10, r=10, t=40, b=10))
    legend = color_scale_legend(selected_scale)
    return map_fig, line_fig, legend, kpi_panel, country_options, country_value

# --- Callback a számbeviteli mező letiltásához a Ranking oldalon ---
@app.callback(
    Output("ranking-n-input", "disabled"),
    Input("ranking-mode-select", "value")
)
def toggle_n_input_disabled(selected_mode):
    return selected_mode == "all"

# --- Callback a Ranking oldalhoz ---
@app.callback(
    Output("ranking-chart-div", "children"),
    Input("ranking-region-select", "value"),
    Input("ranking-color-scale-select", "value"),
    Input("ranking-mode-select", "value"),
    Input("ranking-n-input", "value")
)
def update_ranking_page(selected_region, selected_scale, selected_mode, n_countries):
    dff = df[df["Year"] == latest_year]
    ranking_region_context = None
    if selected_region != "all":
        dff = dff[dff["Region"] == selected_region]
        ranking_region_context = selected_region
    if selected_mode != "all":
        if n_countries is None or n_countries < 1: n_countries = 10
        if selected_mode == "top": dff = dff.sort_values("CPI score", ascending=False).head(n_countries)
        elif selected_mode == "bottom": dff = dff.sort_values("CPI score", ascending=True).head(n_countries)
    return create_ranking_barchart(dff, ranking_region_context, selected_scale, latest_year)

if __name__ == "__main__":
    app.run(debug=True)