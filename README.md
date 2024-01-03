[![License](https://img.shields.io/badge/license-Apache-blue.svg?style=for-the-badge)](https://www.apache.org/licenses/LICENSE-2.0)
[![PyPI Version](https://img.shields.io/pypi/v/report_creator.svg?style=for-the-badge&color=blue)](https://pypi.org/project/report_creator)
[![Python Versions](https://img.shields.io/pypi/pyversions/report_creator.svg?logo=python&logoColor=white&style=for-the-badge)](https://pypi.org/project/report_creator)


# Report Creator

Library to assemble reports in HTML from various components using python

## Features

- good pandas support
- looks modern
- allows markdown as input for text blocks
- allows html as input
- a few simple components for things like metrics ("Accuracy: 87%") from a triple of key, value, Optional[description]
- support for plotting
- images (styled by the library)
- json/yaml/python blocks with color syntax highlighting
- integrate with langchain
- (stretch) support tabs, if not then each tab can just be additional vertical content

## Example

``` .python
    view = Blocks(
        Group(
            Statistic(
                heading="Chances of rain",
                value="84%",
            ),
            Statistic(heading="Loss", value=0.1),
            Statistic(heading="Accuracy", value=95),
        ),
        Text("Some Text")
    )

    report.save(view, "report.html", theme="light")
```

## local development

```
pip install -e .
```
