# RePose Feature Translation TODO

This document outlines the features from RePose (SD-WebUI extension) that need to be implemented in ComfyUI-ultimate-openpose-editor.

## Current ComfyUI Implementation Status

### ✅ Already Implemented
- Basic pose scaling (body, hands, head, overall)
- Individual body part editing via AppendageEditorNode (arms, legs, hands, feet, torso)
- Rotation of body parts
- X/Y offset transformations
- Multi-person support with person indexing
- Animation support with list parameter handling
- Pose rendering and visualization
- Interactive UI editor

## RePose Features Requiring Implementation

### 🔴 HIGH PRIORITY: Core Geometric Transformations

#### 1. Translation/Moving Operations
- **Status**: Partially implemented (x/y offset exists in AppendageEditorNode only)
- **Needed**: Global pose translation node
  - Move entire pose(s) by X/Y coordinates
  - Support batch translation across animation frames
  - Support canvas-relative positioning (e.g., center pose, align to edges)
- **Implementation**: New `PoseTranslationNode`
  - Input: POSE_KEYPOINT, x_offset, y_offset
  - Optional: anchor point selection, multiple person handling

#### 2. Advanced Rotation Operations
- **Status**: Partially implemented (rotation exists in AppendageEditorNode only)
- **Needed**: Global rotation node with flexible pivot points
  - Rotate entire pose around custom pivot points
  - Rotation around body center of mass
  - Rotation around specific body keypoints (hips, neck, etc.)
  - Per-frame rotation for animations
- **Implementation**: Enhance existing rotation or create `PoseRotationNode`
  - Input: POSE_KEYPOINT, rotation_angle, pivot_type, custom_pivot_x, custom_pivot_y

#### 3. Keypoint Replacement/Mixing
- **Status**: NOT IMPLEMENTED - **HIGH VALUE FEATURE**
- **Description**: Mix poses from different sources
  - Replace entire keypoint sets from one pose with another
  - Selective body part replacement (e.g., upper body from pose A, lower body from pose B)
  - Support for replacing specific body parts: head, torso, arms, legs, hands
- **Implementation**: New `PoseKeyPointReplacementNode`
  - Inputs:
    - `POSE_KEYPOINT_BASE`: Base pose
    - `POSE_KEYPOINT_SOURCE`: Source pose for replacement
    - `replace_parts`: Multi-select (body, left_arm, right_arm, left_leg, right_leg, head, hands)
    - `blend_mode`: "replace" or "blend" (for smooth transitions)
    - `person_index_base`: Which person in base pose
    - `person_index_source`: Which person in source pose

#### 4. Frame Smoothing/Interpolation
- **Status**: NOT IMPLEMENTED - **ESSENTIAL FOR ANIMATION**
- **Description**: Smooth positional transitions across frames
  - Temporal smoothing to reduce jitter in animations
  - Interpolation between keyframes
  - Bezier/spline curve interpolation options
- **Implementation**: New `PoseTemporalSmoothingNode`
  - Inputs:
    - `POSE_KEYPOINT`: List of poses (animation frames)
    - `smoothing_factor`: Float (0.0 = no smoothing, 1.0 = maximum)
    - `smoothing_method`: ["moving_average", "gaussian", "bezier", "spline"]
    - `window_size`: Number of frames to consider for smoothing
  - Outputs: Smoothed POSE_KEYPOINT list

### 🟡 MEDIUM PRIORITY: Multi-Character/Non-Standard Anatomy Support

#### 5. Skeleton Splitting/Duplication
- **Status**: NOT IMPLEMENTED - **UNIQUE FEATURE**
- **Description**: Create multi-headed, multi-armed characters
  - Duplicate specific body parts (heads, arms, legs)
  - Split main skeleton while duplicating parts
  - Support for custom anatomies beyond OpenPose standard (2 heads, 4 arms, etc.)
- **Implementation**: New `SkeletonDuplicationNode`
  - Inputs:
    - `POSE_KEYPOINT`: Base pose
    - `duplicate_part`: ["head", "left_arm", "right_arm", "left_leg", "right_leg", "torso"]
    - `offset_x`, `offset_y`: Position offset for duplicated part
    - `rotation_offset`: Optional rotation for duplicated part
    - `num_duplicates`: How many copies (default: 1)
  - Output: Modified POSE_KEYPOINT with extra body parts

#### 6. Left/Right Body Segment Separation
- **Status**: NOT IMPLEMENTED
- **Description**: Duplicate and separate left/right body halves
  - Split body into left and right segments
  - Independent transformation of each segment
  - Useful for creating symmetric multi-body compositions
