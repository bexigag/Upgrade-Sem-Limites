import os
from dotenv import load_dotenv


def load_config() -> dict:
    load_dotenv()

    required_keys = [
        "ANTHROPIC_API_KEY",
        "NOTION_TOKEN",
        "NOTION_PARENT_PAGE_ID",
    ]

    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "notion_token": os.getenv("NOTION_TOKEN"),
        "notion_parent_page_id": os.getenv("NOTION_PARENT_PAGE_ID"),
    }
