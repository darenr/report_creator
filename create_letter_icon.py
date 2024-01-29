import base64
import random
import sys
import re
from string import Template


def random_color_generator(word: str):
    seed = sum([ord(c) for c in word]) % 13
    random.seed(seed)
    r = random.randint(10, 245)
    g = random.randint(10, 245)
    b = random.randint(10, 245)

    text_color = "black" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.5 else "white"

    return f"#{r:02x}{g:02x}{b:02x}", text_color


def svg_to_base64_datauri(svg_contents: str):
    base64_encoded_svg_contents = base64.b64encode(svg_contents.encode())
    return "data:image/svg+xml;base64," + base64_encoded_svg_contents.decode()


def create_word_icon(label: str, width: int = 150):
    match = re.findall(r"(^[a-zA-Z]{1}).*?(\d+[a-z]{1})", label)
    icon_text = ''.join(match[0] if match else [label[0]])
    icon_color, text_color = random_color_generator(label)
    cx = width / 2
    cy = width / 2
    r = width / 2
    fs = int(r / 25)

    t = Template(
        """
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="${width}" height="${width}">

            <style>
                text {
                    font-size: ${fs}em;
                    font-family: lucida console, Fira Mono, monospace;
                    text-anchor: middle;
                    stroke-width: 1px;
                    font-weight: bold;
                    alignment-baseline: central;
                }

            </style>

            <circle cx="${cx}" cy="${cy}" r="${r}" fill="${icon_color}" />
            <text x="50%" y="50%" fill="${text_color}">${icon_text}</text>   
        </svg>
    """.strip()
    )

    icon_svg = t.substitute(**locals())
    return svg_to_base64_datauri(icon_svg)


if __name__ == "__main__":
    datauri = create_word_icon(sys.argv[1] if 1 < len(sys.argv) else "H")
    print('Example usages:')
    print(f'  or <img src="{datauri}" />')
    print('   or create_word_icon.py "Hello" > hello.svg')
    print("   or paste the string into the browser address bar")
