import pathlib
import sys

src_directory = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(src_directory))

project = "chat-flock"
copyright = "2023- Aviram Kofman"


def get_version() -> str:
    text = (src_directory / "pyproject.toml").read_text()
    for line in text.splitlines():
        if line.startswith("version = "):
            return line.split("=")[1].strip().strip('"')

    raise ValueError("Could not find version in pyproject.toml")


release = version = get_version()

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
]
exclude_patterns = ["htmlcov", "assets"]
master_doc = "index"
html_theme = "classic"
