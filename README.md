# Report Creator

[![License](https://img.shields.io/badge/license-Apache-blue.svg?style=for-the-badge)](https://www.apache.org/licenses/LICENSE-2.0)
[![PyPI Version](https://img.shields.io/pypi/v/report_creator.svg?style=for-the-badge&color=blue)](https://pypi.org/project/report_creator)
[![Python Versions](https://img.shields.io/pypi/pyversions/report_creator.svg?logo=python&logoColor=white&style=for-the-badge)](https://pypi.org/project/report_creator)

Library to assemble reports in HTML from various components using python

## Features

* [x] good pandas/dataframe support
* [x] look modern
* [x] allows markdown as input for text blocks
* [x] allows html as input
* [x] a few simple components for things like metrics ("Accuracy: 87%") from a triple of key, value, Optional[description]
* [x] support for plotting figures, interactive (`plotly``) and `matplotlib`
* [x] images (styled by the library)
* [x] `json`/`yaml`/`python` code blocks with color syntax highlighting
* [x] support tabs
* [ ] Youtube embeds rc.Video(url: str, label: str)
* [ ] File attachments (downloadable from page)

## Example

``` .python

    import report_creator as rc

    with ReportCreator("My Report") as report:

        view = rc.Block(
            Text("""It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of light, it was the season of darkness, it was the spring of hope, it was the winter of despair.""", 
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
        )

        report.save(view, "report.html", theme="light")
```

## Development

``` .python
conda create --name rc python=3.9
conda activate rc
pip install -r requirements.txt -U

# optionally for pretty html generation
pip install beautifulsoup4 lxml

# recommended installs for code hygiene
pip install black isort

# run kitchen_sink.py
PYTHONPATH=. python examples/kitchen_sink.py
```

## Dev Notes

* The Blocks/Groups use css [flex](https://css-tricks.com/snippets/css/a-guide-to-flexbox/).
  * Blocks flow vertically (columns)
* Groups flow horizontal (row).
* to render math you'll need to `pip install md4mathjax`

## Ideas

* [html chart](https://codepen.io/sean_codes/pen/VNQVJE)
* [css pie chart](https://codepen.io/t_afif/pen/XWaPXZO)