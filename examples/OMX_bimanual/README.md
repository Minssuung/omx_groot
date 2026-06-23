# GR00T N1.7 — Dual OMX Bimanual Finetuning

ROBOTIS OpenManipulator-X(OMX) 2팔 구성으로 GR00T N1.7을 파인튜닝하는 가이드.

## 하드웨어 구성

```
Left OMX-F  (/dev/omx_left_follower)    Right OMX-F  (/dev/omx_right_follower)
  shoulder_pan   [0]                       shoulder_pan   [6]
  shoulder_lift  [1]                       shoulder_lift  [7]
  elbow_flex     [2]                       elbow_flex     [8]
  wrist_flex     [3]                       wrist_flex     [9]
  wrist_roll     [4]                       wrist_roll     [10]
  gripper        [5]                       gripper        [11]

카메라:
  top        — 상단 오버헤드 (/dev/cam_top)
  wrist_left — 왼팔 손목 (/dev/cam_wrist_left)
  wrist_right — 오른팔 손목 (/dev/cam_wrist_right)
```

State/Action 차원: **12** (left 6 + right 6)

## 데이터 수집

LeRobot BiOmxFollower를 사용해 리더-팔로워 텔레오퍼레이션으로 수집.
기존 `physical-ai-repo-2`의 `store_play` 파이프라인 참고.

수집된 데이터는 LeRobot v2 포맷 (`parquet` + `mp4`) 으로 저장된 후
`modality.json`을 `meta/` 에 복사해 GR00T 호환 포맷으로 만든다.

```bash
cp examples/OMX_bimanual/modality.json <your_dataset>/meta/modality.json
```

## 데이터셋 구조

```
<dataset>/
├── meta/
│   ├── modality.json          ← 이 파일 복사
│   ├── info.json
│   └── episodes.jsonl
├── data/
│   └── chunk-000/
│       └── episode_*.parquet  (state: [12], action: [12])
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
  --dataset-path <your_dataset_path> \
  --modality-config-path examples/OMX_bimanual/omx_bimanual_config.py \
  --embodiment-tag NEW_EMBODIMENT \
  --output-dir /tmp/omx_bimanual_finetune
```

VRAM ~25GB 필요. RTX 4090(24GB)는 배치사이즈 낮추거나 gradient checkpointing 활성화.

## 추론 서버 실행

```bash
uv run python gr00t/eval/run_gr00t_server.py \
  --model-path /tmp/omx_bimanual_finetune/checkpoint-10000 \
  --embodiment-tag NEW_EMBODIMENT \
  --modality-config-path examples/OMX_bimanual/omx_bimanual_config.py \
  --denoising-steps 4 \
  --port 8765
```

## 오픈루프 평가

```bash
uv run python gr00t/eval/open_loop_eval.py \
  --dataset-path <your_dataset_path> \
  --embodiment-tag NEW_EMBODIMENT \
  --modality-config-path examples/OMX_bimanual/omx_bimanual_config.py \
  --model-path /tmp/omx_bimanual_finetune/checkpoint-10000 \
  --traj-ids 0 \
  --action-horizon 16 \
  --steps 400
```

## 기존 inference_server.py 교체

`physical-ai-repo-2`의 가게놀이 파이프라인은 `/chunk` HTTP 인터페이스로 추론 서버와 통신한다.
GR00T 추론 서버를 `http://localhost:8765`로 띄우면 `game_smolvla_http.yaml`의
`inference_url` 설정 그대로 연결된다.

```yaml
# game_smolvla_http.yaml (변경 없음)
policy:
  kind: smolvla_http
  inference_url: "http://localhost:8765"
```

단, GR00T 서버의 `/chunk` 인터페이스 포맷이 기존 SmolVLA 서버와 다를 수 있으므로
`runner_entry.py`의 요청 포맷 확인 필요.
