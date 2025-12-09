"""Unit tests for the suggested_fps.py script."""

import sys

sys.path.append("./")
from suggested_fps import main


def test_suggested_fps():
    main(max_processes=2, max_fps=20, n_screenshots=100, verbose=False)
