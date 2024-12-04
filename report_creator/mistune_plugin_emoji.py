import emoji


def emojis(md) -> None:
    INLINE_EMOJI_PATTERN = r":[A-Za-z0-9._’()_-]+:"

    def parse_inline_emoji_icon(inline, m, state) -> int:
        state.append_token(
            {
                "type": "emoji_icon_ref",
                "attrs": {"emoji_str": m.group(0)},
            }
        )
        return m.end()

    def render_inline_emoji_icon(renderer, emoji_str: str) -> str:
        return emoji.emojize(emoji_str, variant="emoji_type", language="en")

    md.inline.register("emojis", INLINE_EMOJI_PATTERN, parse_inline_emoji_icon)
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("emoji_icon_ref", render_inline_emoji_icon)


import mistune

markdown = mistune.create_markdown(plugins=[emojis])

with open("emoji.html", "w", encoding="utf-8") as f:
    print(
        """
        <!DOCTYPE html>
            <html>
            <body>
            <p>
    """,
        file=f,
    )
    print(markdown("We :red_heart: all :pizza: in Engineering"), file=f)

    print("</p></body></html>", file=f)
