from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html, components

from string import Template

import pandas as pd
import numpy as np

from bokeh.models import ColumnDataSource
from bokeh.palettes import GnBu3, OrRd3
from bokeh.plotting import figure, show
from bokeh.transform import dodge

def get_plot_1():
    fruits = ['Apples', 'Pears', 'Nectarines', 'Plums', 'Grapes', 'Strawberries']
    years = ['2015', '2016', '2017']

    data = {'fruits' : fruits,
            '2015'   : [2, 1, 4, 3, 2, 4],
            '2016'   : [5, 3, 3, 2, 4, 6],
            '2017'   : [3, 2, 4, 4, 5, 3]}

    source = ColumnDataSource(data=data)

    p = figure(x_range=fruits, y_range=(0, 10), title="Fruit Counts by Year",
            height=350, toolbar_location=None, tools="")

    p.vbar(x=dodge('fruits', -0.25, range=p.x_range), top='2015', source=source,
        width=0.2, color="#c9d9d3", legend_label="2015")

    p.vbar(x=dodge('fruits',  0.0,  range=p.x_range), top='2016', source=source,
        width=0.2, color="#718dbf", legend_label="2016")

    p.vbar(x=dodge('fruits',  0.25, range=p.x_range), top='2017', source=source,
        width=0.2, color="#e84d60", legend_label="2017")

    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"
    
    return p

def get_plot_2():

    fruits = ['Apples', 'Pears', 'Nectarines', 'Plums', 'Grapes', 'Strawberries']
    years = ["2015", "2016", "2017"]

    exports = {'fruits' : fruits,
            '2015'   : [2, 1, 4, 3, 2, 4],
            '2016'   : [5, 3, 4, 2, 4, 6],
            '2017'   : [3, 2, 4, 4, 5, 3]}
    imports = {'fruits' : fruits,
            '2015'   : [-1, 0, -1, -3, -2, -1],
            '2016'   : [-2, -1, -3, -1, -2, -2],
            '2017'   : [-1, -2, -1, 0, -2, -2]}

    p = figure(y_range=fruits, height=350, x_range=(-16, 16), title="Fruit import/export, by year",
            toolbar_location=None)

    p.hbar_stack(years, y='fruits', height=0.9, color=GnBu3, source=ColumnDataSource(exports),
                legend_label=[f"{year} exports" for year in years])

    p.hbar_stack(years, y='fruits', height=0.9, color=OrRd3, source=ColumnDataSource(imports),
                legend_label=[f"{year} imports" for year in years])

    p.y_range.range_padding = 0.1
    p.ygrid.grid_line_color = None
    p.legend.location = "top_left"
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    
    return p

with open("experimental/template.html") as ft:
    t = Template(ft.read())

    (javascript, plots) = components({"plot1": get_plot_1(), "plot2": get_plot_2()})

    with open("aa.html", "w") as fh:
        fh.write(t.substitute(javascript=javascript, plot1=plots['plot1'], plot2=plots['plot2']))
