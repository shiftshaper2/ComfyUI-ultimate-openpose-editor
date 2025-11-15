"""
Shared body part definitions for OpenPose keypoint manipulation.

This module provides centralized definitions of body part groupings
based on the COCO 18-keypoint format used by ComfyUI ControlNet Aux OpenPose.
"""

# COCO 18-keypoint format (0-based indexing):
# 0: Nose, 1: Neck, 2: RShoulder, 3: RElbow, 4: RWrist, 5: LShoulder, 6: LElbow, 7: LWrist,
# 8: RHip, 9: RKnee, 10: RAnkle, 11: LHip, 12: LKnee, 13: LAnkle, 14: REye, 15: LEye, 16: REar, 17: LEar

BODY_PART_GROUPS = {
    # Individual appendages (compatible with AppendageEditorNode)
    "left_upper_arm": [5, 6],          # LShoulder, LElbow
    "left_forearm": [6, 7],            # LElbow, LWrist
    "left_full_arm": [5, 6, 7],        # Full left arm
    "right_upper_arm": [2, 3],         # RShoulder, RElbow
    "right_forearm": [3, 4],           # RElbow, RWrist
    "right_full_arm": [2, 3, 4],       # Full right arm

    "left_upper_leg": [11, 12],        # LHip, LKnee
    "left_lower_leg": [12, 13],        # LKnee, LAnkle
    "left_full_leg": [11, 12, 13],     # Full left leg
    "right_upper_leg": [8, 9],         # RHip, RKnee
    "right_lower_leg": [9, 10],        # RKnee, RAnkle
    "right_full_leg": [8, 9, 10],      # Full right leg

    "left_foot": [13],                 # LAnkle (COCO has no foot keypoints)
    "right_foot": [10],                # RAnkle

    "torso": [1, 2, 5, 8, 11],         # Neck, RShoulder, LShoulder, RHip, LHip
    "shoulders": [2, 5],               # Both shoulders

    # Logical groupings
    "head": [0, 14, 15, 16, 17],       # Nose, eyes, ears (no neck)
    "head_and_neck": [0, 1, 14, 15, 16, 17],  # Head + neck
    "upper_body": [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17],  # Head, neck, torso, arms
    "lower_body": [8, 9, 10, 11, 12, 13],  # Hips, legs, feet
    "arms": [2, 3, 4, 5, 6, 7],        # Both full arms
    "legs": [8, 9, 10, 11, 12, 13],    # Both full legs
    "left_side": [5, 6, 7, 11, 12, 13, 15, 17],  # Left arm, leg, eye, ear
    "right_side": [2, 3, 4, 8, 9, 10, 14, 16],   # Right arm, leg, eye, ear

    # Special
    "all": list(range(18)),            # All body keypoints
}

def get_body_part_indices(part_name):
    """
    Get keypoint indices for a named body part.

    Args:
        part_name: Name of the body part (must be in BODY_PART_GROUPS)

    Returns:
        List of keypoint indices, or empty list if not found
    """
    return BODY_PART_GROUPS.get(part_name, [])

def get_all_part_names():
    """
    Get a list of all available body part names.

    Returns:
        Sorted list of body part names
    """
    return sorted(BODY_PART_GROUPS.keys())
