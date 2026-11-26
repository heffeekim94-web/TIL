#!/bin/bash
# 신호등 펌웨어 빌드 + 업로드 (빌드가 실패하면 업로드하지 않고 멈춤)
# 사용: bash ~/pa-opencr-build/build_sign.sh
set -e
cd ~/pa-opencr-build
rm -rf ~/.cache/arduino/sketches            # 예전 빌드 캐시 지우기
echo "=== 빌드 ==="
./bin/arduino-cli --config-file arduino-cli.yaml compile --clean --fqbn ROBOTIS:OpenCR:OpenCR \
  --output-dir output sketches/sign_tower_rc
echo "=== 새 펌웨어 파일 (시각이 지금이어야 함) ==="
ls -l --time-style=+%m/%d_%H:%M:%S output/sign_tower_rc.ino.bin
PORT=$(ls /dev/serial/by-id/*OpenCR* 2>/dev/null | head -1)
if [ -z "$PORT" ]; then echo "OpenCR USB 가 안 보임 → USB 연결 확인"; exit 1; fi
echo "=== 업로드: $PORT ==="
./uploader-src/arduino/opencr_develop/opencr_ld/opencr_ld "$PORT" 115200 output/sign_tower_rc.ino.bin 1
echo "=== 끝: 6 으로 퍽 구성을 다시 입력하세요 ==="
