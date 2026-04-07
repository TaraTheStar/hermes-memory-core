import os

# Base data directory: honour env var, then Docker path, then local fallback.
_DOCKER_BASE = "/data/hermes_memory_engine"
_LOCAL_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".data")


def _base_dir() -> str:
    explicit = os.environ.get("HERMES_DATA_DIR")
    if explicit:
        return explicit
    if os.path.isdir(_DOCKER_BASE):
        return _DOCKER_BASE
    return _LOCAL_BASE


def default_structural_db() -> str:
    return os.environ.get(
        "HERMES_STRUCTURAL_DB",
        os.path.join(_base_dir(), "structural", "structure.db"),
    )


def default_semantic_dir() -> str:
    return os.environ.get(
        "HERMES_SEMANTIC_DIR",
        os.path.join(_base_dir(), "semantic", "chroma_db"),
    )
