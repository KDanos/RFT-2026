
import qtawesome as qta
from PyQt6.QtGui import QIcon
from pathlib import Path



PRIMARY        = "#1f77b4"   # idle
ACTIVE         = "#0d4f80"   # hover / pressed (a touch darker)
DISABLED_GREY  = "#bbbbbb"

STYLES_DIR = Path(__file__).resolve().parent/"styles"

def app_icon (name:str)->QIcon:
    "Return a QIcon styled with the app's icon palette"
    return qta.icon(
        name,
        color=PRIMARY,
        color_active = ACTIVE,
        color_disabled = DISABLED_GREY
    )

def load_qss(*names:str)->str:
    "Read one or more .qss files from this folder and concatenate them."
    parts = []
    for name in names:
        path = STYLES_DIR/name
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)