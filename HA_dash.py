import dash
from dash import Dash, html, dcc, dash_table, page_container, callback
from dash.dependencies import Input, Output, State
import datetime
import json
import sys

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H1('Husky Ambassador Hours', style={'textAlign': 'center', 'fontSize': 60}),

    dcc.Store(id='data-store', storage_type='local'),
    dcc.Store(id='work-log-refresh', storage_type='memory'),
    dcc.Store(id='invalid-rows-flag', storage_type='memory'),

    dcc.Tabs(
        id="tabs",
        value="work-log",
        children=[
            dcc.Tab(label="Work Log", value="work-log"),
            dcc.Tab(label="Summary", value="summary"),
        ],
        style={'fontSize': '20px', 'textAlign': 'center'}
    ),

    html.Div(id="tab-content", style={'padding': '20px'})
], style={'backgroundColor': '#E3F2FD', 'padding': '20px'})

def clean_time_input(time_str):
    if not time_str:
        return ""

    # If user entered only hour, fill with ":00"
    if time_str.isdigit():
        return f"{time_str}:00"

    # If they entered something like "1:0" or "14:9"
    if ':' in time_str:
        parts = time_str.split(':')
        hour = parts[0].zfill(2)  # make sure hour has 2 digits if you want it uniform
        minute = parts[1].zfill(2)
        return f"{hour}:{minute}"

    # If input is invalid or something else, just return it as is
    return time_str

@app.callback(
    [Output('data-store', 'data'),
     Output('work-log-refresh', 'data'),
     Output('invalid-rows-flag', 'data')],
    [Input('work-log-submit', 'n_clicks'),
     Input('work-log', 'data_timestamp')],   # Only triggers on manual edits/deletions
    [State('work-date', 'date'),
     State('work-time', 'value'),
     State('work-done', 'value'),
     State('hours-worked', 'value'),
     State('data-store', 'data'),
     State('work-log', 'data')],       
    prevent_initial_call=True
)
def update_data_store(work_clicks, table_edit_timestamp, work_date, work_time, work_done, hours_worked, stored_data, current_table_data):
    stored_data = stored_data or []
    triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    invalid_detected = False

    if triggered_id == 'work-log-submit' and work_clicks > 0:
        # Clean up time formatting
        work_time = clean_time_input(work_time)
        new_row = {'Date': work_date, 'Time': work_time, 'Work': work_done, 'Hours': hours_worked}
        stored_data.append(new_row)
        print(f"✅ Added Row: {new_row}", file=sys.stderr, flush=True)

    elif triggered_id == 'work-log' and table_edit_timestamp is not None:
        # Sync row deletions safely
        print(f"🗑️ Detected row deletion or edit. Updating store.", file=sys.stderr, flush=True)
        stored_data = current_table_data[:]

    # Auto-clean invalid rows
    cleaned_data = []
    for row in stored_data:
        try:
            datetime.datetime.strptime(f"{row['Date']} {row['Time']}", "%Y-%m-%d %H:%M")
            cleaned_data.append(row)
        except:
            invalid_detected = True
            print(f"🧹 Auto-removed invalid row: {row}", file=sys.stderr, flush=True)

    # Clear invalid flag if last add was successful
    invalid_flag = invalid_detected
    if triggered_id == 'work-log-submit' and not invalid_detected:
        invalid_flag = False

    return cleaned_data, str(datetime.datetime.now()), invalid_flag

