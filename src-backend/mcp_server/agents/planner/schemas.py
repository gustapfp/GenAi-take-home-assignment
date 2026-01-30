from pydantic import BaseModel, Field


class SlidePlan(BaseModel):
    slide_number: int
    title: str = Field(description="The main title of the slide")
    search_queries: list[str] = Field(
        description="Specific search queries for the Researcher to find facts for this slide"
    )
    content_goal: str = Field(description="A brief instruction on what this slide should cover")


class PresentationPlan(BaseModel):
    topic: str
    slides: list[SlidePlan]


class PresentationPayload(BaseModel):
    topic: str
    num_slides: int
