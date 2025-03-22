import dash
from dash import html, dcc, dash_table, callback, Input, Output, State
import pandas as pd
import datetime

app = dash.Dash(__name__)
dash.register_page(__name__, path="/summary")

layout = html.Div([
    html.H1("Summary of Hours Worked", style={'textAlign': 'center', 'fontSize': 40}),

    html.Label("Filter by Semester:"),
    dcc.Dropdown(
        id="semester-filter",
        options=[
            {"label": "Spring 2024", "value": "Spring 2024"},
            {"label": "Summer 2024", "value": "Summer 2024"},
            {"label": "Fall 2024", "value": "Fall 2024"},
            {"label": "Spring 2025", "value": "Spring 2025"}
        ],
        value="Spring 2024",
        clearable=False
    ),

    html.Div([
        html.H3("Total Hours Worked:"),
        html.Div(id="total-hours"),

        html.H3("Total Money Earned:"),
        html.Div(id="total-money"),

        html.H3("Shift Breakdown:"),
        html.Div(id="shift-breakdown", style={'whiteSpace': 'pre-line'})
    ], style={'textAlign': 'center', 'marginTop': '20px'}),

    html.Div([
        dcc.Link('Go Back', href='/', style={'fontSize': '20px'})
    ], style={'textAlign': 'center', 'marginTop': '20px'})
])

@callback(
    [Output("total-hours", "children"),
     Output("total-money", "children"),
     Output("shift-breakdown", "children"),
     Output("summary-title", "children")],  # Update title dynamically
    [Input("semester-filter", "value"),
     Input("data-store", "data")]
)
def update_summary(semester, stored_data):
    if not stored_data:
        return "0 hours", "$0.00", "No Shifts Logged", "Summary of Hours Worked"

    df = pd.DataFrame(stored_data)

    # ✅ Define get_semester() inside update_summary()
    def get_semester(date):
        if not date:
            return "Unknown"  

        try:
            dt = datetime.datetime.strptime(date, "%Y-%m-%d")
            year = dt.year
            month = dt.month

            if month in [1, 2, 3, 4]:   # January - April
                return f"Spring {year}"
            elif month in [5, 6, 7, 8]:  # May - August
                return f"Summer {year}"
            elif month in [9, 10, 11, 12]:  # September - December
                return f"Fall {year}"
        except ValueError:
            return "Unknown"  

        return "Unknown"

    # Apply semester mapping to each row
    df["Semester"] = df["Date"].apply(lambda x: get_semester(x) if x else "Unknown")

    # Filter based on selected semester
    if semester != "all":
        df = df[df["Semester"] == semester]

    # Calculate total hours
    total_hours = df["Hours"].sum()

    # Calculate total money earned (Rounded to 2 decimals)
    total_money = round((total_hours * 17) * 0.84, 2)

    # Format shift breakdown
    shift_counts = df["Work"].value_counts().to_dict()
    # shift_summary = "\n".join([f"{k.capitalize()}: {v}" for k, v in shift_counts.items()]) or "No Shifts Logged"
    shift_summary = [html.Div(f"{k.capitalize()}: {v}") for k, v in shift_counts.items()] or "No Shifts Logged"  # ✅ Each type on a new line

    # Update title dynamically
    title = "Summary of Hours Worked Across All Semesters" if semester == "all" else f"Summary of Hours Worked During the {semester} Semester"

    return f"{total_hours} hours", f"${total_money:.2f}", shift_summary, title
