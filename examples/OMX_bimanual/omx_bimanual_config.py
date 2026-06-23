# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Embodiment config for dual ROBOTIS OpenManipulator-X (OMX-F) bimanual setup.
# Based on minssuung/store_play_v2_en dataset (store_play task).
#
# Hardware:
#   Left OMX-F  — /dev/omx_left_follower  (5 joints + gripper = 6 DOF)
#   Right OMX-F — /dev/omx_right_follower (5 joints + gripper = 6 DOF)
#   Total state/action dim: 12
#
# State/action layout (matches runner_entry.py MOTOR_ORDER):
#   [0]  left_shoulder_pan.pos
#   [1]  left_shoulder_lift.pos
#   [2]  left_elbow_flex.pos
#   [3]  left_wrist_flex.pos
#   [4]  left_wrist_roll.pos
#   [5]  left_gripper.pos
#   [6]  right_shoulder_pan.pos
#   [7]  right_shoulder_lift.pos
#   [8]  right_elbow_flex.pos
#   [9]  right_wrist_flex.pos
#   [10] right_wrist_roll.pos
#   [11] right_gripper.pos
#
# Unit: LeRobot motor .pos (NOT radians — bypasses ROS to avoid unit mismatch with store_play_v2_en)
#
# Cameras (dataset keys):
#   observation.images.top        — top-down overhead  (/dev/cam_top)
#   observation.images.wrist_left — left wrist egocentric  (/dev/cam_wrist_left)
#   observation.images.wrist_right — right wrist egocentric (/dev/cam_wrist_right)

from gr00t.configs.data.embodiment_configs import register_modality_config
from gr00t.data.embodiment_tags import EmbodimentTag
from gr00t.data.types import (
    ActionConfig,
    ActionFormat,
    ActionRepresentation,
    ActionType,
    ModalityConfig,
)

omx_bimanual_config = {
    "video": ModalityConfig(
        delta_indices=[0],
        modality_keys=["top", "wrist_left", "wrist_right"],
    ),
    "state": ModalityConfig(
        delta_indices=[0],
        modality_keys=[
            "left_arm",     # left_shoulder_pan/lift, elbow_flex, wrist_flex/roll (.pos)
            "left_gripper",
            "right_arm",    # right_shoulder_pan/lift, elbow_flex, wrist_flex/roll (.pos)
            "right_gripper",
        ],
    ),
    "action": ModalityConfig(
        delta_indices=list(range(0, 16)),
        modality_keys=[
            "left_arm",
            "left_gripper",
            "right_arm",
            "right_gripper",
        ],
        action_configs=[
            # store_play_v2_en은 절대 .pos 단위로 수집됨 — ABSOLUTE 사용.
            # (ROS radian 우회해 LeRobot .pos 직결이므로 delta 변환 불필요)
            ActionConfig(
                rep=ActionRepresentation.ABSOLUTE,
                type=ActionType.NON_EEF,
                format=ActionFormat.DEFAULT,
            ),
            ActionConfig(
                rep=ActionRepresentation.ABSOLUTE,
                type=ActionType.NON_EEF,
                format=ActionFormat.DEFAULT,
            ),
            ActionConfig(
                rep=ActionRepresentation.ABSOLUTE,
                type=ActionType.NON_EEF,
                format=ActionFormat.DEFAULT,
            ),
            ActionConfig(
                rep=ActionRepresentation.ABSOLUTE,
                type=ActionType.NON_EEF,
                format=ActionFormat.DEFAULT,
            ),
        ],
    ),
    "language": ModalityConfig(
        delta_indices=[0],
        modality_keys=["annotation.human.task_description"],
    ),
}

register_modality_config(omx_bimanual_config, embodiment_tag=EmbodimentTag.NEW_EMBODIMENT)
