import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app import app

# Vercel handler
def handler(request):
    return app(request)