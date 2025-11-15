"""
Node for temporal smoothing of pose animations.

Applies exponential smoothing to reduce jitter and create smoother transitions
between frames in pose sequences.
"""

import copy


class PoseTemporalSmoothingNode:
    """
    Apply temporal smoothing to pose sequences using exponential smoothing.

    Each frame is blended with the previous frame by a smoothing factor:
    new_position = previous_position + smoothing_factor * (target_position - previous_position)

    Example: sequence [0, 1, 1, 1, 0] with smoothing 0.2 becomes:
    Frame 0: 0 (unchanged)
    Frame 1: 0 + 0.2*(1-0) = 0.2
    Frame 2: 0.2 + 0.2*(1-0.2) = 0.36
    Frame 3: 0.36 + 0.2*(1-0.36) = 0.488
    Frame 4: 0.488 + 0.2*(0-0.488) = 0.390
    """

    @classmethod
    def INPUT_TYPES(s):
        # Keypoint indices for COCO 18-point format
        keypoint_options = [
            "none",
            "0: Nose", "1: Neck",
            "2: RShoulder", "3: RElbow", "4: RWrist",
            "5: LShoulder", "6: LElbow", "7: LWrist",
            "8: RHip", "9: RKnee", "10: RAnkle",
            "11: LHip", "12: LKnee", "13: LAnkle",
            "14: REye", "15: LEye", "16: REar", "17: LEar"
        ]

        return {
            "required": {
                "POSE_KEYPOINT": ("POSE_KEYPOINT", {"tooltip": "Pose sequence to smooth"}),
                "smoothing_factor": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 1.0, "step": 0.01,
                                              "tooltip": "0=no change, 1=instant transition"}),
            },
            "optional": {
                "POSE_SELECTION": ("POSE_SELECTION", {"tooltip": "Which keypoints to smooth (from selector node)"}),
                "focus_point": (keypoint_options, {"default": "none",
                                                   "tooltip": "Point to use as reference for smoothing (none = smooth all independently)"}),
                "person_index": ("INT", {"default": -1, "min": -1, "max": 100,
                                        "tooltip": "Which person to smooth (-1 for all)"}),
                "smooth_hands": ("BOOLEAN", {"default": True,
                                            "tooltip": "Apply smoothing to hand keypoints"}),
                "smooth_face": ("BOOLEAN", {"default": False,
                                           "tooltip": "Apply smoothing to face keypoints"}),
            },
        }

    RETURN_NAMES = ("POSE_KEYPOINT",)
    RETURN_TYPES = ("POSE_KEYPOINT",)
    FUNCTION = "smooth_pose"
    CATEGORY = "ultimate-openpose"

    def smooth_pose(self, POSE_KEYPOINT, smoothing_factor,
                   POSE_SELECTION=None, focus_point="none",
                   person_index=-1, smooth_hands=True, smooth_face=False):
        """
        Apply temporal smoothing to pose sequence.

        Args:
            POSE_KEYPOINT: Sequence of poses to smooth
            smoothing_factor: How much to move toward target (0-1)
            POSE_SELECTION: Optional selection of which keypoints to smooth
            focus_point: Reference point for coordinated smoothing (or "none")
            person_index: Which person to smooth (-1 for all)
            smooth_hands: Whether to smooth hand keypoints
            smooth_face: Whether to smooth face keypoints

        Returns:
            Smoothed pose sequence
        """
        if not isinstance(POSE_KEYPOINT, list) or len(POSE_KEYPOINT) <= 1:
            # Single frame or not a list, no smoothing needed
            return (POSE_KEYPOINT,)

        # Parse focus point
        focus_point_idx = None
        if focus_point != "none":
            focus_point_idx = int(focus_point.split(":")[0])

        # Determine which keypoints to smooth
        if POSE_SELECTION:
            body_indices_to_smooth = set(POSE_SELECTION.get('body_indices', []))
            do_smooth_hands = POSE_SELECTION.get('include_left_hand', False) or POSE_SELECTION.get('include_right_hand', False) or smooth_hands
            do_smooth_face = POSE_SELECTION.get('include_face', False) or smooth_face
        else:
            # Smooth all body keypoints
            body_indices_to_smooth = set(range(18))
            do_smooth_hands = smooth_hands
            do_smooth_face = smooth_face

        # Deep copy and smooth frame by frame
        smoothed_poses = [copy.deepcopy(POSE_KEYPOINT[0])]  # First frame unchanged

        for frame_idx in range(1, len(POSE_KEYPOINT)):
            previous_frame = smoothed_poses[frame_idx - 1]
            current_frame = copy.deepcopy(POSE_KEYPOINT[frame_idx])

            if 'people' not in previous_frame or 'people' not in current_frame:
                smoothed_poses.append(current_frame)
                continue

            # Determine which people to smooth
            people_to_smooth = range(len(current_frame['people'])) if person_index == -1 else [person_index]

            for person_idx in people_to_smooth:
                if person_idx >= len(current_frame['people']) or person_idx >= len(previous_frame['people']):
                    continue

                current_person = current_frame['people'][person_idx]
                previous_person = previous_frame['people'][person_idx]

                # If focus point is specified, smooth relative to that point
                if focus_point_idx is not None:
                    self._smooth_person_with_focus(
                        current_person, previous_person, smoothing_factor,
                        focus_point_idx, body_indices_to_smooth,
                        do_smooth_hands, do_smooth_face
                    )
                else:
                    # Smooth each point independently
                    self._smooth_person_independent(
                        current_person, previous_person, smoothing_factor,
                        body_indices_to_smooth, do_smooth_hands, do_smooth_face
                    )

            smoothed_poses.append(current_frame)

        return (smoothed_poses,)

    def _smooth_person_with_focus(self, current_person, previous_person, smoothing_factor,
                                  focus_point_idx, body_indices_to_smooth,
                                  smooth_hands, smooth_face):
        """
        Smooth keypoints relative to a focus point.

        First smooth the focus point, then smooth other points relative to it.
        """
        current_body = current_person.get('pose_keypoints_2d', [])
        previous_body = previous_person.get('pose_keypoints_2d', [])

        if not current_body or not previous_body:
            return

        # First, smooth the focus point itself
        focus_idx = focus_point_idx * 3
        if len(current_body) > focus_idx + 2 and len(previous_body) > focus_idx + 2:
            if current_body[focus_idx + 2] > 0 and previous_body[focus_idx + 2] > 0:
                current_body[focus_idx] = self._smooth_value(
                    previous_body[focus_idx], current_body[focus_idx], smoothing_factor
                )
                current_body[focus_idx + 1] = self._smooth_value(
                    previous_body[focus_idx + 1], current_body[focus_idx + 1], smoothing_factor
                )

        # Get smoothed focus point position
        focus_pos_current = [current_body[focus_idx], current_body[focus_idx + 1]]

        # Smooth other body keypoints relative to focus point
        for keypoint_idx in body_indices_to_smooth:
            if keypoint_idx == focus_point_idx:
                continue  # Already smoothed

            i = keypoint_idx * 3
            if len(current_body) > i + 2 and len(previous_body) > i + 2:
                if current_body[i + 2] > 0 and previous_body[i + 2] > 0:
                    current_body[i] = self._smooth_value(
                        previous_body[i], current_body[i], smoothing_factor
                    )
                    current_body[i + 1] = self._smooth_value(
                        previous_body[i + 1], current_body[i + 1], smoothing_factor
                    )

        current_person['pose_keypoints_2d'] = current_body

        # Smooth hands and face if specified
        if smooth_hands:
            self._smooth_keypoint_array(
                current_person, previous_person, 'hand_left_keypoints_2d', smoothing_factor
            )
            self._smooth_keypoint_array(
                current_person, previous_person, 'hand_right_keypoints_2d', smoothing_factor
            )

        if smooth_face:
            self._smooth_keypoint_array(
                current_person, previous_person, 'face_keypoints_2d', smoothing_factor
            )

    def _smooth_person_independent(self, current_person, previous_person, smoothing_factor,
                                   body_indices_to_smooth, smooth_hands, smooth_face):
        """
        Smooth each keypoint independently (no focus point).
        """
        current_body = current_person.get('pose_keypoints_2d', [])
        previous_body = previous_person.get('pose_keypoints_2d', [])

        if current_body and previous_body:
            # Smooth selected body keypoints
            for keypoint_idx in body_indices_to_smooth:
                i = keypoint_idx * 3
                if len(current_body) > i + 2 and len(previous_body) > i + 2:
                    if current_body[i + 2] > 0 and previous_body[i + 2] > 0:
                        current_body[i] = self._smooth_value(
                            previous_body[i], current_body[i], smoothing_factor
                        )
                        current_body[i + 1] = self._smooth_value(
                            previous_body[i + 1], current_body[i + 1], smoothing_factor
                        )

            current_person['pose_keypoints_2d'] = current_body

        # Smooth hands and face if specified
        if smooth_hands:
            self._smooth_keypoint_array(
                current_person, previous_person, 'hand_left_keypoints_2d', smoothing_factor
            )
            self._smooth_keypoint_array(
                current_person, previous_person, 'hand_right_keypoints_2d', smoothing_factor
            )

        if smooth_face:
            self._smooth_keypoint_array(
                current_person, previous_person, 'face_keypoints_2d', smoothing_factor
            )

    def _smooth_keypoint_array(self, current_person, previous_person, keypoint_field, smoothing_factor):
        """
        Smooth an entire keypoint array (hands or face).
        """
        if keypoint_field not in current_person or keypoint_field not in previous_person:
            return

        current_kps = current_person[keypoint_field]
        previous_kps = previous_person[keypoint_field]

        if current_kps is None or previous_kps is None:
            return

        if len(current_kps) != len(previous_kps):
            return

        # Smooth each keypoint
        smoothed = []
        for i in range(0, len(current_kps), 3):
            if len(current_kps) > i + 2 and len(previous_kps) > i + 2:
                if current_kps[i + 2] > 0 and previous_kps[i + 2] > 0:
                    # Smooth x and y
                    smoothed.append(self._smooth_value(previous_kps[i], current_kps[i], smoothing_factor))
                    smoothed.append(self._smooth_value(previous_kps[i + 1], current_kps[i + 1], smoothing_factor))
                    smoothed.append(current_kps[i + 2])  # Keep confidence
                else:
                    # No confidence, keep current
                    smoothed.extend([current_kps[i], current_kps[i + 1], current_kps[i + 2]])

        current_person[keypoint_field] = smoothed

    def _smooth_value(self, previous, current, factor):
        """
        Apply exponential smoothing: new = previous + factor * (current - previous)

        Args:
            previous: Previous frame value
            current: Current frame target value
            factor: Smoothing factor (0-1)

        Returns:
            Smoothed value
        """
        return previous + factor * (current - previous)


# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "PoseTemporalSmoothing": PoseTemporalSmoothingNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseTemporalSmoothing": "Pose Temporal Smoothing",
}
