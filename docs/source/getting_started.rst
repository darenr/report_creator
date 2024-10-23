Getting Started
===============

.. _installation:

Installation
------------

To use ``report_creator``, first install it using pip:

.. admonition:: Installation
   :class: note

   $ pip install report_creator --upgrade

Example Usage
-------------

.. code-block:: python3

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
         rc.Bar(px.data.medals_long(),
                  x="nation",
                  y="count",
                  dimension="medal",
                  label="Bar Chart - Olympic Medals",
         ),
         rc.Scatter(
               px.data.iris(),
               x="sepal_width",
               y="sepal_length",
               dimension="species",
               marginal="histogram",
               label="Scatter Plot - Iris",
         ),
      )

      report.save(view, "report.html") 

Flow
----

With an instance of ``rc.ReportCreator()`` you add components, there are two container components, one that lays out vertically, called
``rc.Block()`` and one that lays out child components horizontally in a flow called ``rc.Group()``. Every component allows for a 
label that is styled approprite to the component. A special container called ``rc.Select()`` is used to show tabs. It should be noted that 
for reports that are printed the ``rc.Select()`` component might not be suitable.

Text
----

There are three types of text components, ``rc.Text()``, ``rc.Html()``, and ``rc.Markdown()``. The ``rc.Text()`` is a simple component 
for plain text, ``rc.Html()`` is to be used if you already have html, while ``rc.Markdown()`` is very flexible, the markdown is the 
GitHub extended syntax, tables will be rendered properly, and code in Markdown will be styled to match code in the code components.

Code
----

There are components for ``rc.Yaml()``, ``rc.Json()``, ``rc.Python()``, ``rc.Java()``, and ``rc.Sql()``,  each will format and
will render with color syntax highlighting.

Images
------

One of the goals of report creator is to be self-contained, images may not be visible, or available at view time so the ``rc.Image()``
component allows an option (``convert_to_base64``) which will retrieve at report creation time the image from the url and keep the 
local copy in the report. This can be used to get around CORS issues also. Images, like all the compoents will be styled and laid 
out to look consistent and attractive.

Charts
------

There are a number of charting components, ``rc.Bar()``, ``rc.Scatter()``, ``rc.Histogram()``, ``rc.Box()``, ``rc.Line()``, and ``rc.Pie()``.
These are wrappers around plotly express componets. There is also a ``rc.Widget()`` component that can be used anywhere 
the object supports the ``repr_html`` that is used by Jupyter notebooks (for example ``matplotlib`` object)

Tables
------

There are two types of table components, ``rc.Table()`` for simple tables, and ``rc.DataTable()`` for a richer experience, the data table
will paginate data, is searchablem, supports export to pdf and print. Both table objects will construct from table-like objects. In the
``rc.DataTable()`` you can specify precision to keep numeric values more readable. 

Metrics
-------

A common use for reports is to show numeric/text results, like for example scores. These will be layed out in a flow that is responsive. 
You can also color them if you like, you can't change the color, only indicate that they should be colored. The layout engine will ensure
that backgound/text colors always have legible contrast, and that never adjacent metrics will have the same color. The default is a while
backgound. The component to use is called ``rc.Metric()`` - ctor elements for heading, value and optionally units. As with any component you
can also use a label which can serve as a description. Some times you have your data in a ``Pandas`` dataframe and it's inconventient to 
expand the rows, in this case the component ``rc.MetricGroup()`` takes a dataframe and the column names for the headings and value, 
a component will be created *for each row.*

Miscellaneous
-------------

There are compoents also to be used as separators ``rc.Separator()``, to hide content under a drop down ``rc.Collapse()``, and 
to include diagrams in |mermaid_location_link| ``rc.Diagram()``

.. |mermaid_location_link| raw:: html

   <a href="https://mermaid.js.org/syntax/examples.html" target="_blank">Mermaid JS syntax</a>


.. code-block:: python3

   rc.Diagram("""
      graph LR
         A[Square Rect] -- Link text --> B((Circle))
         A --> C(Round Rect)
         B --> D{Rhombus}
         C --> D
      """)


Produces:

.. mermaid::

   graph LR
      A[Square Rect] -- Link text --> B((Circle))
      A --> C(Round Rect)
      B --> D{Rhombus}
      C --> D


