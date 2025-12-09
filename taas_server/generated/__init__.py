"""Generated gRPC code package."""

# Fix relative imports in generated files
import sys
from pathlib import Path

# Add the generated directory to the path
generated_dir = Path(__file__).parent
if str(generated_dir) not in sys.path:
    sys.path.insert(0, str(generated_dir))
