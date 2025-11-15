from .openpose_editor_nodes import OpenposeEditorNode
from .appendage_editor_nodes import AppendageEditorNode
from .pose_filter_nodes import (
    PoseKeypointSelectorNode,
    PoseKeypointFilterNode,
    PoseKeypointMoverNode,
)


WEB_DIRECTORY = "js"

NODE_CLASS_MAPPINGS = {
    "OpenposeEditorNode": OpenposeEditorNode,
    "AppendageEditorNode": AppendageEditorNode,
    "PoseKeypointSelector": PoseKeypointSelectorNode,
    "PoseKeypointFilter": PoseKeypointFilterNode,
    "PoseKeypointMover": PoseKeypointMoverNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OpenposeEditorNode": "Openpose Editor Node",
    "AppendageEditorNode": "Appendage Editor",
    "PoseKeypointSelector": "Pose Keypoint Selector",
    "PoseKeypointFilter": "Pose Keypoint Filter",
    "PoseKeypointMover": "Pose Keypoint Mover",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
