# GR00T N1.7 — Dual OMX Bimanual (store_play)

ROBOTIS OpenManipulator-X 2팔 구성으로 GR00T N1.7을 파인튜닝하는 가이드.
`minssuung/store_play_v2_en` 데이터셋 기준.

## 하드웨어 구성

```
Left OMX-F  (/dev/omx_left_follower)    Right OMX-F  (/dev/omx_right_follower)
  shoulder_pan   [0]                       shoulder_pan   [6]
  shoulder_lift  [1]                       shoulder_lift  [7]
  elbow_flex     [2]                       elbow_flex     [8]
  wrist_flex     [3]                       wrist_flex     [9]
  wrist_roll     [4]                       wrist_roll     [10]
  gripper        [5]                       gripper        [11]

카메라 (dataset key → 물리 장치):
  observation.images.top         → /dev/cam_top        (상단 오버헤드)
  observation.images.wrist_left  → /dev/cam_wrist_left (왼팔 손목)
  observation.images.wrist_right → /dev/cam_wrist_right (오른팔 손목)
```

State/Action 차원: **12** (left 6 + right 6)  
단위: LeRobot motor **.pos** — radian 아님 (ROS `/joint_states` 우회)

## 데이터셋

**`minssuung/store_play_v2_en`** — LeRobot BiOmxFollower로 수집한 가게놀이 시연 데이터.

- HuggingFace 에서 받아 `meta/modality.json` 복사:

```bash
# LeRobot v2 포맷으로 다운로드
huggingface-cli download minssuung/store_play_v2_en \
  --repo-type dataset \
  --local-dir examples/OMX_bimanual/store_play_v2_en

# modality.json 을 meta/ 에 복사
cp examples/OMX_bimanual/modality.json \
   examples/OMX_bimanual/store_play_v2_en/meta/modality.json
```

### 데이터셋 구조

```
store_play_v2_en/
├── meta/
│   ├── modality.json          ← 위에서 복사
│   ├── info.json
│   └── episodes.jsonl
├── data/
│   └── chunk-000/
│       └── episode_*.parquet  (observation.state[12], action[12])
└── videos/
    └── chunk-000/
        ├── observation.images.top_episode_*.mp4
        ├── observation.images.wrist_left_episode_*.mp4
        └── observation.images.wrist_right_episode_*.mp4
```

## 파인튜닝

```bash
CUDA_VISIBLE_DEVICES=0 NUM_GPUS=1 uv run bash examples/finetune.sh \
  --base-model-path nvidia/GR00T-N1.7-3B \
  --dataset-path examples/OMX_bimanual/store_play_v2_en \
  --modality-config-path examples/OMX_bimanual/omx_bimanual_config.py \
  --embodiment-tag NEW_EMBODIMENT \
  --output-dir /tmp/omx_bimanual_finetune
```

VRAM ~25GB 필요. RTX 4090(24GB)는 `--per-device-train-batch-size 1` + gradient checkpointing 활성화.

## 추론 서버

```bash
uv run python gr00t/eval/run_gr00t_server.py \
  --model-path /tmp/omx_bimanual_finetune/checkpoint-10000 \
  --embodiment-tag NEW_EMBODIMENT \
  --modality-config-path examples/OMX_bimanual/omx_bimanual_config.py \
  --denoising-steps 4 \
  --port 8765
```

## 기존 파이프라인 연결 (physical-ai-repo-2)

가게놀이 `runner_entry.py`의 `smolvla_http` provider가 `http://localhost:8765/chunk`로
obs/action을 교환한다. GR00T 추론 서버를 같은 포트로 띄우면 `game_smolvla_http.yaml` 설정
변경 없이 연결 가능.

단, GR00T 서버의 `/chunk` 요청/응답 스키마가 기존 SmolVLA inference_server와 다를 수 있으므로
`runner_entry.py`의 `_make_smolvla_http_provider` 요청 포맷 확인 필요.

## 오픈루프 평가

```bash
uv run python gr00t/eval/open_loop_eval.py \
  --dataset-path examples/OMX_bimanual/store_play_v2_en \
  --embodiment-tag NEW_EMBODIMENT \
  --modality-config-path examples/OMX_bimanual/omx_bimanual_config.py \
  --model-path /tmp/omx_bimanual_finetune/checkpoint-10000 \
  --traj-ids 0 \
  --action-horizon 16 \
  --steps 400
```
