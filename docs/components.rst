Components
==========

Report Creator provides a rich set of components for building reports.

Layout Components
---------------

Block
~~~~~
Vertical container for stacking components:

.. code-block:: python

   Block(
       Heading("Section"),
       Markdown("Content"),
       DataTable(df)
   )

**Key Features:**
- Vertical stacking
- Consistent spacing
- Nestable with other components

Group
~~~~~
Horizontal container for side-by-side components:

.. code-block:: python

   Group(
       Metric("Value 1", 100),
       Metric("Value 2", 200),
       Metric("Value 3", 300)
   )

**Key Features:**
- Horizontal arrangement
- Responsive wrapping
- Equal width distribution

Content Components
----------------

Heading
~~~~~~~
Section headers with multiple levels:

.. code-block:: python

   Heading("Main Title", level=1)
   Heading("Subtitle", level=2)
   Heading("Section", level=3)

**Options:**
- ``level``: 1-5 (default: 1)
- ``label``: Optional anchor link

Markdown
~~~~~~~
Rich text with GitHub-flavored markdown:

.. code-block:: python

   Markdown("""
       # Title
       
       Regular text with **bold** and *italic*.
       
       - List item 1
       - List item 2
       
       ```python
       def example():
           return "Code block"
       ```
       
       | Column 1 | Column 2 |
       |----------|----------|
       | Data 1   | Data 2   |
   """)

**Features:**
- Headers and lists
- Code blocks with syntax highlighting
- Tables
- Links and images
- Task lists
- Emoji support

Data Components
-------------

Metric
~~~~~~
Key performance indicators:

.. code-block:: python

   Metric(
       "Revenue",
       1500000,
       unit="$",
       float_precision=2,
       label="Monthly revenue"
   )

**Features:**
- Automatic number formatting
- Optional units
- Description text
- Color backgrounds

DataTable
~~~~~~~~
Interactive data tables:

.. code-block:: python

   DataTable(
       df,
       label="Sales Data",
       wrap_text=False,
       index=False,
       max_rows=1000
   )

**Features:**
- Search functionality
- Column sorting
- Pagination
- CSV/Excel export
- Responsive layout

Chart Components
--------------

Line
~~~~
Time series and trend visualization:

.. code-block:: python

   Line(
       df,
       x="date",
       y="value",
       dimension="category",
       label="Trends"
   )

**Features:**
- Multiple series support
- Interactive zoom
- Hover tooltips
- Legend
- Date formatting

Bar
~~~
Category comparisons:

.. code-block:: python

   Bar(
       df,
       x="category",
       y="value",
       dimension="group",
       label="Comparison"
   )

**Features:**
- Grouped or stacked bars
- Horizontal or vertical
- Value labels
- Sorting options

Scatter
~~~~~~~
Relationship visualization:

.. code-block:: python

   Scatter(
       df,
       x="x_value",
       y="y_value",
       dimension="group",
       label="Correlation"
   )

**Features:**
- Point coloring
- Size mapping
- Trend lines
- Marginal plots

Special Components
----------------

EventMetric
~~~~~~~~~~
Time-based event tracking:

.. code-block:: python

   EventMetric(
       df,
       condition="status == 'error'",
       date="timestamp",
       frequency="D",
       heading="Daily Errors"
   )

**Features:**
- Automatic aggregation
- Sparkline visualization
- Custom conditions
- Multiple frequencies

Diagram
~~~~~~~
Mermaid.js diagrams:

.. code-block:: python

   Diagram("""
       graph TD
           A[Start] --> B{Decision}
           B -->|Yes| C[OK]
           B -->|No| D[Cancel]
   """)

**Features:**
- Multiple diagram types
- Pan and zoom
- Custom styling
- Auto-formatting 