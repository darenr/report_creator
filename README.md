# Report Creator

[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](https://www.apache.org/licenses/LICENSE-2.0)
[![PyPI Version](https://img.shields.io/pypi/v/report_creator.svg?style=for-the-badge&color=blue)](https://pypi.org/project/report_creator)
[![Python Versions](https://img.shields.io/pypi/pyversions/report_creator.svg?logo=python&logoColor=white&style=for-the-badge)](https://pypi.org/project/report_creator)

Library to assemble reports in HTML from various components using python

## Features

* [x] Good pandas/dataframe/table support
* [x] Look modern
* [x] Allows markdown as input for text blocks
* [x] Allows html as input
* [x] A few simple components for things like metrics ("Accuracy: 87%") from a triple of key, value
* [x] Support for plotting figures, interactive `plotly` and `matplotlib`
* [x] images (styled by the library)
* [x] `json`/`yaml`/`python` code blocks with color syntax highlighting
* [x] Support tabs
* [x] Add support for any Jupyter widget, any object that renders in a notebook should render to a report
* [x] Add built-in easy plotting that looks stylistically consistent with the report
* [ ] Add a metric type for timeseries data which should some aggregate function of the data, and plot over time.
* [ ] Add choropleth map plot type
* [ ] Add bookmark anchors to blocks
* [ ] Add a Table of Contents option based on labels of top-level-blocks
* [ ] Youtube embeds rc.Video(url: str, label: str)
* [ ] File attachments (downloadable from page)

## Example

```python3

import report_creator as rc

with rc.ReportCreator("My Report") as report:

    view = rc.Block(
        rc.Text("""It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of light, it was the season of darkness, it was the spring of hope, it was the winter of despair.""", 
        label="Charles Dickens, A Tale of Two Cities"),
        rc.Group(
            rc.Metric(
                heading="Answer to Life, The Universe, and Everything",
                value="42",
            ),
            rc.Metric(
                heading="Author",
                value="Douglas Adams",
            ),   
        ),
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
    )

    report.save(view, "report.html") 
```

## Development

``` .python
conda create --name rc python=3.9
conda activate rc
pip install -r requirements.txt -U

# optionally for pretty html generation
pip install beautifulsoup4 lxml

# recommended installs for code hygiene
pip install ruff

# build "kitchen_sink" example

make

# install local package
pip install -e .

```

## Dev Notes

* **4/18/24 - no breaking changes**, all changes should go through standard deprecation policies
* The Blocks/Groups use css [flex](https://css-tricks.com/snippets/css/a-guide-to-flexbox/).
  * Blocks flow vertically (columns)
* Groups flow horizontal (row).
* To render math you'll need to `pip install md4mathjax`
