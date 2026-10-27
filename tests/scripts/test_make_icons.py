"""Tests for scripts/make-icons.py, on images in a temporary tree."""

from PIL import Image

BACKGROUND = (0x14, 0x0A, 0x2E)
WHITE = (255, 255, 255, 255)


def _wordmark(size=(200, 200)):
    """A transparent square with an opaque white block in the middle."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    image.paste(WHITE, (size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4))
    return image


def test_flattened_puts_transparency_on_the_background(make_icons):
    flat = make_icons.flattened(_wordmark())

    assert flat.mode == "RGB"
    assert flat.getpixel((0, 0)) == BACKGROUND
    assert flat.getpixel((100, 100)) == (255, 255, 255)


def test_flattened_keeps_an_opaque_image(make_icons):
    flat = make_icons.flattened(Image.new("RGB", (4, 4), (1, 2, 3)))

    assert flat.getpixel((0, 0)) == (1, 2, 3)


def test_round_icon_is_a_circle_of_the_visible_centre(make_icons):
    icon = make_icons.round_icon(make_icons.flattened(_wordmark((216, 216))), 48)

    assert icon.size == (48, 48)
    assert icon.getpixel((0, 0))[3] == 0
    assert icon.getpixel((24, 24)) == WHITE


def test_splash_centres_the_wordmark_at_its_share(make_icons):
    mark = _wordmark((100, 50)).crop((25, 12, 75, 38))
    image = make_icons.splash((600, 300), mark, share=3)

    assert image.size == (600, 300)
    assert image.getpixel((0, 0)) == BACKGROUND
    assert image.getpixel((300, 150)) == (255, 255, 255)
    assert image.getpixel((300 - 51, 150)) == BACKGROUND


def test_main_writes_every_icon_and_splash(make_icons, tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    Image.new("RGBA", (1024, 1024), (19, 216, 216, 255)).save(tmp_path / "assets/icon.png")
    _wordmark((432, 432)).save(tmp_path / "assets/icon-foreground.png")
    res = tmp_path / "res"
    xcassets = tmp_path / "Assets.xcassets"
    for density in make_icons.DENSITIES:
        (res / f"mipmap-{density}").mkdir(parents=True)
    for folder in ("drawable", "drawable-land-hdpi"):
        (res / folder).mkdir()
        Image.new("RGB", (320, 480)).save(res / folder / "splash.png")
    (xcassets / "AppIcon.appiconset").mkdir(parents=True)
    (xcassets / "Splash.imageset").mkdir()
    Image.new("RGB", (900, 900)).save(xcassets / "Splash.imageset/splash-2732x2732.png")
    monkeypatch.setattr(make_icons, "ROOT", tmp_path)
    monkeypatch.setattr(make_icons, "RES", res)
    monkeypatch.setattr(make_icons, "XCASSETS", xcassets)

    make_icons.main()

    store = Image.open(xcassets / "AppIcon.appiconset/AppIcon-512@2x.png")
    assert (store.size, store.mode) == ((1024, 1024), "RGB")
    for density, size in make_icons.DENSITIES.items():
        folder = res / f"mipmap-{density}"
        assert Image.open(folder / "ic_launcher.png").size == (size, size)
        assert Image.open(folder / "ic_launcher_round.png").size == (size, size)
        edge = size * 108 // 48
        assert Image.open(folder / "ic_launcher_foreground.png").size == (edge, edge)
    for path in res.glob("drawable*/splash.png"):
        splash = Image.open(path)
        assert splash.size == (320, 480)
        assert splash.getpixel((160, 240)) == (255, 255, 255)
        # Half the short side: the 160 px wordmark spans x 80-240.
        assert splash.getpixel((82, 240)) == (255, 255, 255)
        assert splash.getpixel((77, 240)) == BACKGROUND
    ios = Image.open(xcassets / "Splash.imageset/splash-2732x2732.png")
    assert ios.getpixel((0, 0)) == BACKGROUND
