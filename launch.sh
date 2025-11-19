#!/bin/bash

# 1. Go to the dir of this script
cd "$(dirname "$0")"

# 2. Activate the venv
# source myenv/bin/activate

# 3. Run FastAPI with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
