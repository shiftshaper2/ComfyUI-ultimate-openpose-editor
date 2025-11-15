"""
Node for merging multiple pose datasets together.

Combines people from multiple POSE_KEYPOINT inputs into a single pose dataset.
"""

import copy


class PoseMergeNode:
    """
    Merge multiple pose datasets by combining their people lists.
    Useful for compositing multiple poses into a single scene.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "POSE_KEYPOINT_1": ("POSE_KEYPOINT",),
            },
            "optional": {
                "POSE_KEYPOINT_2": ("POSE_KEYPOINT",),
                "POSE_KEYPOINT_3": ("POSE_KEYPOINT",),
                "POSE_KEYPOINT_4": ("POSE_KEYPOINT",),
                "POSE_KEYPOINT_5": ("POSE_KEYPOINT",),
                "canvas_width": ("INT", {"default": 512, "min": 64, "max": 8192,
                                        "tooltip": "Canvas width for merged pose"}),
                "canvas_height": ("INT", {"default": 768, "min": 64, "max": 8192,
                                         "tooltip": "Canvas height for merged pose"}),
            },
        }

    RETURN_NAMES = ("POSE_KEYPOINT",)
    RETURN_TYPES = ("POSE_KEYPOINT",)
    FUNCTION = "merge_poses"
    CATEGORY = "ultimate-openpose"

    def merge_poses(self, POSE_KEYPOINT_1, POSE_KEYPOINT_2=None, POSE_KEYPOINT_3=None,
                   POSE_KEYPOINT_4=None, POSE_KEYPOINT_5=None,
                   canvas_width=512, canvas_height=768):
        """
        Merge multiple pose datasets by combining people from each.

        Args:
            POSE_KEYPOINT_1: First pose (required)
            POSE_KEYPOINT_2-5: Additional poses (optional)
            canvas_width: Width of output canvas
            canvas_height: Height of output canvas

        Returns:
            Merged pose dataset with all people combined
        """
        # Collect all non-None pose inputs
        pose_inputs = [POSE_KEYPOINT_1]
        for pose in [POSE_KEYPOINT_2, POSE_KEYPOINT_3, POSE_KEYPOINT_4, POSE_KEYPOINT_5]:
            if pose is not None:
                pose_inputs.append(pose)

        # Determine output length (max frames across all inputs)
        max_frames = max(len(pose) if isinstance(pose, list) else 1 for pose in pose_inputs)

        # Normalize all inputs to lists
        normalized_poses = []
        for pose in pose_inputs:
            if not isinstance(pose, list):
                normalized_poses.append([pose])
            else:
                normalized_poses.append(pose)

        # Merge frame by frame
        output_poses = []
        for frame_idx in range(max_frames):
            merged_frame = {
                "people": [],
                "canvas_width": canvas_width,
                "canvas_height": canvas_height
            }

            # Collect people from each pose input for this frame
            for pose_list in normalized_poses:
                # Loop/repeat behavior: use last frame if we run out
                source_frame_idx = min(frame_idx, len(pose_list) - 1)
                source_frame = pose_list[source_frame_idx]

                if isinstance(source_frame, dict) and 'people' in source_frame:
                    # Deep copy people to avoid reference issues
                    for person in source_frame['people']:
                        merged_frame['people'].append(copy.deepcopy(person))

            output_poses.append(merged_frame)

        return (output_poses,)


# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "PoseMerge": PoseMergeNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseMerge": "Pose Merge",
}
