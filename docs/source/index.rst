.. Project documentation master file

.. meta::
    :description lang=en:
        Report creator is a library to create self contained HTML reports from python code for text, code, images, and data visualizations.

Report Creator
==============

|PyPI|_ |Python|_ |GitHub|_

.. |PyPI| image:: https://img.shields.io/pypi/v/report_creator.svg?style=for-the-badge&logo=pypi&logoColor=white
..  _PyPI: https://pypi.org/project/report_creator/
.. |Python| image:: https://img.shields.io/pypi/pyversions/report_creator.svg?style=for-the-badge&logo=pypi&logoColor=white
..  _Python: https://pypi.org/project/report_creator/

.. |GitHub| image:: https://img.shields.io/github/license/darenr/report_creator?style=for-the-badge&logo=pypi&logoColor=white
..  _GitHub: https://github.com/darenr/report_creator

Report Creator generates shareable, self-contained HTML reports, including base64-encoded 
images. These reports are viewable in any browser or printable to PDF. Using simple Python 
components, it creates reports incorporating text, code, images, and data visualizations.
Markdown is supported within dedicated components or as labels/descriptions for other 
components. The philosophy for layout is that components flow in either the horizontal 
(``rc.Group()``) or Vertical (``rc.Block()``) direction.

.. code-block:: python

   import report_creator as rc

   with rc.ReportCreator(title="Report", logo="octocat") as report:
      report.save(
         rc.Block(
               rc.Heading("Hello World", level=1),
               rc.Markdown("This is a simple report using Report Creator."),
         ),
         "report.html",
      )


Beyond its built-in capabilities, Report Creator allows the inclusion of 
any ``matplotlib`` figure and any Python object implementing the ``_repr_html_()`` function 
(a common feature in libraries supporting Jupyter notebooks). Report Creator ensures 
a modern and consistent report appearance, even with components from diverse sources. 
For diagrams, the ``rc.Diagram()`` component supports any valid |mermaid_js| syntax.

.. |mermaid_js| raw:: html

   <a href="https://mermaid-js.github.io/mermaid/" target="_blank">mermaid js</a>


The python file |kitchen_sink_location_source| is an example (in the ``examples`` folder) 
that demonstrates every component, and many of the options. The created report can be 
viewed |kitchen_sink_location_output|.

.. |kitchen_sink_location_source| raw:: html

   <a href="https://github.com/darenr/report_creator/blob/main/examples/kitchen_sink.py" target="_blank">kitchen_sink.py</a>

.. |kitchen_sink_location_output| raw:: html

   <a href="https://darenr.github.io/report_creator/" target="_blank">here</a>


Contents
--------

.. toctree::
   :titlesonly:
   :maxdepth: 2

   getting_started
   api
