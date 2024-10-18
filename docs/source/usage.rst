Usage
=====

.. _installation:

Installation
------------

To use ``report_creator``, first install it using pip:

.. code-block:: console

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