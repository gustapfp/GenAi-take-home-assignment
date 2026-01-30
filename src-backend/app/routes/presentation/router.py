import asyncio
import json
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import ValidationError

from app.routes.presentation.schemas import (
    PresentationDownloadResponse,
    PresentationRequest,
    PresentationResponse,
)
from app.routes.presentation.utils import generate_pprt_id
from core.consts import FILE_PATH
from core.logger_config import logger
from mcp_server.workflow import run_ppt_workflow

presentation_router = APIRouter(
    prefix="/presentation",
    tags=["presentation"],
)


@presentation_router.post("/generate_ppt", status_code=202)
async def generate_ppt(
    request: PresentationRequest, background_tasks: BackgroundTasks
) -> PresentationResponse:
    """
    Generate a PowerPoint presentation based on the given topic and number of slides. The endpoint accepts a topic
    and triggers

    Args:
        request: PresentationRequest - The request containing the topic and number of slides.

    Returns:
        PresentationResponse - The response containing the message, status, and presentation ID.
    """
    pprt_id = generate_pprt_id(request.topic)
    logger.info(
        f"Generating presentation: topic='{request.topic}', slides={request.slides}, pprt_id={pprt_id}"
    )
    try:
        background_tasks.add_task(
            run_ppt_workflow, topic=request.topic, num_slides=request.slides, filename=pprt_id
        )
        return PresentationResponse(
            message="Presentation generation task created successfully! To retrieve the presentation, please use the pprt_id in the response.",
            status="Success",
            pprt_id=pprt_id,
        )
    except ValidationError as e:
        logger.error(f"Validation error for pprt_id={pprt_id}: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: Invalid request parameters. Please check the request and try again. Error: {e.errors()}",
        ) from e
    except Exception as e:
        logger.error(f"Error generating presentation for pprt_id={pprt_id}: {e}")
        return PresentationResponse(
            message=f"Error generating presentation: {e}",
            status="Error",
        )


@presentation_router.get("/download/{pprt_id}", response_model=None)
async def download_ppt(pprt_id: str) -> FileResponse | PresentationDownloadResponse:
    """Download the PowerPoint presentation based on the given presentation ID.

    Args:
        pprt_id (str): The presentation ID.

    Returns:
        FileResponse | PresentationDownloadResponse: The file response or the presentation response with the status "Pending" if the presentation is not found.
    """
    if os.path.exists(f"{FILE_PATH}/{pprt_id}.pptx"):
        return FileResponse(
            path=f"{FILE_PATH}/{pprt_id}.pptx",
            filename=f"{pprt_id}.pptx",
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
    else:
        return PresentationDownloadResponse(
            message="Presentation not found. Please check the presentation ID and try again in a few minutes.",
            status="Pending",
        )


@presentation_router.get("/status/{pprt_id}")
async def presentation_status(pprt_id: str) -> StreamingResponse:
    """Stream the status of the presentation generation using Server-Sent Events (SSE).

    The client connects to this endpoint and receives real-time updates when the
    presentation is ready for download.

    Args:
        pprt_id (str): The presentation ID to monitor.

    Returns:
        StreamingResponse: SSE stream with status updates.
    """
    file_path = str(FILE_PATH / f"{pprt_id}.pptx")
    logger.info(f"SSE: Starting status stream for pprt_id={pprt_id}, checking file: {file_path}")

    async def event_stream():
        max_wait_time = 1200  # 20 minutes timeout
        elapsed = 0
        interval = 30  # Check every 30 seconds

        while elapsed < max_wait_time:
            if os.path.exists(file_path):
                logger.info(f"SSE: File ready for pprt_id={pprt_id}")
                yield f"data: {json.dumps({'status': 'ready', 'pprt_id': pprt_id})}\n\n"
                return
            yield f"data: {json.dumps({'status': 'processing', 'elapsed': elapsed})}\n\n"
            await asyncio.sleep(interval)
            elapsed += interval

        # Timeout reached
        logger.warning(f"SSE: Timeout waiting for pprt_id={pprt_id}")
        yield f"data: {json.dumps({'status': 'timeout', 'message': 'Generation timed out'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
