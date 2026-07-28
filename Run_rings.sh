#!/bin/bash

# Run from the repo root so the relative venv path works from any directory
cd "$(dirname "$0")" || exit 1

# Path to your python script
PYTHON_SCRIPT="ring_sender.py"

# Interpreter from the uv managed venv (create it with: uv sync)
PYTHON_PATH=".venv/bin/python"

# Run the Python script
$PYTHON_PATH $PYTHON_SCRIPT
