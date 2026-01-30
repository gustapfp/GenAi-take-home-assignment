import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from core.logger_config import logger
from mcp_server.agents.illustrator.agent import IllustratorAgent

# Import your 4 Agents
from mcp_server.agents.planner.agent import PlannerAgent
from mcp_server.agents.planner.schemas import PresentationPayload
from mcp_server.agents.researcher.agent import ResearcherAgent
from mcp_server.agents.researcher.schemas import ResearcherPayload
from mcp_server.agents.writer.agent import WriterAgent

# --- Configuration ---
# Ensure these match your mcp_server.py location
MCP_SERVER_SCRIPT = "mcp_server.py"


async def run_ppt_workflow(topic: str, num_slides: int, filename: str):
    """
    Main Orchestration Function:
    1. Planner -> Creates Outline
    2. Researcher -> Finds Data & Validates Sources
    3. Writer -> Drafts Content + Requests Visuals
    4. Illustrator -> Generates Charts / Downloads Images
    5. Tool -> Assembles Final PPTX
    """
    logger.info(f"\n🎬 STARTING WORKFLOW: '{topic}' ({num_slides} slides)")

    # 1. Start MCP Server Connection
    server_params = StdioServerParameters(
        command="python",
        args=[MCP_SERVER_SCRIPT],
        env=os.environ.copy(),  # Pass API keys (OpenAI, Tavily) to server
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Verify Tools
            tools = await session.list_tools()
            logger.info(f"MCP Connected. Tools: {[t.name for t in tools.tools]}")

            # --- Initialize Agents ---
            planner = PlannerAgent()
            researcher = ResearcherAgent()
            writer = WriterAgent()
            illustrator = IllustratorAgent()

            # --- STEP 1: PLANNER ---
            # "Blueprints the presentation structure"
            logger.info("Step 1: Planning the presentation structure...")
            plan = await planner.create_presentation_plan(
                payload=PresentationPayload(topic=topic, num_slides=num_slides)
            )
            logger.info(f"Presentation plan created with {len(plan.slides)} slides.")
            logger.info(f"Presentation plan: {plan.model_dump_json()}")
            # --- STEP 2: RESEARCHER ---
            # "Gathers verified facts for each slide"
            logger.info("Step 2: Researching the web for information...")
            research_data = []
            for slide in plan.slides:
                # The Researcher uses the MCP session to call 'search_web'
                summary = await researcher.research_web(
                    payload=ResearcherPayload(
                        slide_title=slide.title, search_queries=slide.search_queries
                    ),
                    session=session,
                )
                research_data.append(summary.model_dump())
            logger.info(
                f"Research completed successfully. Research data: {json.dumps(research_data, indent=2, ensure_ascii=False)}"
            )

            # --- STEP 3: WRITER ---
            # "Synthesizes text and decides on visuals"
            logger.info("Step 3: Writing & Designing the presentation...")
            deck_content = await writer.prepare_presentation(
                topic=topic, plan_json=plan.model_dump(), research_data=research_data
            )

            # --- STEP 4: ILLUSTRATOR ---
            # "Fulfills the visual requests from the Writer"
            logger.info("\n🔹 Step 4: Illustrating...")

            # Extract requests from Writer's output
            visual_requests = []
            for i, slide in enumerate(deck_content.slides):
                if slide.visual_request:
                    req = slide.visual_request.model_dump()
                    req["slide_number"] = i  # Track which slide this belongs to
                    visual_requests.append(req)

            # Illustrator uses MCP tools (generate_chart, get_stock_image)
            illustration_result = await illustrator.create_visuals(visual_requests, session)

            # Helper to convert Pydantic models to dicts for the Writer
            generated_assets = [asset.model_dump() for asset in illustration_result.assets]
            # --- STEP 5: ASSEMBLY (MCP Tool) ---
            # Merge text and image paths into the final JSON for the tool
            logger.info("\n🔹 Step 5: Assembling Final File...")

            final_slides_payload = []
            for i, slide in enumerate(deck_content.slides):
                slide_data = {
                    "title": slide.title,
                    "points": slide.points,
                    "image": None,  # Default
                }

                # Check if Illustrator provided an asset for this slide
                matching_asset = next(
                    (a for a in illustration_result.assets if a.slide_number == i), None
                )
                if matching_asset:
                    slide_data["image"] = matching_asset.file_path

                final_slides_payload.append(slide_data)

            # Call the 'create_presentation' tool
            await writer.write_presentation(
                content=deck_content,
                session=session,
                generated_assets=generated_assets,
                filename=filename,
            )

            final_filename = f"{deck_content.filename_suggestion}.pptx"
            print(f"\n✅ DONE! Presentation saved as: output/{final_filename}")
            return final_filename


# --- Entry Point (for testing workflow independently) ---
if __name__ == "__main__":
    # Ensure keys are set before running!
    # os.environ["OPENAI_API_KEY"] = "..."
    # os.environ["TAVILY_API_KEY"] = "..."

    try:
        asyncio.run(run_ppt_workflow("The Future of AI Agents in 2025", 3, "test-presentation"))
    except KeyboardInterrupt:
        logger.info("\nWorkflow stopped by user.")
