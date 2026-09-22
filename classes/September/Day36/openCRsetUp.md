현재 보고 계신 [OpenCR 빌드 업로드 가이드](https://github.com/SpartaPA/physicalai-lv2-assignments/blob/main/모듈1_임베디드제어기초/OpenCR_빌드_업로드_가이드.md?utm_source=gemini) 문서의 단계별 코드들이 각각 어떤 의미와 역할을 하는지 순서대로 설명해 드리겠습니다.

---

### 1. 환경과 필수 도구 준비

```bash
hostname
cat /etc/os-release
uname -m
df -h "$HOME"

```

* **의미:** 현재 접속한 라즈베리파이 시스템의 기본 정보(호스트 이름, OS 버전, CPU 아키텍처, 디스크 여유 공간)를 확인하는 명령어들입니다. ARM64 환경과 5GB 이상의 여유 공간이 있는지 확인합니다.

```bash
export BASE="$HOME/pa-opencr-build"
set -o pipefail
mkdir -p "$BASE"/{bin,downloads,data,user,sketches,output}

```

* **의미:** 작업에 필요한 기본 디렉토리 경로를 환경 변수(`BASE`)로 지정하고, 빌드와 설치에 필요한 하위 폴더(`bin`, `downloads`, `data`, `user`, `sketches`, `output`)들을 한 번에 생성합니다.

```bash
sudo apt update
sudo apt install -y build-essential curl git python3-serial \
  gcc-arm-none-eabi libnewlib-arm-none-eabi \
  libstdc++-arm-none-eabi-newlib usbutils file

```

* **의미:** 시스템 패키지 목록을 최신화하고, 컴파일러(`build-essential`, `gcc-arm-none-eabi` 등)와 유틸리티 도구들을 설치합니다.

```bash
sudo usermod -aG dialout "$USER"

```

* **의미:** 현재 사용자를 `dialout` 그룹에 추가하여, OpenCR 보드가 연결되는 시리얼 포트(`/dev/ttyACM0` 등)에 접근할 수 있는 권한을 부여합니다.

---

### 2. Arduino CLI 1.5.1 설치

```bash
cd "$BASE/downloads"
VER=1.5.1
ASSET="arduino-cli_${VER}_Linux_ARM64.tar.gz"
RELEASE="https://github.com/arduino/arduino-cli/releases/download"
curl -fL -o "\(ASSET" "\)RELEASE/v\(VER/\)ASSET"
curl -fL -o checksums.txt "\(RELEASE/v\)VER/${VER}-checksums.txt"
grep "$ASSET\$" checksums.txt | sha256sum -c -

```

* **의미:** 아두이노 명령줄 도구(Arduino CLI) ARM64 버전을 다운로드하고, 무결성 검증을 위해 체크섬(SHA256)을 비교합니다.

```bash
tar -xzf "\(ASSET" -C "\)BASE/bin" arduino-cli
file "$BASE/bin/arduino-cli"
"$BASE/bin/arduino-cli" version

```

* **의미:** 다운로드한 압축 파일을 해제하여 `$BASE/bin` 폴더에 넣고, 정상적으로 실행 가능한 ARM64 파일인지 및 버전이 맞는지 확인합니다.

---

### 3. OpenCR 코어 1.5.3 설치

```bash
cd "$BASE/downloads"
CORE_URL="https://github.com/ROBOTIS-GIT/OpenCR/releases/download"
curl -fL -o opencr.tar.bz2 "$CORE_URL/1.5.3/opencr.tar.bz2"
CORE_SHA=418656e5e6d99d45d187ffdb28dece0f450c6707da3f6db56769f3ecafdc413c
printf '%s  opencr.tar.bz2\n' "$CORE_SHA" | sha256sum -c -

```

* **의미:** ROBOTIS OpenCR 보드 지원 코어 파일을 다운로드하고 SHA256 해시값으로 파일 변조 여부를 검증합니다.

```bash
mkdir -p "$BASE/user/hardware/ROBOTIS/OpenCR"
tar -xf opencr.tar.bz2 -C "$BASE/user/hardware/ROBOTIS/OpenCR" --strip-components=1

```

* **의미:** 검증된 OpenCR 코어 아카이브를 아두이노 사용자 하드웨어 경로(`$BASE/user/hardware/ROBOTIS/OpenCR`)에 해제합니다.

---

### 4. CLI 설정과 라이브러리 설치

```bash
cat > "$BASE/arduino-cli.yaml" << EOF
directories:
  data: $BASE/data
  downloads: $BASE/downloads
  user: $BASE/user
EOF
"\(BASE/bin/arduino-cli" --config-file "\)BASE/arduino-cli.yaml" core update-index
"\(BASE/bin/arduino-cli" --config-file "\)BASE/arduino-cli.yaml" board listall

```

* **의미:** Arduino CLI가 참조할 경로 설정 파일(`arduino-cli.yaml`)을 생성하고, 인덱스를 업데이트한 뒤 사용 가능한 보드 목록을 조회합니다.

```bash
mkdir -p "$BASE/user/libraries"
git clone https://github.com/ROBOTIS-GIT/Dynamixel2Arduino.git "$BASE/user/libraries/Dynamixel2Arduino"
git -C "$BASE/user/libraries/Dynamixel2Arduino" checkout cfbbaf79581ecfcdec952a87916572885453f4ab

```

* **의미:** 다이나믹셀 제어를 위한 `Dynamixel2Arduino` 라이브러리를 클론(Clone)하고, 호환성이 검증된 특정 커밋 버전으로 체크아웃합니다.

---

### 5. Ubuntu 컴파일러 연결

```bash
cat > "$BASE/user/hardware/ROBOTIS/OpenCR/platform.local.txt" << 'EOF'
compiler.path=/usr/bin/
EOF
arm-none-eabi-g++ --version

```

* **의미:** OpenCR 빌드 시 기본 내장 컴파일러 대신 라즈베리파이에 설치된 Ubuntu 시스템 컴파일러(`/usr/bin/`의 `arm-none-eabi-g++`)를 사용하도록 설정 파일을 작성합니다.

---

### 6. 과제 소스 준비와 빌드

```bash
git clone https://github.com/SpartaPA/physicalai-lv2-assignments.git "$BASE/repo"
SOURCE=\((find "\)BASE/repo" -type d -name opencr_position_p -print -quit)
test -n "\(SOURCE" && test -f "\)SOURCE/opencr_position_p.ino"

```

* **의미:** 과제 레포지토리를 클론한 뒤, 컴파일할 대상 소스 폴더(`opencr_position_p`)가 정상적으로 존재하는지 확인합니다.

```bash
cp -r "\(SOURCE" "\)BASE/sketches/"
set -o pipefail
"\(BASE/bin/arduino-cli" --config-file "\)BASE/arduino-cli.yaml" \
  compile --fqbn ROBOTIS:OpenCR:OpenCR --jobs 1 \
  --output-dir "\(BASE/output" "\)BASE/sketches/opencr_position_p" 2>&1 | tee "$BASE/build.log"

```

* **의미:** 소스 코드를 작업 스케치 폴더로 복사하고, Arduino CLI를 이용해 OpenCR 보드(`ROBOTIS:OpenCR:OpenCR`)용으로 컴파일을 수행합니다. 결과물은 `$BASE/output`에 저장되며 로그는 기록됩니다.

```bash
test -s "$BASE/output/opencr_position_p.ino.bin"
file "$BASE/output/opencr_position_p.ino.elf"
arm-none-eabi-size "$BASE/output/opencr_position_p.ino.elf"
sha256sum "$BASE/output/opencr_position_p.ino.bin"

```

* **의미:** 빌드가 성공적으로 끝나 바이너리 파일(`.bin`)과 ELF 파일(`.elf`)이 생성되었는지 확인하고, 파일 크기와 해시값을 점검합니다.

---

### 7. 라즈베리파이용 업로더 빌드

```bash
mkdir "$BASE/uploader-src"
cd "$BASE/uploader-src"
git init
git remote add origin https://github.com/ROBOTIS-GIT/OpenCR.git
git sparse-checkout init --cone
git sparse-checkout set arduino/opencr_develop/opencr_ld
git fetch --depth 1 --filter=blob:none origin 68ec75d8a400949580ecf263e0105ea9743b878e
git checkout --detach FETCH_HEAD
make -C arduino/opencr_develop/opencr_ld
file arduino/opencr_develop/opencr_ld/opencr_ld

```

* **의미:** OpenCR 공식 저장소에서 펌웨어 업로드에 필요한 툴(`opencr_ld`) 소스만 골라서(`sparse-checkout`) 다운로드한 뒤, 라즈베리파이(ARM64) 환경에 맞게 직접 빌드하여 실행 파일을 생성합니다.

---

### 8. OpenCR 포트 확인과 업로드

```bash
lsusb
ls -l /dev/ttyACM*

```

* **의미:** USB로 연결된 OpenCR 장치의 인식 상태를 확인하고, 시리얼 포트 이름(`/dev/ttyACM0` 등)을 파악합니다.

```bash
PORT=/dev/ttyACM0
udevadm info --query=property --name="$PORT"
test -r "\(PORT" && test -w "\)PORT" && echo 'Port access OK'

```

* **의미:** 지정한 포트의 상세 속성을 확인하고, 읽기/쓰기 권한이 정상적으로 부여되었는지 테스트합니다.

```bash
Uploader="$BASE/uploader-src/arduino/opencr_develop/opencr_ld/opencr_ld"
set -o pipefail
"\(Uploader" "\)PORT" 115200 "\(BASE/output/opencr_position_p.ino.bin" 1 2>&1 | tee "\)BASE/upload.log"

```

* **의미:** 앞서 직접 빌드한 펌웨어 바이너리(`.bin`) 파일을 지정한 시리얼 포트와 통신 속도(115200)로 OpenCR 보드에 전송하여 업로드합니다.

---

### 9. 업로드 이후 준비 상태 확인

```bash
ls -l /dev/ttyACM*
PORT=/dev/ttyACM0
python3 -m serial.tools.miniterm "$PORT" 115200 --eol LF

```

* **의미:** 업로드 완료 후 시리얼 모니터 프로그램을 실행하여 OpenCR 보드가 보내는 초기 메시지(`READY` 등)를 확인합니다. (종료할 때는 `Ctrl + ]` 입력)