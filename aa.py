import mistune


class BlockScriptTagRenderer(mistune.HTMLRenderer):



markdown = mistune.create_markdown(renderer=BlockScriptTagRenderer())

# Example usage
markdown_text = """
This is some markdown text.

<div>This is a div tag.</div>

<script>
// This is a script tag that will be blocked.
alert("Hello!");
</script>
"""

html_output = markdown(markdown_text)
print(html_output)
