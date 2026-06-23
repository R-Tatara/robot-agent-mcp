from mcp.server.fastmcp import FastMCP
from typing import Literal
import json
from pathlib import Path

from melfa_api import RobotController, RcResultCode

IP_ADDR = "192.168.179.105"
PORT_NO = 10002
mcp = FastMCP("robot-mcp-server")

error_database: dict[int, dict] = {}


@mcp.tool()
def open_hand() -> str:
    """Open the hand, or release suction on a suction gripper."""
    rc: RobotController = RobotController(IP_ADDR, PORT_NO)
    try:
        ret = rc.connect()
        if ret != RcResultCode.MR_OK:
            return "Failed to connect."
        
        ret = rc.direct("M_Out(901)=0")
        if ret != RcResultCode.MR_OK:
            return "Failed to open hand."
        
        return "Hand opened successfully."
    finally:
        rc.disconnect()


@mcp.tool()
def close_hand() -> str:
    """Close the hand, or enable suction on a suction gripper."""
    rc: RobotController = RobotController(IP_ADDR, PORT_NO)
    try:
        ret = rc.connect()
        if ret != RcResultCode.MR_OK:
            return "Failed to connect."
        
        ret = rc.direct("M_Out(901)=1")
        if ret != RcResultCode.MR_OK:
            return "Failed to close hand."
        
        return "Hand closed successfully."
    finally:
        rc.disconnect()


@mcp.tool()
def move_to_home() -> str:
    """Move the robot to its home position (preparation position) with the end-effector facing downward."""
    rc: RobotController = RobotController(IP_ADDR, PORT_NO)
    try:
        ret = rc.connect()
        if ret != RcResultCode.MR_OK:
            return "Failed to connect."
        
        ret = rc.set_override(20)
        if ret != RcResultCode.MR_OK:
            return "Failed to set override."

        ret = rc.turn_servo(True)
        if ret != RcResultCode.MR_OK:
            return "Failed to turn on servo."
        
        ret = rc.direct("Jhome=(0,0,90,0,90,0)")
        if ret != RcResultCode.MR_OK:
            return "Failed to set home position."

        ret = rc.direct("Mov Jhome")
        if ret != RcResultCode.MR_OK:
            return "Failed to move to home position."
        
        ret, state = rc.get_slot_state()
        if ret != RcResultCode.MR_OK:
            return "Failed to get slot state."
        if state.err_no != 0:
            return f"Error {state.err_no} occurred during movement."
        
        return "Moved to home position successfully."
    finally:
        rc.turn_servo(False)
        rc.disconnect()


@mcp.tool()
def move_slowly(direction: Literal["上", "下", "左", "右", "前", "後", "奥", "手前"], distance: float) -> str:
    """Move the robot slowly with a relative offset in the given direction.

    Args:
        direction: Move direction ("上" / "下" / "左" / "右" / "前" / "奥" / "後" / "手前").
                   "奥" is an alias for "前", "手前" is an alias for "後".
        distance: Move any distance in millimeters. Must be greater than 0.

    Returns:
        A result message. Returns a failure reason for invalid input,
        connection failure, or motion failure.
    """
    if distance <= 0:
        return "Distance must be greater than 0 mm."

    direction_to_offset = {
        "前": (distance, 0.0, 0.0),
        "奥": (distance, 0.0, 0.0),
        "後": (-distance, 0.0, 0.0),
        "手前": (-distance, 0.0, 0.0),
        "左": (0.0, distance, 0.0),
        "右": (0.0, -distance, 0.0),
        "上": (0.0, 0.0, distance),
        "下": (0.0, 0.0, -distance),
    }
    dx, dy, dz = direction_to_offset[direction]

    rc: RobotController = RobotController(IP_ADDR, PORT_NO)
    try:
        ret = rc.connect()
        if ret != RcResultCode.MR_OK:
            return "Failed to connect."
        
        ret = rc.set_override(20)
        if ret != RcResultCode.MR_OK:
            return "Failed to set override."

        ret = rc.turn_servo(True)
        if ret != RcResultCode.MR_OK:
            return "Failed to turn on servo."
        
        ret = rc.direct(
            f"Mvs P_Curr + ({dx:.1f}, {dy:.1f}, {dz:.1f}, 0.0, 0.0, 0.0)(7, 0)"
        )
        if ret != RcResultCode.MR_OK:
            return f"Failed to move {direction}."

        ret, state = rc.get_slot_state()
        if ret != RcResultCode.MR_OK:
            return "Failed to get slot state."
        if state.err_no != 0:
            return f"Error {state.err_no} occurred during movement."
        
        return f"Moved {direction} by {distance:.1f} mm slowly."
    finally:
        rc.turn_servo(False)
        rc.disconnect()


@mcp.tool()
def rotate_tool_slowly(rotation: Literal["時計回り", "反時計回り"], angle: float) -> str:
    """Rotate the robot tool (J6 axis) slowly by the given angle.

    Args:
        rotation: Rotation direction ("時計回り" / "反時計回り").
        angle: Rotation angle in degrees. Must be greater than 0.

    Returns:
        A result message. Returns a failure reason for invalid input,
        connection failure, or motion failure.
    """
    if angle <= 0:
        return "Angle must be greater than 0 degrees."

    delta = angle if rotation == "反時計回り" else -angle

    rc: RobotController = RobotController(IP_ADDR, PORT_NO)
    try:
        ret = rc.connect()
        if ret != RcResultCode.MR_OK:
            return "Failed to connect."

        ret = rc.set_override(20)
        if ret != RcResultCode.MR_OK:
            return "Failed to set override."

        ret = rc.turn_servo(True)
        if ret != RcResultCode.MR_OK:
            return "Failed to turn on servo."

        ret = rc.direct(
            f"Mvs P_Curr + (0.0, 0.0, 0.0, 0.0, 0.0, {delta:.1f})(7, 0)"
        )
        if ret != RcResultCode.MR_OK:
            return f"Failed to rotate tool {rotation}."

        ret, state = rc.get_slot_state()
        if ret != RcResultCode.MR_OK:
            return "Failed to get slot state."
        if state.err_no != 0:
            return f"Error {state.err_no} occurred during movement."
        
        return f"Rotated tool {rotation} by {angle:.1f} degrees slowly."
    finally:
        rc.turn_servo(False)
        rc.disconnect()


@mcp.tool()
def reset_error() -> str:
    """Reset the robot's error state."""
    rc: RobotController = RobotController(IP_ADDR, PORT_NO)
    try:
        ret = rc.connect()
        if ret != RcResultCode.MR_OK:
            return "Failed to connect."

        ret = rc.reset_error()
        if ret != RcResultCode.MR_OK:
            return "Failed to reset error."
        
        return "Error is reset successfully."
    finally:
        rc.disconnect()


@mcp.tool()
def investigate_robot_error(error_code: int) -> str:
    """Investigate the cause of the robot's error.
    
    Args:
        error_code: 4-digit error code from the robot.
    """
    if error_code in error_database:
        return error_database[error_code]
    else:
        return f"Error code {error_code} not found in database."


def load_json() -> None:
    """Load error codes from trouble_shooting.json into memory."""
    global error_database
    json_path = Path(__file__).parent / "trouble_shooting.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for error in data.get("errors", []):
            code = error.get("code")
            cause = error.get("cause", "")
            measures = error.get("measures", "")
            if code is not None:
                error_database[code] = f"{cause} {measures}".strip()
    except Exception as e:
        print(f"Failed to load error database: {e}")


if __name__ == "__main__":
    load_json()
    mcp.run()
