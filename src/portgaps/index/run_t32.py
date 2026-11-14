"""Entry point: python -I src/portgaps/index/run_t32.py   (from the repo root)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo/src
from portgaps.index.run_index import main  # noqa: E402

main()
