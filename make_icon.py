from string import Template
import random, sys


def random_color_generator(word: str):
    seed = sum([ord(c) for c in word]) % 32768
    random.seed(seed)
    r = random.randint(10, 245)
    g = random.randint(10, 245)
    b = random.randint(10, 245)

    text_color = "black" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.5 else "white"

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


if __name__ == "__main__":
    create_icon(sys.argv[1])
