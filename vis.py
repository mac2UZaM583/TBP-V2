import plotly.graph_objects as go

def g_visualize(
    x,
    y,
    markers=None,

):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Close Price'))

    for el in markers:
        fig.add_trace(go.Scatter(
            x=el["data"].index, 
            y=el["data"]['close'], 
            mode='markers', 
            marker=dict(size=10, color=el["color"]), 
            name=el["name"]
        ))

    # Настройка макета графика
    fig.update_layout(
        title='Price with Predicted Buy Signals',
        xaxis_title='Date',
        yaxis_title='Price',
        legend_title='Legend',
    )
    fig.show()