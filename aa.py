import emoji

# https://github.com/lepture/mistune/blob/master/src/mistune/plugins/url.py


__all__ = ["emoji_icon"]

INLINE_EMOJI_PATTERN = r":[A-Za-z0-9._’()_-]+:"


def parse_inline_emoji_icon(inline, m, state) -> int:
    state.append_token({"type": "text", "raw": m.group(0)})
    return m.end()


def render_inline_emoji_icon(renderer, text: str) -> str:
    return f"{emoji.emojize(text)}"


def emoji(md) -> None:
    md.inline.register("emoji", INLINE_EMOJI_PATTERN, parse_inline_emoji_icon)
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("emoji_icon_ref", render_inline_emoji_icon)


import mistune

markdown = mistune.create_markdown(plugins=[emoji])
print(markdown(":smile:"))  # <p>😄</p>
