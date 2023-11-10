import logging
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)

from components import *
from report_creator import ReportCreator

if __name__ == "__main__":
    emp_df = pd.read_csv("employees.csv")

    boring_df = pd.DataFrame(
        [["Daren", 42], ["Yekaterina", 15], ["Andrea", 14]], columns=["Name", "Age"]
    )

    fig = boring_df.plot.bar(x="Name", y="Age")

    # fig = boring_df.plot.bar(x="Name", y="Age")

    report = ReportCreator("My Report")

    view = Blocks(
        Group(
            BigNumber(
                heading="Chances of rain",
                value="84%",
            ),
            BigNumber(heading="Loss", value=0.1),
            BigNumber(heading="Accuracy", value=95),
        ),
        Text(
            """Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, “and what is the use of a book,” thought Alice “without pictures or conversations?”

So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.

There was nothing so very remarkable in that; nor did Alice think it so very much out of the way to hear the Rabbit say to itself, “Oh dear! Oh dear! I shall be late!” (when she thought it over afterwards, it occurred to her that she ought to have wondered at this, but at the time it all seemed quite natural); but when the Rabbit actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge.
        """,
            label="Alice in Wonderland",
        ),
        Yaml(
            """
doe: "a deer, a female deer"
ray: "a drop of golden sun"
pi: 3.14159
xmas: true
french-hens: 3
calling-birds:
- huey
- dewey
- louie
- fred
xmas-fifth-day:
calling-birds: four
french-hens: 3
golden-rings: 5
partridges:
    count: 1
    location: "a pear tree"
turtle-doves: two             
        """,
            label="Random Yaml",
        ),
        Python(
            "import pandas as pd\n\ndf = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})",
            label="Some random python",
        ),
        DataTable(boring_df, label="Boring data", index=False),
        Plot(fig, label="Chart"),
        Markdown(
            """
> #### The quarterly results look great!
>
> - Revenue was off the chart.
> - Profits were higher than ever.
>
>  *Everything* is going according to **plan**.                 
        """
        ),
        Plot(fig, label="Chart"),
        DataTable(emp_df, label="Employees", index=False),
    )

    report.save(view, "aa.html", theme="light")
