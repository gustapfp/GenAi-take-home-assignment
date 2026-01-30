from pydantic import BaseModel, Field


class SlideContent(BaseModel):
    title: str = Field(description="The final title for the slide")
    points: list[str] = Field(description="3-5 bullet points summarizing the research")
    speaker_notes: str | None = Field(description="Brief notes for the presenter to say")


class VisualRequest(BaseModel):
    type: str = Field(description="'chart' if you have numerical data, 'image' for concepts")
    prompt: str = Field(description="Title of the chart OR search query for the image")
    data_json: str | None = Field(
        description="JSON string {'labels':[], 'values':[]} ONLY for charts"
    )


class PresentationContent(BaseModel):
    filename_suggestion: str = Field(
        description="A clean, underscore-separated filename (e.g., 'ai_trends_2026')"
    )
    slides: list[SlideContent]
    visual_request: VisualRequest | None = None