def display_logs(stored_data, refresh_signal, invalid_flag, semester_filter):
    print(f"🔄 display_logs triggered! Refresh Signal: {refresh_signal}", file=sys.stderr, flush=True)

    if not stored_data or not any('Work' in row for row in stored_data):
        return html.Div("No work log entries yet.", style={'textAlign': 'center', 'fontSize': '21px', 'marginBottom': '30px'})

    def get_semester(date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            month = dt.month
            year = dt.year
            if month in [1, 2, 3, 4]:
                return f"Spring {year}"
            elif month in [5, 6, 7, 8]:
                return f"Summer {year}"
            elif month in [9, 10, 11, 12]:
                return f"Fall {year}"
        except:
            return "Unknown"

    invalid_rows = []
    valid_rows = []

    # Filter by semester
    if semester_filter and semester_filter != "all":
        filtered_data = [row for row in stored_data if get_semester(row.get("Date", "")) == semester_filter]
    else:
        filtered_data = stored_data

    try:
        for row in filtered_data:
            if row.get("Date") and row.get("Time"):
                try:
                    row["DateTime"] = datetime.datetime.strptime(f"{row['Date']} {row['Time']}", "%Y-%m-%d %H:%M")
                    valid_rows.append(row)
                except ValueError:
                    invalid_rows.append(row)
                    print(f"⚠️ Detected invalid row (auto-clean will remove): {row}", file=sys.stderr, flush=True)
            else:
                row["DateTime"] = datetime.datetime.min
                valid_rows.append(row)

        work_data = sorted(valid_rows, key=lambda x: x["DateTime"], reverse=True)

        # Format time and clean up
        for row in work_data:
            try:
                dt_obj = datetime.datetime.strptime(f"{row['Date']} {row['Time']}", "%Y-%m-%d %H:%M")
                row['Time'] = dt_obj.strftime("%-I:%M") if sys.platform != 'win32' else dt_obj.strftime("%#I:%M")
            except:
                pass
            row.pop("DateTime", None)

        auto_clean_notice = None
        if invalid_rows or invalid_flag:
            auto_clean_notice = html.Div([
                html.P("⚠️ Some invalid entries were detected and automatically removed from your work log."),
                html.P("Please make sure to enter time in HH:MM format next time!")
            ], style={'color': 'orange', 'textAlign': 'center', 'fontSize': '16px', 'marginBottom': '20px'})

        if not work_data:
            return html.Div("No work log entries found for this semester.", style={'textAlign': 'center', 'fontSize': '18px'})

        return html.Div([
            auto_clean_notice if auto_clean_notice else None,
            dash_table.DataTable(
                id='work-log',
                columns=[{'name': col, 'id': col, 'editable': False} for col in work_data[0].keys()],
                data=work_data,
                row_deletable=True,
                style_table={'width': '60%', 'margin': 'auto'},
                style_cell={'textAlign': 'center', 'fontSize': '20px'},
                style_header={'fontWeight': 'bold'}
            )
        ])

    except Exception as e:
        print(f"❌ Error in display_logs: {str(e)}", file=sys.stderr, flush=True)
        return html.Div(f"Error processing data: {str(e)}", style={'color': 'red', 'textAlign': 'center'})

@callback(
    Output("tab-content", "children"),
    Input("tabs", "value")
)
def render_content(tab):
    if tab == "work-log":
        return html.Div([
            dcc.Store(id='data-store', storage_type='local'),

            html.Div(style={'height': '10px'}),

            html.H1('Work Log', style={'textAlign': 'center', 'fontSize': '30px', 'fontWeight': 'bold', 'marginBottom': '50px'}),

            html.Div([
                html.Div([
                    html.Label('Date Worked:', style={'fontSize': '20px', 'fontWeight': 'bold'}),
                    dcc.DatePickerSingle(id='work-date', display_format='MM-DD-Y', style={'width': '100%'})
                ], style={'marginBottom': '15px'}),  

                html.Div([
                    html.Label('Time of Day:', style={'fontSize': '20px', 'fontWeight': 'bold'}),
                    dcc.Input(id='work-time', type='text', placeholder='HH:MM', value="")
                ], style={'marginBottom': '15px'}),  

                html.Div([
                    html.Label('What Work was Done:', style={'fontSize': '20px', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='work-done',
                        options=[
                            {'label': 'Tour', 'value': 'tour'},
                            {'label': 'Registration', 'value': 'registration'},
                            {'label': 'Org Wides', 'value': 'org wide'},
                            {'label': 'Other', 'value': 'other'},
                            {'label': 'Training', 'value': 'training'}
                        ],
                        value='tour',
                        style={'width': '100%'}  
                    )
                ], style={'marginBottom': '15px'}),  

                html.Div([
                    html.Label('Number of Hours Worked:', style={'fontSize': '20px', 'fontWeight': 'bold'}),
                    dcc.Input(id='hours-worked', type='number', style={'width': '100%'})  
                ], style={'marginBottom': '30px'}),  

                html.Button(id='work-log-submit', n_clicks=0, children='Submit',
                            style={'fontSize': '20px', 'display': 'block', 'margin': 'auto', 'padding': '10px 20px'}),  
            ], style={'textAlign': 'center', 'maxWidth': '500px', 'margin': 'auto'}),

                html.Div([
    html.Label("Filter by Semester:", style={
        'fontSize': '20px',
        'fontWeight': 'bold',
        'textAlign': 'center',
        'display': 'block',
        'marginBottom': '10px'
    }),
    dcc.Dropdown(
        id="worklog-semester-filter",
        options=[
            {"label": "All Semesters", "value": "all"},
            {"label": "Spring 2024", "value": "Spring 2024"},
            {"label": "Summer 2024", "value": "Summer 2024"},
            {"label": "Fall 2024", "value": "Fall 2024"},
            {"label": "Spring 2025", "value": "Spring 2025"}
        ],
        value="all",
        clearable=False,
        style={'width': '50%', 'margin': 'auto'}
    )
], style={'textAlign': 'center', 'marginTop': '40px'}),


            html.Div(style={'height': '50px'}),

            # ✅ Work log container is only inside this tab
            html.Div(id='work-log-container'), 

            html.Div([
                dash_table.DataTable(
                    id='work-log',
                    columns=[{"name": "Date", "id": "Date"},
                            {"name": "Time", "id": "Time"},
                            {"name": "Work", "id": "Work"},
                            {"name": "Hours", "id": "Hours"}],
                    data=[],  # empty placeholder data
                    row_deletable=True,
                    style_table={'width': '60%', 'margin': 'auto'},
                    style_cell={'textAlign': 'center', 'fontSize': '20px'},
                    style_header={'fontWeight': 'bold'},
                    style_data={'backgroundColor': '#F0F0F0'}
                )
            ])

        ])

    elif tab == "summary":
        return html.Div([
            dcc.Store(id='data-store', storage_type='local'),

            html.Div(style={'height': '10px'}),

            html.H1(id="summary-title", children="Summary of Hours Worked Across All Semesters", 
                    style={'textAlign': 'center', 'fontSize': '30px', 'fontWeight': 'bold'}),

            html.Label("Filter by Semester:", style={'fontSize': '20px', 'fontWeight': 'bold', 'display': 'block', 'textAlign': 'center'}),  

            html.Div(
                dcc.Dropdown(
                    id="semester-filter",
                    options=[
                        {"label": "All Semesters", "value": "all"},
                        {"label": "Spring 2024", "value": "Spring 2024"},
                        {"label": "Summer 2024", "value": "Summer 2024"},
                        {"label": "Fall 2024", "value": "Fall 2024"},
                        {"label": "Spring 2025", "value": "Spring 2025"}
                    ],
                    value="all",
                    clearable=False,
                    style={'width': '50%', 'margin': 'auto'}
                ),
                style={'textAlign': 'center'}
            ),

            html.Div([
                html.H3("Total Hours Worked:", style={'fontSize': '20px'}),
                html.Div(id="total-hours"),

                html.H3("Total Money Earned:", style={'fontSize': '20px'}),
                html.Div(id="total-money"),

                html.H3("Shift Breakdown:", style={'fontSize': '20px'}),
                html.Div(id="shift-breakdown")
            ], style={'textAlign': 'center', 'marginTop': '20px', 'fontSize': '20px'}),  
        ])
    
@app.callback(
    Output('work-log-container', 'children'),
    [
        Input('data-store', 'data'),
        Input('work-log-refresh', 'data'),
        Input('invalid-rows-flag', 'data'),
        Input('worklog-semester-filter', 'value')  # <-- listen to filter changes
    ]
)
def update_work_log_display(stored_data, refresh_signal, invalid_flag, semester_filter):
    return display_logs(stored_data, refresh_signal, invalid_flag, semester_filter)

app.rungit(debug=True)