from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

FILE_PATH = Path(__file__).resolve().parent.parent.parent / "concluded_presentations"


DOMAIN_BLACKLIST = [
    "reddit.com",
    "quora.com",
    "twitter.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "tiktok.com",
    "linkedin.com",
]

TITLE_FONT_NAME = "Calibri"
TITLE_FONT_SIZE = Pt(36)
TITLE_FONT_COLOR = RGBColor(0, 51, 102)
TITLE_BOLD = True

BODY_FONT_NAME = "Calibri"
BODY_FONT_SIZE = Pt(18)
BODY_FONT_SIZE_WITH_IMAGE = Pt(14)
BODY_FONT_COLOR = RGBColor(51, 51, 51)
BODY_LINE_SPACING = Pt(8)

SLIDE_WIDTH = Inches(10)
SLIDE_HEIGHT = Inches(7.5)

IMAGE_HEIGHT = Inches(4.0)

BODY_WIDTH_WITH_IMAGE = Inches(4.5)
