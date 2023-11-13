# report_creator
Tool to assemble reports in HTML from various components

## Features:

- good pandas support
- looks modern
- allows markdown as input for text blocks
- allows html as input
- a few simple components for things like metrics ("Accuracy: 87%") from a triple of key, value, Optional[description]
- declarative support for plotting
- images (styled by the library)
- json/yaml/python blocks with color syntax highlighting
- integrate with langchain
- (stretch) support tabs, if not then each tab can just be additional vertical content


## Example

```python3
    view = Blocks(
        Group(
            BigNumber(
                heading="Chances of rain",
                value="84%",
            ),
            BigNumber(heading="Loss", value=0.1),
            BigNumber(heading="Accuracy", value=95),
        ),
        Text("Some Text")
    )

    report.save(view, "report.html", theme="light")
```