import plotly.graph_objects as go

def g_visualize(
    x,
    y,
    markers_target,
    markers_settings=(),
    add_metrics={},
):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Close Price'))

    for el in markers_settings:
        if_key = markers_target == el["class_"]
        fig.add_trace(go.Scatter(
            x=markers_target[if_key].index, 
            y=y[if_key], 
            mode='markers', 
            marker=dict(size=10, color=el["color"]), 
            name=el["name"]
        ))

    fig.update_layout(
        title='Price with Predicted Buy Signals',
        xaxis_title='Date',
        yaxis_title='Price',
        legend_title='Legend',
    )
    fig.show()