import emoji

# https://github.com/lepture/mistune/blob/master/src/mistune/plugins/url.py


__all__ = ["emoji_icon"]

INLINE_EMOJI_PATTERN = r":[A-Za-z0-9._’()_-]+:"


def parse_inline_emoji_icon(inline, m, state) -> int:
    text = m.group(0)
    pos = m.end()
    if state.in_link:
        inline.process_text(text, state)
        return pos
    state.append_token(
        {
            "type": "link",
            "children": [{"type": "text", "raw": text}],
            "attrs": {"emoji_icon": text},
        }
    )
    return pos


def render_inline_emoji_icon(renderer: "BaseRenderer", text: str) -> str:
    return f"{emoji.emojize(text)}"


def emoji_icon(md) -> None:
    md.inline.register("emoji_icon", INLINE_EMOJI_PATTERN, parse_inline_emoji_icon)
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("emoji_icon", render_inline_emoji_icon)


import mistune

markdown = mistune.create_markdown(plugins=[emoji_icon])
print(markdown(":smile:"))  # <p>😄</p>
