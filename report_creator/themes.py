import plotly.graph_objs as go

preferred_fonts = [
    "Verdana",
    "Oracle Sans",
    "sans-serif",
]

report_creator_colors = [
    "#01befe",
    "#ffdd00",
    "#ff7d00",
    "#ff006d",
    "#adff02",
    "#8f00ff",
]


def get_rc_theme():
    return go.layout.Template(
        layout={
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
            "colorway": report_creator_colors,
            "autotypenumbers": "strict",
            "hovermode": "closest",
            "font": {
                "family": preferred_fonts[0],
                "size": 12,
                "color": "black",
            },
            "xaxis": {"automargin": True},
            "yaxis": {"automargin": True},
            "title": {"x": 0.05},
        },
        data={"pie": [{"automargin": True}]},
    )
