from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.palettes import GnBu3, OrRd3

import os
import pandas as pd
import numpy as np

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.transform import dodge
from bokeh.models import BoxZoomTool, HoverTool

from jinja2 import Template



def get_plot_1():
    fruits = ["Apples", "Pears", "Nectarines", "Plums", "Grapes", "Strawberries"]
    years = ["2015", "2016", "2017"]

    data = {
        "fruits": fruits,
        "2015": [2, 1, 4, 3, 2, 4],
        "2016": [5, 3, 3, 2, 4, 6],
        "2017": [3, 2, 4, 4, 5, 3],
    }

    source = ColumnDataSource(data=data)

    p = figure(
        x_range=fruits,
        y_range=(0, 10),
        title="Fruit Counts by Year",
        width=800,
        height=550,
    )

    p.vbar(
        x=dodge("fruits", -0.25, range=p.x_range),
        top="2015",
        source=source,
        width=0.2,
        color="#c9d9d3",
        legend_label="2015",
    )

    p.vbar(
        x=dodge("fruits", 0.0, range=p.x_range),
        top="2016",
        source=source,
        width=0.2,
        color="#718dbf",
        legend_label="2016",
    )

    p.vbar(
        x=dodge("fruits", 0.25, range=p.x_range),
        top="2017",
        source=source,
        width=0.2,
        color="#e84d60",
        legend_label="2017",
    )

    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"

    return p


def get_plot_2():
    fruits = ["Apples", "Pears", "Nectarines", "Plums", "Grapes", "Strawberries"]
    years = ["2015", "2016", "2017"]

    exports = {
        "fruits": fruits,
        "2015": [2, 1, 4, 3, 2, 4],
        "2016": [5, 3, 4, 2, 4, 6],
        "2017": [3, 2, 4, 4, 5, 3],
    }
    imports = {
        "fruits": fruits,
        "2015": [-1, 0, -1, -3, -2, -1],
        "2016": [-2, -1, -3, -1, -2, -2],
        "2017": [-1, -2, -1, 0, -2, -2],
    }

    p = figure(
        y_range=fruits,
        width=800,
        height=550,
        x_range=(-16, 16),
        title="Fruit import/export, by year",
    )

    p.hbar_stack(
        years,
        y="fruits",
        height=0.9,
        color=GnBu3,
        source=ColumnDataSource(exports),
        legend_label=[f"{year} exports" for year in years],
    )

    p.hbar_stack(
        years,
        y="fruits",
        height=0.9,
        color=OrRd3,
        source=ColumnDataSource(imports),
        legend_label=[f"{year} imports" for year in years],
    )

    p.y_range.range_padding = 0.1
    p.ygrid.grid_line_color = None
    p.legend.location = "top_left"
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None

    return p


def get_plot_3():
    # create some data
    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)

    # create a figure
    p = figure(
        title="Line Plot with Box Zoom Tool",
        width=800,
        height=550,
    )

    p.line(x, y)

    p.add_tools(BoxZoomTool())
    p.add_tools(HoverTool(tooltips=[("Value", "@y")]))

    return p


def main():
    with open("report_creator/templates/plots.html") as file_:
        template = Template(file_.read())

        (javascript, plots) = components([get_plot_1(), get_plot_2(), get_plot_3()])

        with open("aa.html", "w") as fh:
            fh.write(template.render(javascript=javascript, plots=plots))


if __name__ == "__main__":
    main()
