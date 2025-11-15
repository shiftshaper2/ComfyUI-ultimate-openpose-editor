"""
Nodes for filtering and manipulating specific keypoints in OpenPose data.

Provides three nodes:
1. PoseKeypointSelectorNode - Define which keypoints to work with
2. PoseKeypointFilterNode - Zero out confidence for non-selected keypoints
3. PoseKeypointMoverNode - Move selected keypoints by x/y offsets
"""

import copy
from .body_part_definitions import BODY_PART_GROUPS, get_all_part_names


class PoseKeypointSelectorNode:
    """
    Create a selection of keypoints without requiring pose data input.
    Outputs a POSE_SELECTION that can be used by filter and mover nodes.
    """

    @classmethod
    def INPUT_TYPES(s):
        part_names = get_all_part_names()
        return {
            "required": {
                "selection_type": (["custom"] + part_names, {"default": "all"}),
            },
            "optional": {
                # Individual checkboxes for custom selection
                "include_head": ("BOOLEAN", {"default": True}),
                "include_neck": ("BOOLEAN", {"default": True}),
                "include_torso": ("BOOLEAN", {"default": True}),
                "include_left_arm": ("BOOLEAN", {"default": True}),
                "include_right_arm": ("BOOLEAN", {"default": True}),
                "include_left_leg": ("BOOLEAN", {"default": True}),
                "include_right_leg": ("BOOLEAN", {"default": True}),
                "include_left_hand": ("BOOLEAN", {"default": True}),
                "include_right_hand": ("BOOLEAN", {"default": True}),
                "include_face": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_NAMES = ("POSE_SELECTION",)
    RETURN_TYPES = ("POSE_SELECTION",)
    FUNCTION = "create_selection"
    CATEGORY = "ultimate-openpose"

    def create_selection(self, selection_type, **kwargs):
        """
        Create a pose selection based on type or custom checkboxes.

        Returns:
            Dictionary with:
                - body_indices: List of body keypoint indices to include
                - include_face: Whether to include face keypoints
                - include_left_hand: Whether to include left hand
                - include_right_hand: Whether to include right hand
        """
        selection = {
            "body_indices": [],
            "include_face": kwargs.get("include_face", True),
            "include_left_hand": kwargs.get("include_left_hand", True),
            "include_right_hand": kwargs.get("include_right_hand", True),
        }

        if selection_type == "custom":
            # Build from individual checkboxes
            indices = set()

            if kwargs.get("include_head", True):
                indices.update(BODY_PART_GROUPS["head"])

            if kwargs.get("include_neck", True):
                indices.add(1)  # Neck

            if kwargs.get("include_torso", True):
                indices.update(BODY_PART_GROUPS["torso"])

            if kwargs.get("include_left_arm", True):
                indices.update(BODY_PART_GROUPS["left_full_arm"])

            if kwargs.get("include_right_arm", True):
                indices.update(BODY_PART_GROUPS["right_full_arm"])

            if kwargs.get("include_left_leg", True):
                indices.update(BODY_PART_GROUPS["left_full_leg"])

            if kwargs.get("include_right_leg", True):
                indices.update(BODY_PART_GROUPS["right_full_leg"])

            selection["body_indices"] = sorted(list(indices))

        else:
            # Use preset from BODY_PART_GROUPS
            selection["body_indices"] = BODY_PART_GROUPS.get(selection_type, list(range(18)))

            # For preset types, default to including hands/face unless they conflict
            # with the selection (e.g., "lower_body" shouldn't include face)
            if selection_type in ["lower_body", "legs", "left_full_leg", "right_full_leg",
                                 "left_foot", "right_foot"]:
                selection["include_face"] = False

        return (selection,)


class PoseKeypointFilterNode:
    """
    Filter pose keypoints by zeroing confidence values for non-selected keypoints.
    This makes them invisible in renders while keeping the data structure intact.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "POSE_KEYPOINT": ("POSE_KEYPOINT",),
                "POSE_SELECTION": ("POSE_SELECTION",),
            },
            "optional": {
                "person_index": ("INT", {"default": -1, "min": -1, "max": 100,
                                        "tooltip": "Which person to filter (-1 for all)"}),
                "invert_selection": ("BOOLEAN", {"default": False,
                                                "tooltip": "If true, hide selected keypoints instead"}),
            },
        }

    RETURN_NAMES = ("POSE_KEYPOINT",)
    RETURN_TYPES = ("POSE_KEYPOINT",)
    FUNCTION = "filter_pose"
    CATEGORY = "ultimate-openpose"

    def filter_pose(self, POSE_KEYPOINT, POSE_SELECTION, person_index=-1, invert_selection=False):
        """
        Zero out confidence for keypoints not in selection.

        Args:
            POSE_KEYPOINT: Input pose data
            POSE_SELECTION: Selection dict from PoseKeypointSelectorNode
            person_index: Which person to filter (-1 for all)
            invert_selection: If True, hide selected keypoints instead

        Returns:
            Modified pose data with confidence zeroed for filtered keypoints
        """
        pose_data = copy.deepcopy(POSE_KEYPOINT)
        body_indices = set(POSE_SELECTION.get("body_indices", []))

        for frame in pose_data:
            if 'people' not in frame:
                continue

            people_to_edit = (range(len(frame['people'])) if person_index == -1
                            else [person_index])

            for person_idx in people_to_edit:
                if person_idx >= len(frame['people']):
                    continue

                person = frame['people'][person_idx]

                # Filter body keypoints
                if 'pose_keypoints_2d' in person:
                    person['pose_keypoints_2d'] = self._filter_keypoints(
                        person['pose_keypoints_2d'],
                        body_indices,
                        invert_selection
                    )

                # Filter hands and face based on selection
                if not POSE_SELECTION.get('include_left_hand', True) != invert_selection:
                    if 'hand_left_keypoints_2d' in person:
                        person['hand_left_keypoints_2d'] = self._zero_all_keypoints(
                            person['hand_left_keypoints_2d']
                        )

                if not POSE_SELECTION.get('include_right_hand', True) != invert_selection:
                    if 'hand_right_keypoints_2d' in person:
                        person['hand_right_keypoints_2d'] = self._zero_all_keypoints(
                            person['hand_right_keypoints_2d']
                        )

                if not POSE_SELECTION.get('include_face', True) != invert_selection:
                    if 'face_keypoints_2d' in person:
                        person['face_keypoints_2d'] = self._zero_all_keypoints(
                            person['face_keypoints_2d']
                        )

        return (pose_data,)

    def _filter_keypoints(self, keypoints, keep_indices, invert):
        """
        Zero out confidence for keypoints not in keep_indices.

        Args:
            keypoints: Flat array of [x, y, confidence] triplets
            keep_indices: Set of keypoint indices to keep
            invert: If True, zero out keypoints IN keep_indices instead

        Returns:
            Modified keypoints array
        """
        if keypoints is None:
            return None

        filtered = keypoints.copy()
        for i in range(0, len(filtered), 3):
            keypoint_idx = i // 3
            should_keep = keypoint_idx in keep_indices

            if invert:
                should_keep = not should_keep

            if not should_keep:
                filtered[i + 2] = 0  # Zero out confidence

        return filtered

    def _zero_all_keypoints(self, keypoints):
        """Zero out confidence for all keypoints in array."""
        if keypoints is None:
            return None

        result = keypoints.copy()
        for i in range(2, len(result), 3):
            result[i] = 0
        return result


class PoseKeypointMoverNode:
    """
    Move selected keypoints by x/y offsets.
    Unselected keypoints remain in their original positions.
    """

    @classmethod
    def INPUT_TYPES(s):
        part_names = get_all_part_names()
        return {
            "required": {
                "POSE_KEYPOINT": ("POSE_KEYPOINT",),
                "x_offset": ("FLOAT", {"default": 0.0, "min": -10000.0, "max": 10000.0, "step": 1.0,
                                      "tooltip": "X offset in pixels (can be list for animation)"}),
                "y_offset": ("FLOAT", {"default": 0.0, "min": -10000.0, "max": 10000.0, "step": 1.0,
                                      "tooltip": "Y offset in pixels (can be list for animation)"}),
            },
            "optional": {
                "POSE_SELECTION": ("POSE_SELECTION", {"tooltip": "Selection from PoseKeypointSelector (takes priority)"}),
                "appendage_type": (part_names, {"default": "all",
                                               "tooltip": "Body part to move (fallback if no POSE_SELECTION)"}),
                "person_index": ("INT", {"default": -1, "min": -1, "max": 100,
                                        "tooltip": "Which person to move (-1 for all)"}),
                "list_mismatch_behavior": (["truncate", "loop", "repeat"], {"default": "loop",
                                           "tooltip": "How to handle mismatched list lengths"}),
                "affect_hands": ("BOOLEAN", {"default": False,
                                            "tooltip": "Move hands when wrists are selected"}),
                "affect_face": ("BOOLEAN", {"default": False,
                                           "tooltip": "Move face when head is selected"}),
            },
        }

    RETURN_NAMES = ("POSE_KEYPOINT",)
    RETURN_TYPES = ("POSE_KEYPOINT",)
    FUNCTION = "move_keypoints"
    CATEGORY = "ultimate-openpose"

    def move_keypoints(self, POSE_KEYPOINT, x_offset, y_offset,
                      POSE_SELECTION=None, appendage_type="all",
                      person_index=-1, list_mismatch_behavior="loop",
                      affect_hands=False, affect_face=False):
        """
        Move selected keypoints by x/y offsets.

        Args:
            POSE_KEYPOINT: Input pose data
            x_offset: X offset (float or list)
            y_offset: Y offset (float or list)
            POSE_SELECTION: Optional selection (takes priority over appendage_type)
            appendage_type: Body part to move (fallback)
            person_index: Which person to move (-1 for all)
            list_mismatch_behavior: How to handle list length mismatches
            affect_hands: Move hands when wrists are in selection
            affect_face: Move face when head is in selection

        Returns:
            Modified pose data with selected keypoints moved
        """
        pose_data = copy.deepcopy(POSE_KEYPOINT)

        # Normalize offsets to lists for animation support
        x_offset_list = self._normalize_to_list(x_offset, len(pose_data), list_mismatch_behavior)
        y_offset_list = self._normalize_to_list(y_offset, len(pose_data), list_mismatch_behavior)

        # Determine which keypoints to move
        if POSE_SELECTION is not None:
            body_indices = set(POSE_SELECTION.get("body_indices", []))
            move_left_hand = POSE_SELECTION.get("include_left_hand", False) or (affect_hands and 7 in body_indices)
            move_right_hand = POSE_SELECTION.get("include_right_hand", False) or (affect_hands and 4 in body_indices)
            move_face = POSE_SELECTION.get("include_face", False) or (affect_face and any(i in body_indices for i in [0, 14, 15, 16, 17]))
        else:
            body_indices = set(BODY_PART_GROUPS.get(appendage_type, list(range(18))))
            move_left_hand = affect_hands and 7 in body_indices
            move_right_hand = affect_hands and 4 in body_indices
            move_face = affect_face and any(i in body_indices for i in [0, 14, 15, 16, 17])

        # Apply movements frame by frame
        for frame_idx, frame in enumerate(pose_data):
            if 'people' not in frame:
                continue

            current_x = x_offset_list[frame_idx]
            current_y = y_offset_list[frame_idx]

            people_to_edit = (range(len(frame['people'])) if person_index == -1
                            else [person_index])

            for person_idx in people_to_edit:
                if person_idx >= len(frame['people']):
                    continue

                person = frame['people'][person_idx]

                # Move body keypoints
                if 'pose_keypoints_2d' in person:
                    person['pose_keypoints_2d'] = self._apply_offset(
                        person['pose_keypoints_2d'],
                        body_indices,
                        current_x,
                        current_y
                    )

                # Move hands if specified
                if move_left_hand and 'hand_left_keypoints_2d' in person:
                    person['hand_left_keypoints_2d'] = self._apply_offset_all(
                        person['hand_left_keypoints_2d'], current_x, current_y
                    )

                if move_right_hand and 'hand_right_keypoints_2d' in person:
                    person['hand_right_keypoints_2d'] = self._apply_offset_all(
                        person['hand_right_keypoints_2d'], current_x, current_y
                    )

                # Move face if specified
                if move_face and 'face_keypoints_2d' in person:
                    person['face_keypoints_2d'] = self._apply_offset_all(
                        person['face_keypoints_2d'], current_x, current_y
                    )

        return (pose_data,)

    def _normalize_to_list(self, value, target_length, behavior):
        """
        Normalize a value or list to match target length.

        Args:
            value: Single value or list
            target_length: Desired list length
            behavior: "truncate", "loop", or "repeat"

        Returns:
            List of specified length
        """
        if not isinstance(value, list):
            return [value] * target_length

        if len(value) == target_length:
            return value

        if behavior == "truncate":
            return value[:target_length]
        elif behavior == "loop":
            result = []
            for i in range(target_length):
                result.append(value[i % len(value)])
            return result
        elif behavior == "repeat":
            if len(value) == 0:
                return [0.0] * target_length
            last_value = value[-1]
            return value + [last_value] * (target_length - len(value))
        else:
            return value[:target_length]

    def _apply_offset(self, keypoints, indices, x_offset, y_offset):
        """
        Apply x/y offset to selected keypoints only.

        Args:
            keypoints: Flat array of [x, y, confidence] triplets
            indices: Set of keypoint indices to move
            x_offset: X offset to apply
            y_offset: Y offset to apply

        Returns:
            Modified keypoints array
        """
        if keypoints is None:
            return None

        result = keypoints.copy()
        for i in range(0, len(result), 3):
            keypoint_idx = i // 3
            # Only move if: (1) in selected indices, (2) has confidence > 0
            if keypoint_idx in indices and result[i + 2] > 0:
                result[i] += x_offset      # X coordinate
                result[i + 1] += y_offset  # Y coordinate
                # Keep confidence unchanged

        return result

    def _apply_offset_all(self, keypoints, x_offset, y_offset):
        """Apply x/y offset to all keypoints with confidence > 0."""
        if keypoints is None:
            return None

        result = keypoints.copy()
        for i in range(0, len(result), 3):
            if result[i + 2] > 0:  # Only if confidence > 0
                result[i] += x_offset
                result[i + 1] += y_offset
        return result


# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "PoseKeypointSelector": PoseKeypointSelectorNode,
    "PoseKeypointFilter": PoseKeypointFilterNode,
    "PoseKeypointMover": PoseKeypointMoverNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseKeypointSelector": "Pose Keypoint Selector",
    "PoseKeypointFilter": "Pose Keypoint Filter",
    "PoseKeypointMover": "Pose Keypoint Mover",
}
