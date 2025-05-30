import re
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import base64

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Live CAN Viewer"

# Layout of the web page
app.layout = html.Div([
    html.H2("CAN Live Viewer)"),
    dcc.Upload(
        id='upload-data',
        children=html.Div(['📄 Drag & Drop or ', html.A('Select CAN Log File')]),
        style={
            'width': '60%', 'margin': '20px auto', 'padding': '30px',
            'border': '2px dashed #aaa', 'borderRadius': '10px', 'textAlign': 'center'
        },
        multiple=False
    ),
    dcc.Graph(id='live-graph'),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0, disabled=True),
    html.Div(id='hidden-data', style={'display': 'none'})
])

# Global data holder
parsed_data = []

# Function to parse uploaded CAN dump
def parse_can_txt(contents):
    global parsed_data
    parsed_data = []

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    text = decoded.decode('utf-8')

    pattern = re.compile(r"\((.*?)\).*?(18ABE004).*?\[\d+\]\s+([0-9A-Fa-f ]+)")
    
    for line in text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        timestamp_str, _, data_str = match.groups()
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            data_bytes = [int(b, 16) for b in data_str.strip().split()]
            if len(data_bytes) >= 8:
                engine_rpm = data_bytes[0] * 8
                parsed_data.append((timestamp, engine_rpm))
        except Exception:
            continue

# Handle upload
@app.callback(
    Output('interval-component', 'disabled'),
    Output('hidden-data', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
)
def handle_file_upload(contents, filename):
    if contents:
        parse_can_txt(contents)
        return False, "ready"
    return True, ""

# Update graph every second
@app.callback(
    Output('live-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
)
def update_graph(n):
    if not parsed_data:
        return go.Figure()

    slice_size = min(len(parsed_data), n * 10)
    time_data = [p[0] for p in parsed_data[:slice_size]]
    rpm_data = [p[1] for p in parsed_data[:slice_size]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_data, y=rpm_data, mode='lines+markers', name="Engine RPM"))
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Engine RPM",
        title="Live Engine RPM from 18ABE004",
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig

# Run app
if __name__ == '__main__':
    app.run(debug=True)
