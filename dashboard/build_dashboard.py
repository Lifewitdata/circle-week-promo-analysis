"""Compatibility entry point; regenerate the analysis before drawing charts."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pipeline import main
if __name__ == '__main__':
    main()
