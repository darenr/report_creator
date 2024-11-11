import plotly.graph_objs as go

preferred_fonts = [
    "sans-serif",
]

report_creator_colors = [
    "#ffdd00",
    "#5fd83d",
    "#ffb617",
    "#44a124",
    "#f31a7c",
    "#d18f06",
    "#1f6f05",
    "#AFEEEE",
    "#1a1100",
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