- **Implementation**: New `BodySegmentSeparationNode`
  - Inputs:
    - `POSE_KEYPOINT`: Base pose
    - `separation_type`: ["left_right", "upper_lower", "custom"]
    - `separation_distance`: Gap between segments
    - `segment_to_modify`: Which segment(s) to move/transform

#### 7. Keypoint Group Removal
- **Status**: Partially implemented (can hide in render, but not remove from data)
- **Needed**: True keypoint removal from data structure
  - Remove unwanted body parts from pose data
  - Remove specific keypoints or groups
  - Useful for creating partial poses or cleaning up detection artifacts
- **Implementation**: New `KeypointRemovalNode`
  - Inputs:
    - `POSE_KEYPOINT`: Input pose
    - `remove_parts`: Multi-select (face, left_hand, right_hand, left_arm, right_arm, legs, etc.)
    - `threshold`: Optional confidence threshold for removal
  - Output: POSE_KEYPOINT with specified parts removed

#### 8. Shoulder Position Expansion
- **Status**: NOT IMPLEMENTED
- **Description**: Expand shoulder positions for multi-body configurations
  - Widen shoulder spacing for multi-armed characters
  - Adjust shoulder positions independently
  - Maintain proper skeletal connections
- **Implementation**: Enhance `AppendageEditorNode` or create specific shoulder manipulation
  - Add "expand_shoulders" operation
  - Bidirectional expansion from neck/torso center

### 🟢 LOW PRIORITY: Quality-of-Life Features

#### 9. Batch Processing Utilities
- **Status**: Partially supported through list inputs
- **Needed**: Enhanced batch operations
  - Batch apply transformations to multiple poses
  - Batch export/import pose sequences
  - Progress tracking for large batches
- **Implementation**: Enhance existing nodes with better batch handling

#### 10. Pose Library/Preset System
- **Status**: NOT IMPLEMENTED
- **Description**: Save and load pose presets
  - Save frequently used transformations as presets
  - Pose library browser
  - Import/export pose templates
- **Implementation**: New utility nodes + UI enhancement
  - `SavePosePresetNode`
  - `LoadPosePresetNode`
  - File-based preset storage

#### 11. Code-Based Pose Sequences
- **Status**: NOT IMPLEMENTED (RePose's code-based interface)
- **Description**: Programmatic pose control
  - Generate pose sequences via expressions/scripts
  - Mathematical transformations (sin waves, bezier curves, etc.)
  - Could be implemented via custom Python node or expression evaluator
- **Implementation**: New `PoseExpressionNode`
  - Input: POSE_KEYPOINT, transformation expressions
  - Support for frame-based math operations

### 🔧 TECHNICAL ENHANCEMENTS

#### 12. Improved Multi-Person Handling
- **Current**: Basic person_index support
- **Needed**:
  - Better handling of multiple people in single frames
  - Person tracking across animation frames
  - Automatic person identification and indexing

#### 13. Animation Timeline Integration
- **Description**: Better ComfyUI workflow integration for animations
  - Frame-by-frame preview
  - Keyframe-based editing
  - Timeline scrubbing in UI

#### 14. Coordinate System Utilities
- **Description**: Helper nodes for coordinate manipulation
  - Canvas bounds enforcement
  - Coordinate system conversion utilities
  - Relative vs absolute positioning options

## Implementation Roadmap

### Phase 1: Essential Animation Features (PRIORITY)
1. PoseKeyPointReplacementNode - Mix and match poses
2. PoseTemporalSmoothingNode - Smooth animations
3. PoseTranslationNode - Global pose movement

### Phase 2: Multi-Character Support
4. SkeletonDuplicationNode - Multi-head/multi-arm support
5. KeypointRemovalNode - Clean unwanted parts
6. BodySegmentSeparationNode - Left/right separation

### Phase 3: Quality of Life
7. Enhanced batch processing
8. Pose preset system
9. Code-based transformations (if requested)

### Phase 4: Polish
10. UI improvements for animation
11. Documentation and examples
12. Performance optimizations

## Notes

- RePose's strength is in **code-based pose manipulation for animations**
- ComfyUI's strength is in **node-based visual workflows**
- Focus on translating RePose's **geometric operations** into ComfyUI nodes
- The **keypoint replacement** and **smoothing** features are most critical for animation workflows
- **Multi-character anatomy** support (multi-head, multi-arm) is a unique differentiator
