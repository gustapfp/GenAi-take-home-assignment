import re
import uuid


def generate_pprt_id(topic: str) -> str:
    """Generate a unique presentation ID based on the topic.

    Args:
        topic (str): The topic of the presentation.

    Returns:
        str: The unique presentation ID.
    """
    clean_topic = re.sub(r"[^a-zA-Z0-9_\-]", "", topic.replace(" ", "_"))
    return f"{clean_topic}-{uuid.uuid4()}"
