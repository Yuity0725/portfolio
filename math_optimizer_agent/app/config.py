import os

from dotenv import load_dotenv

load_dotenv()

AVAILABLE_MODELS: list[str] = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]

DEFAULT_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5")
if DEFAULT_MODEL not in AVAILABLE_MODELS:
    AVAILABLE_MODELS.insert(0, DEFAULT_MODEL)

DEFAULT_DAG_PATH: str = os.getenv("DAG_PATH", "data/process_dag.json")
