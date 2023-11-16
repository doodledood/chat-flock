import pathlib
import sys

src_directory = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(src_directory))

project = "ChatFlock"
copyright = "2023, Aviram Kofman"
author = "Aviram Kofman"


def get_version() -> str:
    text = (src_directory / "pyproject.toml").read_text()
    for line in text.splitlines():
        if line.startswith("version = "):
            return line.split("=")[1].strip().strip('"')

    raise ValueError("Could not find version in pyproject.toml")


release = version = get_version()

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "tests"]

master_doc = "index"
html_theme = "sphinx-rtd-theme"
html_static_path = ["_static"]
