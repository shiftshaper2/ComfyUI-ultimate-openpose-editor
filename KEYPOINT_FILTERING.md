# Keypoint Filtering and Movement Nodes

This document describes the three new nodes for selective keypoint manipulation.

## Overview

Three nodes work together to enable precise control over which keypoints are visible and where they're positioned:

1. **Pose Keypoint Selector** - Define which keypoints to work with
2. **Pose Keypoint Filter** - Hide non-selected keypoints (zero confidence)
3. **Pose Keypoint Mover** - Move only selected keypoints

## Node Details

### 1. Pose Keypoint Selector

**Purpose:** Create a selection of keypoints without requiring pose data input.

**Inputs:**
- `selection_type` (dropdown): Choose from 25 preset body part groupings:
  - Logical groups: `all`, `head`, `head_and_neck`, `upper_body`, `lower_body`, `arms`, `legs`, `left_side`, `right_side`
  - Individual appendages: `left_full_arm`, `right_full_arm`, `left_upper_arm`, `right_upper_arm`, etc.
  - `custom`: Use checkboxes for fine control
- Individual checkboxes (when `selection_type` = "custom"):
  - `include_head`, `include_neck`, `include_torso`
  - `include_left_arm`, `include_right_arm`
  - `include_left_leg`, `include_right_leg`
  - `include_left_hand`, `include_right_hand`, `include_face`

**Outputs:**
- `POSE_SELECTION`: Dictionary containing:
  - `body_indices`: List of body keypoint indices to include
  - `include_face`: Whether to include face keypoints
  - `include_left_hand`: Whether to include left hand
  - `include_right_hand`: Whether to include right hand

### 2. Pose Keypoint Filter

**Purpose:** Zero out confidence values for non-selected keypoints (makes them invisible in renders).

**Inputs:**
- `POSE_KEYPOINT` (required): Input pose data
- `POSE_SELECTION` (required): Selection from Pose Keypoint Selector
- `person_index` (optional, default=-1): Which person to filter (-1 for all)
- `invert_selection` (optional, default=False): If true, hide selected keypoints instead

**Outputs:**
- `POSE_KEYPOINT`: Pose data with confidence zeroed for filtered keypoints

**Notes:**
- Keeps data structure intact (array sizes unchanged)
- Only sets confidence to 0, doesn't remove keypoints
- Safe for compatibility with existing nodes

### 3. Pose Keypoint Mover

**Purpose:** Move selected keypoints by x/y offsets. Unselected keypoints remain in place.

**Inputs:**
- `POSE_KEYPOINT` (required): Input pose data
- `x_offset` (required): X offset in normalized coordinates (supports lists for animation)
- `y_offset` (required): Y offset in normalized coordinates (supports lists for animation)
- `POSE_SELECTION` (optional): Selection from Pose Keypoint Selector (takes priority)
- `appendage_type` (optional, default="all"): Fallback body part selection
- `person_index` (optional, default=-1): Which person to move (-1 for all)
- `list_mismatch_behavior` (optional): "truncate", "loop", or "repeat"
- `affect_hands` (optional, default=False): Move hands when wrists are selected
- `affect_face` (optional, default=False): Move face when head is selected

**Outputs:**
- `POSE_KEYPOINT`: Pose data with selected keypoints moved

**Notes:**
- Supports animation via list inputs (e.g., `x_offset=[0.0, 0.1, 0.2, ...]`)
- Can use `POSE_SELECTION` or standalone with `appendage_type`
- Unselected keypoints stay at original position

## Example Workflows

### Example 1: Filter and Move Upper Body

```
OpenposeEditorNode (load/create pose)
  ↓ POSE_KEYPOINT
  ↓
Pose Keypoint Selector (selection_type="upper_body")
  ↓ POSE_SELECTION
  ↓
Pose Keypoint Filter (hide lower body)
  ↓ POSE_KEYPOINT (lower body invisible)
  ↓
Pose Keypoint Mover (x_offset=0.1, y_offset=-0.2)
  ↓ POSE_KEYPOINT (upper body moved, lower body filtered)
  ↓
OpenposeEditorNode (render final result)
```

**Result:** Only upper body is visible and has been moved by (0.1, -0.2)

### Example 2: Move Left Arm Without Filtering

```
OpenposeEditorNode
  ↓ POSE_KEYPOINT
  ↓
Pose Keypoint Selector (selection_type="left_full_arm")
  ↓ POSE_SELECTION
  ↓
Pose Keypoint Mover (x_offset=0.15, affect_hands=True)
  ↓ POSE_KEYPOINT (left arm + hand moved)
  ↓
OpenposeEditorNode (render)
```

**Result:** Entire left arm (including hand) moved, rest of body unchanged, all visible

### Example 3: Standalone Movement (No Selector Needed)

```
OpenposeEditorNode
  ↓ POSE_KEYPOINT
  ↓
Pose Keypoint Mover (appendage_type="torso", y_offset=-0.3)
  ↓ POSE_KEYPOINT
  ↓
OpenposeEditorNode (render)
```

**Result:** Torso moved up, no filtering applied

### Example 4: Animated Movement

```
OpenposeEditorNode (animation sequence)
  ↓ POSE_KEYPOINT (list of frames)
  ↓
Pose Keypoint Selector (selection_type="arms")
  ↓ POSE_SELECTION
  ↓
Pose Keypoint Mover (x_offset=[0.0, 0.05, 0.1, 0.15, 0.2], list_mismatch_behavior="loop")
  ↓ POSE_KEYPOINT (arms move progressively)
  ↓
OpenposeEditorNode (render animation)
```

**Result:** Arms move smoothly across frames

## Body Part Groupings

The following preset groupings are available:

**Logical Groups:**
- `all`: All 18 body keypoints
- `head`: Nose, eyes, ears (no neck)
- `head_and_neck`: Head + neck
- `upper_body`: Head, neck, torso, both arms
- `lower_body`: Hips, both legs
- `arms`: Both full arms
- `legs`: Both full legs
- `left_side`: Left arm, leg, eye, ear
- `right_side`: Right arm, leg, eye, ear

**Individual Appendages:**
- Arms: `left_upper_arm`, `left_forearm`, `left_full_arm`, `right_upper_arm`, `right_forearm`, `right_full_arm`
- Legs: `left_upper_leg`, `left_lower_leg`, `left_full_leg`, `right_upper_leg`, `right_lower_leg`, `right_full_leg`
- Other: `left_foot`, `right_foot`, `torso`, `shoulders`

## Technical Details

### COCO 18-Keypoint Format

```
0: Nose        5: LShoulder   10: RAnkle     15: LEye
1: Neck        6: LElbow      11: LHip       16: REar
2: RShoulder   7: LWrist      12: LKnee      17: LEar
3: RElbow      8: RHip        13: LAnkle
4: RWrist      9: RKnee       14: REye
```

### Data Structure

Keypoints are stored as flat arrays of `[x, y, confidence]` triplets:
- `x`, `y`: Normalized coordinates (0.0-1.0) or pixel coordinates (>2.0)
- `confidence`: 0 = not detected/invisible, >0 = visible

### Filter vs Move

- **Filter Node:** Sets `confidence = 0` → keypoints become invisible in renders
- **Mover Node:** Changes `x` and `y` values → keypoints change position
- **Important:** Mover does NOT zero out unselected keypoints; they stay at original position

## Files

- `body_part_definitions.py`: Shared body part groupings
- `pose_filter_nodes.py`: Implementation of all three nodes
- `__init__.py`: Node registration
