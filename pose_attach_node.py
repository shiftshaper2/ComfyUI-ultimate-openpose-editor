"""
Node for attaching body parts from one pose to another.

Replaces keypoints in a base pose with keypoints from an attachment pose,
maintaining relative positions around a specified attachment point.
"""

import copy


class PoseAttachNode:
    """
    Attach body parts from one pose to another by replacing keypoints
    while maintaining relative positions around an attachment point.

    Example: Attach a hand from pose A to an arm in pose B at the wrist.
    The wrist stays in its original position, and all hand keypoints
    maintain their relative positions to the wrist.
    """

    @classmethod
    def INPUT_TYPES(s):
        # Keypoint indices for COCO 18-point format
        keypoint_options = [
            "0: Nose", "1: Neck",
            "2: RShoulder", "3: RElbow", "4: RWrist",
            "5: LShoulder", "6: LElbow", "7: LWrist",
            "8: RHip", "9: RKnee", "10: RAnkle",
            "11: LHip", "12: LKnee", "13: LAnkle",
            "14: REye", "15: LEye", "16: REar", "17: LEar"
        ]

        return {
            "required": {
                "BASE_POSE": ("POSE_KEYPOINT", {"tooltip": "Base pose to attach to"}),
                "ATTACHMENT_POSE": ("POSE_KEYPOINT", {"tooltip": "Pose containing parts to attach"}),
                "attachment_point": (keypoint_options, {"default": "4: RWrist",
                                                        "tooltip": "Keypoint that defines the attachment position"}),
            },
            "optional": {
                "POSE_SELECTION": ("POSE_SELECTION", {"tooltip": "Which keypoints to attach (from selector node)"}),
                "base_person_index": ("INT", {"default": 0, "min": 0, "max": 100,
                                             "tooltip": "Which person in base pose"}),
                "attachment_person_index": ("INT", {"default": 0, "min": 0, "max": 100,
                                                   "tooltip": "Which person in attachment pose"}),
                "attach_hands": ("BOOLEAN", {"default": False,
                                            "tooltip": "Also attach hand keypoints"}),
                "attach_face": ("BOOLEAN", {"default": False,
                                          "tooltip": "Also attach face keypoints"}),
            },
        }

    RETURN_NAMES = ("POSE_KEYPOINT",)
    RETURN_TYPES = ("POSE_KEYPOINT",)
    FUNCTION = "attach_pose"
    CATEGORY = "ultimate-openpose"

    def attach_pose(self, BASE_POSE, ATTACHMENT_POSE, attachment_point,
                   POSE_SELECTION=None, base_person_index=0,
                   attachment_person_index=0, attach_hands=False, attach_face=False):
        """
        Attach body parts from ATTACHMENT_POSE to BASE_POSE.

        Args:
            BASE_POSE: Base pose to modify
            ATTACHMENT_POSE: Pose containing parts to attach
            attachment_point: Keypoint index that defines attachment position (e.g., "4: RWrist")
            POSE_SELECTION: Optional selection of which keypoints to attach
            base_person_index: Which person in base pose
            attachment_person_index: Which person in attachment pose
            attach_hands: Whether to also attach hand keypoints
            attach_face: Whether to also attach face keypoints

        Returns:
            Modified base pose with attached parts
        """
        # Parse attachment point index from string like "4: RWrist"
        attach_point_idx = int(attachment_point.split(":")[0])

        # Normalize poses to lists
        base_poses = BASE_POSE if isinstance(BASE_POSE, list) else [BASE_POSE]
        attachment_poses = ATTACHMENT_POSE if isinstance(ATTACHMENT_POSE, list) else [ATTACHMENT_POSE]

        # Process frame by frame
        output_poses = []
        max_frames = max(len(base_poses), len(attachment_poses))

        for frame_idx in range(max_frames):
            # Get frames (loop if one is shorter)
            base_frame = copy.deepcopy(base_poses[frame_idx % len(base_poses)])
            attachment_frame = attachment_poses[frame_idx % len(attachment_poses)]

            if 'people' not in base_frame or 'people' not in attachment_frame:
                output_poses.append(base_frame)
                continue

            # Check person indices are valid
            if base_person_index >= len(base_frame['people']):
                output_poses.append(base_frame)
                continue
            if attachment_person_index >= len(attachment_frame['people']):
                output_poses.append(base_frame)
                continue

            base_person = base_frame['people'][base_person_index]
            attachment_person = attachment_frame['people'][attachment_person_index]

            # Perform attachment
            self._attach_keypoints(
                base_person, attachment_person, attach_point_idx,
                POSE_SELECTION, attach_hands, attach_face
            )

            output_poses.append(base_frame)

        return (output_poses,)

    def _attach_keypoints(self, base_person, attachment_person, attach_point_idx,
                         pose_selection, attach_hands, attach_face):
        """
        Attach keypoints from attachment_person to base_person.

        The attachment point stays at its base position, and all other
        selected keypoints are positioned relative to it.
        """
        # Get body keypoints
        base_keypoints = base_person.get('pose_keypoints_2d', [])
        attachment_keypoints = attachment_person.get('pose_keypoints_2d', [])

        if not base_keypoints or not attachment_keypoints:
            return

        # Get attachment point positions
        base_attach_pos = self._get_keypoint_pos(base_keypoints, attach_point_idx)
        attachment_attach_pos = self._get_keypoint_pos(attachment_keypoints, attach_point_idx)

        if base_attach_pos is None or attachment_attach_pos is None:
            return

        # Calculate offset to align attachment point
        offset_x = base_attach_pos[0] - attachment_attach_pos[0]
        offset_y = base_attach_pos[1] - attachment_attach_pos[1]

        # Determine which keypoints to attach
        if pose_selection:
            indices_to_attach = set(pose_selection.get('body_indices', []))
            do_attach_hands = pose_selection.get('include_left_hand', False) or pose_selection.get('include_right_hand', False) or attach_hands
            do_attach_face = pose_selection.get('include_face', False) or attach_face
        else:
            # No selection - attach all keypoints with confidence > 0
            indices_to_attach = set()
            for i in range(0, len(attachment_keypoints), 3):
                keypoint_idx = i // 3
                if len(attachment_keypoints) > i + 2 and attachment_keypoints[i + 2] > 0:
                    indices_to_attach.add(keypoint_idx)
            do_attach_hands = attach_hands
            do_attach_face = attach_face

        # Attach body keypoints
        new_keypoints = base_keypoints[:]
        for keypoint_idx in indices_to_attach:
            i = keypoint_idx * 3
            if len(attachment_keypoints) > i + 2:
                # Get attachment keypoint with offset applied
                x = attachment_keypoints[i] + offset_x
                y = attachment_keypoints[i + 1] + offset_y
                conf = attachment_keypoints[i + 2]

                # Replace in base keypoints
                if len(new_keypoints) > i + 2:
                    new_keypoints[i] = x
                    new_keypoints[i + 1] = y
                    new_keypoints[i + 2] = conf

        base_person['pose_keypoints_2d'] = new_keypoints

        # Attach hands if specified
        if do_attach_hands:
            self._attach_hand_keypoints(base_person, attachment_person, offset_x, offset_y, 'hand_left_keypoints_2d')
            self._attach_hand_keypoints(base_person, attachment_person, offset_x, offset_y, 'hand_right_keypoints_2d')

        # Attach face if specified
        if do_attach_face:
            self._attach_face_keypoints(base_person, attachment_person, offset_x, offset_y)

    def _attach_hand_keypoints(self, base_person, attachment_person, offset_x, offset_y, keypoint_field):
        """Attach hand keypoints with offset applied."""
        if keypoint_field not in attachment_person or not attachment_person[keypoint_field]:
            return

        attachment_hand = attachment_person[keypoint_field]
        if attachment_hand is None:
            return

        # Apply offset to all hand keypoints
        new_hand = []
        for i in range(0, len(attachment_hand), 3):
            if len(attachment_hand) > i + 2:
                new_hand.append(attachment_hand[i] + offset_x)
                new_hand.append(attachment_hand[i + 1] + offset_y)
                new_hand.append(attachment_hand[i + 2])

        base_person[keypoint_field] = new_hand

    def _attach_face_keypoints(self, base_person, attachment_person, offset_x, offset_y):
        """Attach face keypoints with offset applied."""
        if 'face_keypoints_2d' not in attachment_person or not attachment_person['face_keypoints_2d']:
            return

        attachment_face = attachment_person['face_keypoints_2d']
        if attachment_face is None:
            return

        # Apply offset to all face keypoints
        new_face = []
        for i in range(0, len(attachment_face), 3):
            if len(attachment_face) > i + 2:
                new_face.append(attachment_face[i] + offset_x)
                new_face.append(attachment_face[i + 1] + offset_y)
                new_face.append(attachment_face[i + 2])

        base_person['face_keypoints_2d'] = new_face

    def _get_keypoint_pos(self, keypoints, keypoint_idx):
        """Get [x, y] position of a keypoint, or None if not available."""
        i = keypoint_idx * 3
        if len(keypoints) <= i + 2:
            return None
        if keypoints[i + 2] <= 0:  # No confidence
            return None
        return [keypoints[i], keypoints[i + 1]]


# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "PoseAttach": PoseAttachNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseAttach": "Pose Attach",
}
