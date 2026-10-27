"""Write the app icons and splash screens into the native projects.

Run from the repository root: python3 scripts/make-icons.py (needs Pillow).
Sources: assets/icon.png (1024², opaque) and assets/icon-foreground.png
(Android adaptive foreground, transparent). See docs/logbook.md.
"""

from pathlib import Path

from PIL import Image, ImageDraw

BACKGROUND = (0x14, 0x0A, 0x2E)
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "android/app/src/main/res"
XCASSETS = ROOT / "ios/App/App/Assets.xcassets"

#: Launcher icon edge in px per density; the adaptive foreground is 108/48 of it.
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}


def flattened(image):
    """Return `image` composited on the background, as RGB (no alpha for Apple)."""
    canvas = Image.new("RGB", image.size, BACKGROUND)
    canvas.paste(image, mask=image.getchannel("A") if image.mode == "RGBA" else None)
    return canvas


def round_icon(adaptive, size):
    """Return the adaptive icon's visible 72/108 centre in a circle, `size` px."""
    edge = adaptive.width * 72 // 108
    offset = (adaptive.width - edge) // 2
    square = adaptive.crop((offset, offset, offset + edge, offset + edge))
    square = square.resize((size * 4, size * 4), Image.LANCZOS)
    mask = Image.new("L", square.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, square.width - 1, square.height - 1), fill=255)
    icon = Image.new("RGBA", square.size, (0, 0, 0, 0))
    icon.paste(square, mask=mask)
    return icon.resize((size, size), Image.LANCZOS)


def splash(size, wordmark, share=3):
    """Return a splash of `size` with the wordmark 1/`share` of the short side wide."""
    canvas = Image.new("RGB", size, BACKGROUND)
    width = min(size) // share
    mark = wordmark.resize(
        (width, round(wordmark.height * width / wordmark.width)), Image.LANCZOS
    )
    canvas.paste(
        mark, ((size[0] - mark.width) // 2, (size[1] - mark.height) // 2), mark
    )
    return canvas


def main():
    icon = flattened(Image.open(ROOT / "assets/icon.png").convert("RGBA"))
    foreground = Image.open(ROOT / "assets/icon-foreground.png").convert("RGBA")
    adaptive = flattened(foreground)
    wordmark = foreground.crop(foreground.getchannel("A").getbbox())

    icon.save(XCASSETS / "AppIcon.appiconset/AppIcon-512@2x.png")

    for density, size in DENSITIES.items():
        folder = RES / f"mipmap-{density}"
        icon.resize((size, size), Image.LANCZOS).save(folder / "ic_launcher.png")
        round_icon(adaptive, size).save(folder / "ic_launcher_round.png")
        edge = size * 108 // 48
        foreground.resize((edge, edge), Image.LANCZOS).save(
            folder / "ic_launcher_foreground.png"
        )

    # Drawn unscaled and centred (launch_splash.xml), so the share is its size on screen.
    for path in RES.glob("drawable*/splash.png"):
        splash(Image.open(path).size, wordmark, share=2).save(path)
    # The iOS square is aspect-filled to the screen height, which enlarges it about 2x.
    for path in (XCASSETS / "Splash.imageset").glob("splash-*.png"):
        splash(Image.open(path).size, wordmark, share=6).save(path)


if __name__ == "__main__":
    main()
