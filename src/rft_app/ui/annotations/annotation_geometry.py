from dataclasses import dataclass
import math
import pyqtgraph as pg


@dataclass
class RotateDragState:
    """Snapshot at rotate_handle press (all geometry in scene/pixel space)."""
    center_scene:tuple[float, float]
    start_angle_rad: float
    corners_scene:list[tuple[float, float]]

def view_point_to_scene (vb, x:float, y:float)->tuple[float, float]:
    """ Converts a point from view cordinates to scene cordinates"""
    p = vb.mapViewToScene(pg.Point(x,y))
    return float(p.x()), float(p.y())

def capture_rotate_drag_start(
    vb, 
    corners_view:list[tuple[float, float]],
    mouse_scene:tuple[float, float],
    )->RotateDragState:
    """Build a rotate state from view-space corners and and current mouse"""
    #Convert the corners from view to scene cordinates
    corners_scene = [view_point_to_scene(vb, x,y) for x,y in corners_view]
    
    #Identify the central location of the shape in scene cordinates
    cx = sum(pt[0] for pt in corners_scene)/len(corners_scene)
    cy = sum(pt[1] for pt in corners_scene)/len(corners_scene)
    
    mx, my = mouse_scene
    start_angle = math.atan2(my-cy, mx-cx)
    
    return RotateDragState(
        center_scene = (cx,cy) ,
        start_angle_rad=start_angle,
        corners_scene=corners_scene
    )

def axis_aligned_rect_corner_view(
    pos: tuple[float, float], 
    size: tuple[float, float]
    )->list[tuple[float, float]]:
    """Four corners in view coordinates:
    top-left, top-right, bottom-right, bottom-left"""
    x0 , y0 = pos
    w, h = size
    return [
        (x0,y0),(x0+w, y0),(x0+w, y0+h),(x0, y0+h)
    ]

def rotate_corners_scene(
    state:RotateDragState, 
    mouse_scene:tuple[float, float]
    )->list[tuple[float,float]]:
    """Rotate the snapshotted scene corners by the mouse angle delta since press."""
    mx, my = mouse_scene
    cx, cy= state.center_scene
    angle_now = math.atan2(my-cy, mx-cx)
    delta = angle_now-state.start_angle_rad
    cos_d = math.cos(delta)
    sin_d = math.sin(delta)

    result:list[tuple[float, float]]=[]
    for x,y in state.corners_scene:
        dx = x-cx
        dy = y-cy
        result.append(
            (
                cx+dx*cos_d -dy*sin_d,
                cy+dx*sin_d+dy*cos_d
            )
            )
    return result

def scene_point_to_view(vb, x:float, y:float)->tuple[float,float]:
    """Convert a point from scene coordindates to view coordinates"""
    p = vb.mapSceneToView(pg.Point(x,y))
    return float(p.x()), float(p.y())