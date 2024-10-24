import datetime
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

    with open("examples/example.java") as f:
        example_java = f.read()

    with open("README.md") as f:
        example_md = f.read()

    # begin the use of the report_creator package

    with rc.ReportCreator(
        title="Kitchen Sink",
        description="All the things",
        theme="rc",
        code_theme="ir-black",
        diagram_theme="default",
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
                    label="Probability of rain in the next 24 hours using a weather model trained on historical data.",
                ),
                rc.Metric(
                    heading="Loss",
                    value=0.1,
                ),
                rc.Metric(
                    heading="Accuracy",
                    value=0.95,
                    label="Number of correct predictions by Total number of predictions",
                    colored=True,
                ),
                rc.Metric(
                    heading="Today",
                    value=datetime.datetime.now(),
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
                    label="""Douglas Adams was an English author, humourist, and screenwriter, best known
                            for The Hitchhiker's Guide to the Galaxy. Originally a 1978 BBC radio comedy, The
                            Hitchhiker's Guide to the Galaxy developed into a "trilogy" of five books which
                            sold more than 15 million copies in his lifetime.""",
                ),
                label="Grouped Metrics",
            ),
            rc.Group(
                rc.MetricGroup(
                    df1,
                    heading="Name",
                    value="Age",
                    label="Metrics Group from DataFrame",
                ),
                rc.Table(df1, label="Table of DataFrame"),
            ),
            rc.Group(
                rc.EventMetric(
                    pd.read_csv("examples/logs.csv"),
                    condition="status == 200",
                    color="green",
                    date="time",
                    frequency="B",
                    heading="Successful Requests",
                ),
                rc.EventMetric(
                    pd.read_csv("examples/logs.csv"),
                    condition="status == 404",
                    color="red",
                    date="time",
                    frequency="B",
                    heading="Not Found Requests",
                ),
                label="Log File Metrics",
            ),
            rc.Text(
                example_text,
                label="Ready Player One",
            ),
            rc.Yaml(
                datastructure,
                label="Kubernetes Creating a Deployment as YAML",
            ),
            rc.Java(
                example_java,
                label="Example Java",
            ),
            rc.Separator(),
            rc.Markdown(example_md, label="README.md"),
            rc.Widget(df1.plot.bar(x="Name", y="Age"), label="Matplotlib Figure - People"),
            rc.Widget(
                px.line(df2, x="date", y=["GOOG", "AAPL", "NFLX", "MSFT"]),
                label="rc.Widget() of a Plotly Figure",
            ),
            rc.Separator(),
            rc.Group(
                rc.Pie(
                    px.data.gapminder().query("year == 2002").query("continent == 'Europe'"),
                    values="pop",
                    names="country",
                    label="rc.Pie Chart - 2002 Population of European continent",
                ),
                rc.Pie(
                    px.data.gapminder().query("year == 2002").query("continent == 'Americas'"),
                    values="pop",
                    names="country",
                    label="rc.Pie Chart - 2002 Population of American continent",
                ),
            ),
            rc.Group(
                rc.Histogram(
                    px.data.tips(),
                    x="total_bill",
                    dimension="sex",
                    label="rc.Histogram() Chart of Total Bill",
                ),
                rc.Box(
                    px.data.tips(),
                    y="total_bill",
                    dimension="day",
                    label="rc.Box() Chart of Total Bill by Day Dimension",
                ),
            ),
            rc.Select(
                blocks=[
                    rc.Bar(
                        px.data.medals_long(),
                        x="nation",
                        y="count",
                        dimension="medal",
                        label="Bar Chart - Olympic Medals",
                    ),
                    rc.Scatter(
                        df=px.data.iris(),
                        x="sepal_width",
                        y="sepal_length",
                        dimension="species",
                        marginal="histogram",
                        label="Scatter Plot - Iris",
                    ),
                ],
                label="Tabbed Plots",
            ),
            rc.Line(
                px.data.stocks(),
                x="date",
                y=["GOOG", "AAPL", "NFLX", "MSFT"],
                label="Stock Plot",
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
                        for color in rc.report_creator_colors
                    ]
                )
                + "</span>",
                label="HTML SVG Circles of Report Creator Colors",
            ),
            rc.Separator(),
            rc.Select(
                blocks=[
                    rc.DataTable(
                        px.data.gapminder().query("year == 2002").query("continent == 'Europe'"),
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
                ],
                label="Tab Group of Data Tables",
            ),
            rc.Separator(),
            rc.Diagram(
                src="""
mindmap
  root((Artificial Intelligence))
    subtopic1(Machine Learning)
      subtopic1a(Supervised Learning)
        subtopic1a1(Linear Regression)
        subtopic1a2(Decision Trees)
        subtopic1a3(SVM)
      subtopic1b(Unsupervised Learning)
        subtopic1b1(Clustering)
        subtopic1b2(Dimensionality Reduction)
      subtopic1c(Reinforcement Learning)
        subtopic1c1(Q-Learning)
        subtopic1c2(Deep Q-Networks)
        subtopic1c3(Policy Gradient)
    subtopic2(Neural Networks)
      subtopic2a(Feedforward Networks)
        subtopic2a1(Activation Functions)
        subtopic2a2(Backpropagation)
      subtopic2b(Recurrent Networks)
        subtopic2b1(LSTM)
        subtopic2b2(GRU)
      subtopic2c(Convolutional Networks)
        subtopic2c1(Image Classification)
        subtopic2c2(Object Detection)
    subtopic3(Natural Language Processing)
      subtopic3a(Tokenization)
      subtopic3b(Word Embeddings)
        subtopic3b1(Word2Vec)
        subtopic3b2(GloVe)
      subtopic3c(Transformers)
        subtopic3c1(BERT)
        subtopic3c2(GPT)
    subtopic4(Computer Vision)
      subtopic4a(Image Recognition)
      subtopic4b(Semantic Segmentation)
      subtopic4c(Object Detection)
    subtopic5(Generative Models)
      subtopic5a(GANs)
        subtopic5a1(Discriminator)
        subtopic5a2(Generator)
      subtopic5b(VAEs)
        subtopic5b1(Latent Space)
        subtopic5b2(Reconstruction)
    subtopic6(Ethics in AI)
      subtopic6a(Bias)
      subtopic6b(Privacy)
      subtopic6c(Transparency)
      subtopic6d(Accountability)


                """,
                label="Example AI Mind Map Diagram",
            ),
            rc.Diagram(
                src="""
                    graph LR
                        A[Square Rect] -- Link text --> B((Circle))
                        A --> C(Round Rect)
                        B --> D{Rhombus}
                        C --> D
                """,
                label="Example Git Graph",
            ),
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
                    "https://assets.midlibrary.io/6629522db4ea3030cf8c4f18/6629522eb4ea3030cf8c5df2_Portrait%20of%20a%20Man%20with%20a%20Medal%20of%20Cosimo%20il%20Vecchio%20de%27%20Medici%20(1475).jpg",
                    label="Portrait of a Man with a Medal (1475)",
                    link_to="https://midlibrary.io/focus/sandro-botticelli",
                    convert_to_base64=True,
                ),
                rc.Image(
                    "https://assets.midlibrary.io/6629522db4ea3030cf8c4f18/6629522eb4ea3030cf8c5df1_Detail%20of%20The%20Spring%20(Flora)%20(late%201470s%20or%20early%201480s).jpg",
                    label="The Spring, Flora (late 1470s or early 1480s)",
                    convert_to_base64=True,
                ),
                rc.Image(
                    "https://assets.midlibrary.io/6629522db4ea3030cf8c4f18/6629522eb4ea3030cf8c5df0_Idealised%20Portrait%20of%20a%20Lady%20(Portrait%20of%20Simonetta%20Vespucci%20as%20Nymph)%20(1480%E2%80%931485).jpg",
                    label="Portrait of Simonetta Vespucci",
                    convert_to_base64=True,
                ),
            ),
        )

        report.save(view, "index.html")
