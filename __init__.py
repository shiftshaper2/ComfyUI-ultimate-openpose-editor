from .openpose_editor_nodes import OpenposeEditorNode
from .appendage_editor_nodes import AppendageEditorNode
from .pose_filter_nodes import (
    PoseKeypointSelectorNode,
    PoseKeypointFilterNode,
    PoseKeypointMoverNode,
)
from .pose_merge_node import PoseMergeNode
from .pose_attach_node import PoseAttachNode


WEB_DIRECTORY = "js"

NODE_CLASS_MAPPINGS = {
    "OpenposeEditorNode": OpenposeEditorNode,
    "AppendageEditorNode": AppendageEditorNode,
    "PoseKeypointSelector": PoseKeypointSelectorNode,
    "PoseKeypointFilter": PoseKeypointFilterNode,
    "PoseKeypointMover": PoseKeypointMoverNode,
    "PoseMerge": PoseMergeNode,
    "PoseAttach": PoseAttachNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OpenposeEditorNode": "Openpose Editor Node",
    "AppendageEditorNode": "Appendage Editor",
    "PoseKeypointSelector": "Pose Keypoint Selector",
    "PoseKeypointFilter": "Pose Keypoint Filter",
    "PoseKeypointMover": "Pose Keypoint Mover",
    "PoseMerge": "Pose Merge",
    "PoseAttach": "Pose Attach",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
