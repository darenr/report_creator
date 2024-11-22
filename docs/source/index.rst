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

Report Creator will generate a report in HTML format that you can share with others, fully self contained, even Images 
can be base64 encoded and included in the report. The report can be viewed in a browser, or printed to PDF. Use simple
Python components to create a report, for text, code, images, and data visualizations. Markdown can be used in its own
component, or in the label/description of any component. While the charging is very capable, Report Creator allows you 
also to add any matplotlib figure, along with any python object that supports the ``_repr_html_()`` function (which many 
libraries support since this is used in Jupyter notebooks). Report Creator does its best to make the report look modern
and consistent even with different components coming from different sources. For diagramming there's a ``rc.Diagram()`` component 
which can be used with any valid |mermaid_js| syntax.

.. |mermaid_js| raw:: html

   <a href="https://mermaid-js.github.io/mermaid/" target="_blank">mermaid js</a>


The python file |kitchen_sink_location_source| is an example (in the ``examples`` folder) that demonstrates every 
component, and many of the options. The report created from that can be seen |kitchen_sink_location_output|.

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
