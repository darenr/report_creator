import emoji

# https://github.com/lepture/mistune/blob/master/src/mistune/plugins/url.py


__all__ = ["emoji_icon"]

INLINE_EMOJI_PATTERN = r":[A-Za-z0-9._’()_-]+:"


def parse_inline_emoji_icon(inline, m, state) -> int:
    text = m.group(0)
    pos = m.end()

    state.append_token(
        {
            "type": "emoji_icon_ref",
            "attrs": {"emoji_str": text},
        }
    )
    return pos


def render_inline_emoji_icon(renderer, emoji_str: str) -> str:
    return f"{emoji.emojize(emoji_str)}"


def emoji_plugin(md) -> None:
    md.inline.register("emoji_plugin", INLINE_EMOJI_PATTERN, parse_inline_emoji_icon)
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("emoji_icon_ref", render_inline_emoji_icon)


import mistune

markdown = mistune.create_markdown(plugins=[emoji_plugin])
print(markdown("We :love: :pizza:"))  # <p>😄</p>
