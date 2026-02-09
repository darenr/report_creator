import logging
import textwrap

import pandas as pd
import plotly.express as px

import report_creator as rc

logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    # set up of example text, plots and dataframes
    df1 = pd.DataFrame(columns=["Name", "Age"])
    df1.Name = ["Lizzie", "Julie", "Andrea"]
    df1.Age = [24, 18, 22]
    df2 = px.data.stocks()

    with open(__file__) as f:
        example_python = f.read()

    with open("examples/example.txt") as f:
        example_text = f.read()

    with open("README.md") as f:
        example_md = f.read()

    # Try to import d3blocks for the D3 component example
    try:
        from d3blocks import D3Blocks

        d3 = D3Blocks()
        d3_df = d3.import_example("energy")
        # Ensure compatibility with newer pandas versions that might use PyArrow backed strings
        # d3blocks/ismember might fail with ArrowStringArray
        for col in d3_df.columns:
            if str(d3_df[col].dtype).startswith("string"):
                d3_df[col] = d3_df[col].astype(object)

        d3.sankey(d3_df, showfig=False)
        d3_component = rc.D3(d3, label="Sankey Chart using D3Blocks")
    except (ImportError, Exception) as e:
        logging.warning(f"Could not create D3 example: {e}")
        d3_component = rc.Markdown(
            f"**d3blocks** example skipped due to error: {e}",
            label="D3Blocks Error",
        )

    # begin the use of the report_creator package

    with rc.ReportCreator(
        title="Kitchen Sink",
        description="**All** the *things*",
        footer=f"Made with `report_creator` (v{rc.__version__}), `pip install report-creator` :red_heart:",
    ) as report:
        view = rc.Block(
            rc.Collapse(
                rc.Python(example_python, label="kitchen_sink.py"),
                label="Code (kitchen_sink.py) to create this report",
            ),
            rc.Group(
                rc.Metric(
                    heading="Hitchhiker's Guide to the Galaxy",
                    value="Don't Panic",
                ),
                rc.Metric(
                    heading="Gross profit margin",
                    value=65,
                    unit="%",
                    label="A commonly tracked metric by finance departments that can be found on an income statement.",
                ),
                rc.Metric(
                    heading="Accuracy",
                    value=0.95,
                    label="Number of correct predictions by Total number of predictions",
                ),
                rc.Metric(
                    heading="Recurring revenue",
                    value="$10.7B",
                    label="Recurring revenue is the portion of a company's revenue that is predictable and stable.",
                ),
                rc.Metric(
                    heading="Capacity utilization",
                    value=42,
                    unit="%",
                    label="A popular productivity metric that measures the ratio of actual output to potential output.",
                ),
                rc.Metric(
                    heading="Asset turnover ratio",
                    value=3.3,
                    label="Asset turnover ratio is a financial metric that shows how efficiently a company generates revenue from its assets.",
                ),
                label="Grouped Metrics",
            ),
            rc.Separator(),
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
                    color="black",
                    date="time",
                    frequency="B",
                    heading="Successful Requests",
                ),
                rc.EventMetric(
                    pd.read_csv("examples/logs.csv"),
                    condition="status == 404",
                    color="black",
                    date="time",
                    frequency="B",
                    heading="Not Found Requests",
                ),
                label="Log File Metrics",
            ),
            rc.Accordion(
                blocks=[
                    rc.Markdown(
                        """
                            > Love all, trust a few, do wrong to none.

                            > Moderate lamentation is the right of the dead, excessive grief the enemy to the living.
                        """,
                        label="All's Well That Ends Well",
                    ),
                    rc.Markdown(
                        """
                            >Something is rotten in the state of Denmark.

                            > There are more things in heaven and earth, Horatio,  
                            > Than are dreamt of in our philosophy.

                            > To be, or not to be, that is the question.

                            > How all occasions do inform against me, and spur my dull revenge.
                        """,
                        label="Hamlet",
                    ),
                    rc.Markdown(
                        """
                        > But, soft, what light through yonder window breaks?  
                        > It is the east, and Juliet is the sun.

                        > O happy dagger,  
                        > This is thy sheath: there rust, and let me die.

                        > For never was a story of more woe  
                        > Than this of Juliet and her Romeo.
                        """,
                        label="Romeo and Juliet",
                    ),
                ],
                label="Accordion",
            ),
            rc.Text(
                example_text,
                label="Alice’s Adventures in Wonderland (Text)",
            ),
            rc.Group(
                rc.Java(
                    textwrap.dedent("""
                    public class HelloWorld {
                        public static void main(String[] args) {
                            // Print "Hello, World!" to the console
                            System.out.println("Hello, World!");
                        }
                    }
                    """),
                    label="Java",
                ),
                rc.Prolog(
                    textwrap.dedent("""
                    % Define a rule to display the message
                    hello_world :- 
                        write('Hello, World!'), nl.

                    % To run, consult the file and call the rule:
                    % ?- hello_world.
                    """),
                    label="Prolog",
                ),
            ),
            rc.Group(
                rc.Yaml(
                    textwrap.dedent("""
                    # Example YAML configuration
                    version: 1.0
                    services:
                      web:
                        image: nginx:latest
                        ports:  
                          - "80:80"
                      db:
                        image: postgres:latest
                        environment:
                          POSTGRES_USER: user
                          POSTGRES_PASSWORD: password
                    """),
                    label="YAML",
                ),
                rc.Json(
                    textwrap.dedent("""
                    {
                        "name": "Alice",
                        "age": 25,
                        "city": "Wonderland",
                        "hobbies": ["reading", "adventures", "tea parties", "cats"]
                    }
                    """),
                    label="JSON",
                ),
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
                ],
                label="Tab Group of Data Tables",
            ),
            rc.Separator(),
            rc.Select(
                blocks=[
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
                                subtopic6e(Fairness)
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
                        pan_and_zoom=False,
                        label="Example Git Graph",
                    ),
                ],
                label="Tab Group of Diagrams",
            ),
            rc.Separator(),
            d3_component,
            rc.Separator(),
            rc.Radar(
                df=pd.DataFrame(
                    {
                        "Llama3.1": {
                            "MMLU (Accuracy)": 0.72,
                            "TruthfulQA (Accuracy)": 0.65,
                            "Winogrande (Accuracy)": 0.85,
                            "ARC-Challenge (Accuracy)": 0.48,
                            "ARC-Easy (Accuracy)": 0.78,
                            "CommonsenseQA (Accuracy)": 0.68,
                            "BoolQ (Accuracy)": 0.80,
                            "CB (Accuracy)": 0.88,
                            "COPA (Accuracy)": 0.95,
                            "WiC (Accuracy)": 0.75,
                            "ReCoRD (F1)": 0.72,
                            "RACE-h (Accuracy)": 0.60,
                            "RACE-m (Accuracy)": 0.65,
                        },
                        "Llama3.2": {  # Example of a second model
                            "MMLU (Accuracy)": 0.75,
                            "TruthfulQA (Accuracy)": 0.68,
                            "Winogrande (Accuracy)": 0.88,
                            "ARC-Challenge (Accuracy)": 0.52,
                            "ARC-Easy (Accuracy)": 0.81,
                            "CommonsenseQA (Accuracy)": 0.71,
                            "BoolQ (Accuracy)": 0.83,
                            "CB (Accuracy)": 0.90,
                            "COPA (Accuracy)": 0.97,
                            "WiC (Accuracy)": 0.78,
                            "ReCoRD (F1)": 0.75,
                            "RACE-h (Accuracy)": 0.63,
                            "RACE-m (Accuracy)": 0.68,
                        },
                    }
                ).T,
                lock_minimum_to_zero=True,
                filled=False,
                label="Radar Chart of Model Performance",
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

        report.save(view, "index.html", prettify_html=False)
