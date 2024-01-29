from string import Template
import random


def random_color_generator(word: str):
    seed = sum([ord(c) for c in word]) % 32768
    random.seed(seed)
    r = random.randint(20, 235)
    g = random.randint(20, 235)
    b = random.randint(20, 235)

    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b; # per ITU-R BT.709
    text_color = "black" if luma > 160 else "white"
    return f"#{r:02x}{g:02x}{b:02x}", text_color


def create_icon(label: str, width: int = 150):
    icon_color, text_color = random_color_generator(label)
    cx = width / 2
    cy = width / 2
    r = width / 2

    t = Template(
        """

        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="${width}" height="${width}">

            <circle cx="${cx}" cy="${cy}" r="${r}" fill="${icon_color}" />
            <text x="50%" y="50%" 
                alignment-baseline="middle" 
                fill="${text_color}" 
                font-size="150%"
                font-family="monospace"
                font-weight="bold" 
                text-anchor="middle">
                ${label}
            </text>   


             
        </svg>
    """.strip()
    )

    with open("test.svg", "w") as f:
        icon_svg = t.substitute(
            r=r,
            label=label,
            cx=cx,
            cy=cy,
            width=width,
            height=width,
            icon_color=icon_color,
            text_color=text_color,
        )
        f.write(icon_svg)


create_icon("Mistral")
