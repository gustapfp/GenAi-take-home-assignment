from pptx.enum.text import PP_ALIGN

from core.consts import (
    BODY_FONT_COLOR,
    BODY_FONT_NAME,
    BODY_FONT_SIZE,
    TITLE_BOLD,
    TITLE_FONT_COLOR,
    TITLE_FONT_NAME,
    TITLE_FONT_SIZE,
)


def apply_title_style(title_shape):
    """Apply custom styling to the title."""
    if title_shape is None:
        return

    for paragraph in title_shape.text_frame.paragraphs:
        paragraph.font.name = TITLE_FONT_NAME
        paragraph.font.size = TITLE_FONT_SIZE
        paragraph.font.bold = TITLE_BOLD
        paragraph.font.color.rgb = TITLE_FONT_COLOR
        paragraph.alignment = PP_ALIGN.LEFT


def apply_body_style(paragraph, font_size=None):
    """Apply custom styling to body paragraphs."""
    paragraph.font.name = BODY_FONT_NAME
    paragraph.font.size = font_size or BODY_FONT_SIZE
    paragraph.font.color.rgb = BODY_FONT_COLOR
