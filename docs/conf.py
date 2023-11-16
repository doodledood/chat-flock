import pathlib
import sys

from chatflock import get_version

src_directory = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(src_directory))

project = "chat-flock"
copyright = "2023- Aviram Kofman"
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
