import plotly.graph_objs as go

preferred_fonts = [
    "Verdana",
    "Oracle Sans",
    "sans-serif",
]

report_creator_colors = [
    "#01befe",
    "#ffdd00",
    "#FFA500",
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
            "xaxis": {"automargin": True, "title": {"standoff": 30}},
            "yaxis": {"automargin": True, "title": {"standoff": 30}},
            "title": {"x": 0.05},
        },
        data={"pie": [{"automargin": True}]},
    )
