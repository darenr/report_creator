import logging

import pandas as pd
import plotly.express as px
import yaml

import report_creator as rc

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    # set up of example text, plots and dataframes
    df1 = pd.DataFrame(columns=["Name", "Age"])
    df1.Name = ["Lizzie", "Julie", "Andrea"]
    df1.Age = [24, 18, 22]
    df2 = px.data.stocks()

    with open(__file__) as f:
        example_python = f.read()

    with open("examples/example.yaml") as f:
        datastructure = yaml.safe_load(f.read())

    with open("examples/example.txt") as f:
        example_text = f.read()

    with open("README.md") as f:
        example_md = f.read()

    # begin the use of the report_creator package

    with rc.ReportCreator(
        title="Kitchen Sink Report", description="All the things"
    ) as report:
        view = rc.Block(
            rc.Collapse(
                rc.Python(example_python, label="kitchen_sink.py"),
                label="Code (kitchen_sink.py) to create this report",
            ),
            rc.Group(
                rc.Metric(
                    heading="Chances of rain",
                    value="84",
                    unit="%",
                ),
                rc.Metric(heading="Loss", value=0.1),
                rc.Metric(
                    heading="Accuracy",
                    value=0.95,
                    label="Number of correct predictions by Total number of predictions",
                ),
                rc.Metric(
                    heading="Ultimate Answer",
                    value="42",
                ),
                rc.Metric(
                    heading="Confidence",
                    value=95,
                    unit="%",
                    label="How likely is this to be correct.",
                ),
                rc.Metric(
                    heading="Author",
                    value="Douglas Adams",
                ),
                label="Grouped Metrics",
            ),
            rc.MetricGroup(
                df1,
                heading="Name",
                value="Age",
                label="Metrics Group from DataFrame",
            ),
            rc.Text(
                example_text,
                label="Ready Player One",
            ),
            rc.Group(
                rc.Yaml(
                    datastructure,
                    label="Kubernetes Creating a Deployment as YAML",
                ),
                rc.Json(
                    datastructure,
                    label="Kubernetes Creating a Deployment as JSON",
                ),
            ),
            rc.Separator(),
            rc.Markdown(example_md, label="README.md"),
            rc.Widget(
                df1.plot.bar(x="Name", y="Age"), label="Matplotlib Figure - People"
            ),
            rc.Widget(
                px.line(df2, x="date", y=["GOOG", "AAPL", "NFLX", "MSFT"]),
                label="Plotly Figure - Stocks",
            ),
            rc.Separator(),
            rc.Group(
                rc.PieChart(
                    px.data.gapminder()
                    .query("year == 2002")
                    .query("continent == 'Europe'"),
                    values="pop",
                    names="country",
                    label="Pie Chart - 2002 Population of European continent",
                ),
                rc.PieChart(
                    px.data.gapminder()
                    .query("year == 2002")
                    .query("continent == 'Americas'"),
                    values="pop",
                    names="country",
                    label="Pie Chart - 2002 Population of American continent",
                ),
            ),
            rc.Group(
                rc.HistogramChart(
                    px.data.tips(),
                    x="total_bill",
                    dimension="sex",
                    label="Histogram of Total Bill",
                ),
                rc.BoxChart(
                    px.data.tips(),
                    y="total_bill",
                    dimension="time",
                    label="Box Chart of Total Bill by Day",
                ),
            ),
            rc.BarChart(
                px.data.medals_long(),
                x="nation",
                y="count",
                dimension="medal",
                label="Bar Chart - Olympic Medals",
            ),
            rc.Separator(),
            rc.Html(
                "<span>"
                + "".join(
                    [
                        f"""
                <svg height="100" width="100">
                    <circle cx="50" cy="50" r="40" stroke="lightgrey" stroke-width="0.5" fill="{color}" />
                </svg>
                """
                        for color in (
                            "red",
                            "orange",
                            "yellow",
                            "green",
                            "indigo",
                            "violet",
                            "blue",
                        )
                    ]
                )
                + "</span>",
                label="HTML Showing SVG Circles with black border",
            ),
            rc.Separator(),
            rc.Select(
                blocks=[
                    rc.DataTable(
                        px.data.gapminder()
                        .query("year == 2002")
                        .query("continent == 'Europe'"),
                        label="2002 European Population",
                        index=False,
                    ),
                    rc.DataTable(px.data.iris(), label="Iris Petals", index=False),
                    rc.DataTable(
                        px.data.election(),
                        label="2013 Montreal Election",
                        index=False,
                    ),
                    rc.DataTable(
                        px.data.medals_long(),
                        label="Olympic Speed Skating",
                        index=False,
                    ),
                    rc.DataTable(
                        px.data.wind(),
                        label="Wind Intensity",
                        index=False,
                    ),
                    rc.Table(
                        px.data.wind().describe(), label="Wind Description", index=False
                    ),
                ],
                label="Tab Group of Data Tables",
            ),
            rc.Separator(),
            rc.Unformatted(
                r"""
 ___________________________________
< This is an unformatted component >
 -----------------------------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
""",
                label="Unformatted",
            ),
            rc.Group(
                rc.Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d114b7bf12e5f2e5d0_Portrait%20of%20a%20Man%20with%20a%20Medal%20of%20Cosimo%20il%20Vecchio%20de%27%20Medici%20(1475)-p-800.jpg",
                    label="Portrait of a Man with a Medal (1475)",
                    link_to="https://midlibrary.io/focus/sandro-botticelli",
                ),
                rc.Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d07c2a7e39a7e7424e_Detail%20of%20The%20Spring%20(Flora)%20(late%201470s%20or%20early%201480s).jpg",
                    label="The Spring, Flora (late 1470s or early 1480s)",
                ),
                rc.Image(
                    "https://midlibraryassets.b-cdn.net/638266c083c0cd991057c455/655f82d0703381e47145077a_Idealised%20Portrait%20of%20a%20Lady%20(Portrait%20of%20Simonetta%20Vespucci%20as%20Nymph)%20(1480%E2%80%931485).jpg",
                    label="Portrait of Simonetta Vespucci",
                    rounded=False,
                ),
            ),
        )

        report.save(view, "kitchen_sink.html")
