from PyQt6.QtCore import Qt
import pyqtgraph as pg

def install_screen_rotate_handle(
    roi:pg.ROI,
    pos:tuple[float, float] =(1.05,0.5),
    center: tuple[float, float] = (0.5,0.5,)
    ):
    """Attach a rotate grip that uses screen-space rotate (not ROI setAngle)

    Expects the ROI to implement _begin_screen_rotate(mouse_scene) and to 
    store state on _rotate_drag"""
    handle = roi.addRotateHandle(list(pos), list(center))

    def mouseDragEvent(ev)->None:
        if ev.button()!=Qt.MouseButton.LeftButton:
            return
        if ev.isStart():
            sp = ev.scenePos()
            roi._begin_screen_rotate((float(sp.x()), float(sp.y())))
            ev.accept()
        elif ev.isFinish():
            roi.rotate_drag = None
            ev.accept()
        else:
            sp = ev.scenePos()
            roi._update_screen_rotate((float(sp.x()), float(sp.y())))
            ev.accept()

    handle.mouseDragEvent = mouseDragEvent
    return handle