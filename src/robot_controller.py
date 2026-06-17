from mcp.server.fastmcp import FastMCP
from typing import Literal

from melfa_api import RobotController, RcResultCode

IP_ADDR = "192.168.179.10"
PORT_NO = 10002
mcp = FastMCP("robot-mcp-server")


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
def move_slowly(direction: Literal["上", "下", "左", "右", "前", "後"], distance: float) -> str:
    """Move the robot slowly with a relative offset in the given direction.

    Args:
        direction: Move direction ("上" / "下" / "左" / "右" / "前" / "後").
        distance: Move distance in millimeters. Must be greater than 0.

    Returns:
        A result message. Returns a failure reason for invalid input,
        connection failure, or motion failure.
    """
    if distance <= 0:
        return "Distance must be greater than 0 mm."

    direction_to_offset = {
        "前": (distance, 0.0, 0.0),
        "後": (-distance, 0.0, 0.0),
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
        
        ret = rc.set_override(10)
        if ret != RcResultCode.MR_OK:
            return "Failed to set override."

        ret = rc.turn_servo(True)
        if ret != RcResultCode.MR_OK:
            return "Failed to turn on servo."
        
        ret = rc.direct(
            f"Mvs P_Curr + ({dx:.1f}, {dy:.1f}, {dz:.1f}, 0.0, 0.0, 0.0)(7, 0)"
            # "Mvs P_Curr+(100,0,0,0,0,0)(7,0)"
            # "Mvs P_Curr+Pdelta"
        )
        if ret != RcResultCode.MR_OK:
            return f"Failed to move {direction}."
        
        return f"Moved {direction} by {distance:.1f} mm slowly."
    finally:
        rc.turn_servo(False)
        rc.disconnect()


if __name__ == "__main__":
    mcp.run()
