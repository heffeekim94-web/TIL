// Lv2 2강: OpenCR에서 위치 오차를 읽고 P 제어로 속도를 보정한다.
// 기준 하드웨어: XM430-W210-T/R (모델 번호 1030), Protocol 2.0, firmware >= 38, 모터 1개.
#include <Dynamixel2Arduino.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

using namespace ControlTableItem;
Dynamixel2Arduino dxl(Serial3, 84);  // OpenCR DXL 포트 / 방향 제어 핀

const uint8_t DXL_ID = 1;          // 사용자 모터 검색 결과
const uint32_t DXL_BAUD = 1000000;
constexpr float PI_F = 3.14159265358979323846f;
constexpr float RAD_PER_DEG = PI_F / 180.0f;
constexpr float RAD_PER_TICK = 2.0f * PI_F / 4096.0f;
constexpr float RAD_S_PER_VELOCITY_RAW = 0.229f * 2.0f * PI_F / 60.0f;
constexpr float DEFAULT_SPEED_RAD_S = 20.0f * RAD_PER_DEG;
constexpr float MIN_SPEED_DEG_S = 2.0f;
constexpr float MAX_SPEED_DEG_S = 30.0f;
constexpr float MAX_ANGLE_DEG = 90.0f;
constexpr float MIN_POSITION_RAD = -120.0f * RAD_PER_DEG;
constexpr float MAX_POSITION_RAD = 120.0f * RAD_PER_DEG;
constexpr float DEADBAND_RAD = 0.2f * RAD_PER_DEG;
const uint32_t PERIOD_US = 10000;    // 100 Hz 요청 주기; 실제 dt는 로그로 확인
uint32_t run_ms = 60000;  // 시작할 때 입력 각도·속도로 결정한다. 최소 60초.
constexpr float MAX_GAIN = 2.0f;

bool running = false;
bool faulted = false;
float kp = 0.5f;                    // [1/s], 모터 내부 Position P Gain과 다름
float speed_limit_rad_s = DEFAULT_SPEED_RAD_S;
float goal_rad = 90.0f * RAD_PER_DEG;
int32_t origin_ticks = 0;
uint32_t started_ms = 0, last_us = 0, last_log_ms = 0;

constexpr float limitSpeed(float speed, float limit) {
  return speed > limit ? limit : speed < -limit ? -limit : speed;
}

constexpr float feedbackVelocity(float error_rad, float gain, float limit) {
  return (error_rad > -DEADBAND_RAD && error_rad < DEADBAND_RAD)
         ? 0.0f : limitSpeed(gain * error_rad, limit);
}

int32_t velocityToRaw(float speed, float limit) {
  const int32_t raw_limit = static_cast<int32_t>(limit / RAD_S_PER_VELOCITY_RAW);
  return constrain(static_cast<int32_t>(lroundf(speed / RAD_S_PER_VELOCITY_RAW)),
                   -raw_limit, raw_limit);  // 반올림 후에도 입력한 명령 상한을 넘지 않는다.
}

// 빌드할 때 실제 제어 함수의 부호, 영점, 데드밴드, 양방향 포화를 검증한다.
static_assert(feedbackVelocity(0.0f, 1.0f, DEFAULT_SPEED_RAD_S) == 0.0f, "zero error");
static_assert(feedbackVelocity(DEADBAND_RAD / 2.0f, 1.0f, DEFAULT_SPEED_RAD_S) == 0.0f, "deadband");
static_assert(feedbackVelocity(0.1f, 2.0f, DEFAULT_SPEED_RAD_S) == 0.2f, "positive command");
static_assert(feedbackVelocity(-0.1f, 2.0f, DEFAULT_SPEED_RAD_S) == -0.2f, "negative command");
static_assert(feedbackVelocity(1.0f, 2.0f, 0.1f) == 0.1f, "custom positive limit");
static_assert(feedbackVelocity(-1.0f, 2.0f, 0.1f) == -0.1f, "custom negative limit");
static_assert(MAX_ANGLE_DEG * RAD_PER_DEG < MAX_POSITION_RAD &&
              -MAX_ANGLE_DEG * RAD_PER_DEG > MIN_POSITION_RAD, "target range");

constexpr bool validSetting(char key, float value) {
  return key == 'k' ? value > 0 && value <= MAX_GAIN :
         key == 'v' ? value >= MIN_SPEED_DEG_S && value <= MAX_SPEED_DEG_S :
         key == 'a' ? value >= -MAX_ANGLE_DEG && value <= MAX_ANGLE_DEG : false;
}

bool parseSettingCommand(const char *line, float &value) {
  if (line[0] != 'k' && line[0] != 'v' && line[0] != 'a') return false;
  char *end;
  value = strtof(line + 1, &end);
  if (end == line + 1) return false;
  while (isspace(static_cast<unsigned char>(*end))) ++end;
  return *end == '\0' && isfinite(value) && validSetting(line[0], value);
}

bool parseRunCommand(const char *line, float &gain, float &speed_deg_s, float &angle_deg) {
  if (line[0] != 's' || !isspace(static_cast<unsigned char>(line[1]))) return false;
  const char *cursor = line + 1;
  float values[3];
  for (uint8_t i = 0; i < 3; ++i) {
    char *end;
    values[i] = strtof(cursor, &end);
    if (end == cursor || !isfinite(values[i])) return false;
    if (*end != '\0' && !isspace(static_cast<unsigned char>(*end))) return false;
    cursor = end;
  }
  while (isspace(static_cast<unsigned char>(*cursor))) ++cursor;
  if (*cursor != '\0' || !validSetting('k', values[0]) ||
      !validSetting('v', values[1]) || !validSetting('a', values[2])) return false;
  gain = values[0]; speed_deg_s = values[1]; angle_deg = values[2];
  return true;  // 세 값 모두 유효할 때에만 적용한다.
}

bool settingsSelfCheck() {
  float value, gain, speed, angle;
  return parseSettingCommand("k 0.1", value) && value == 0.1f &&
         parseSettingCommand("v 2", value) && value == 2 &&
         parseSettingCommand("a -90", value) && value == -90 &&
         !parseSettingCommand("k nan", value) && !parseSettingCommand("k inf", value) &&
         !parseSettingCommand("k 0", value) && !parseSettingCommand("k -1", value) &&
         !parseSettingCommand("k 99", value) && !parseSettingCommand("k 0.1 junk", value) &&
         !parseSettingCommand("v 0", value) && !parseSettingCommand("v 31", value) &&
         !parseSettingCommand("a 91", value) && !parseSettingCommand("k", value) &&
         parseRunCommand("s 0.1 20 -45", gain, speed, angle) &&
         gain == 0.1f && speed == 20 && angle == -45 &&
         !parseRunCommand("s 0.1 20", gain, speed, angle) &&
         !parseRunCommand("s 0.1 20 90 extra", gain, speed, angle) &&
         !parseRunCommand("s 0.1 inf 90", gain, speed, angle) &&
         !parseRunCommand("s 0.1 20 91", gain, speed, angle);
}

void printSettings() {
  Serial.print("SET Kp="); Serial.print(kp, 4);
  Serial.print(", speed_limit_deg_s="); Serial.print(speed_limit_rad_s / RAD_PER_DEG, 3);
  Serial.print(", angle_deg="); Serial.println(goal_rad / RAD_PER_DEG, 3);
}

void stopRun(const char *reason, bool fault) {
  running = false;
  // 읽기 실패를 위치 0으로 해석하지 않는다. 정지 패킷은 각각 한 번 보낸다.
  const bool zero_ok = dxl.setGoalVelocity(DXL_ID, 0, UNIT_RPM);
  const bool off_ok = dxl.torqueOff(DXL_ID);
  faulted = fault || !zero_ok || !off_ok;
  if (faulted) {
    // OpenCR에서 전원을 공급받는 DXL 포트를 차단한다. RESET 전까지 재시작 금지.
    digitalWrite(BDPIN_DXL_PWR_EN, LOW);
  }
  Serial.print(faulted ? "FAULT (RESET required): " : "STOP: ");
  Serial.println(reason);
}

bool requireOk(bool ok, const char *reason) {
  if (!ok) {
    const auto lib_error = dxl.getLastLibErrCode();
    const auto status_error = dxl.getLastStatusPacketError();
    stopRun(reason, true);  // 정지 통신이 원래 오류를 덮어쓰기 전에 위에서 보존한다.
    Serial.print("DXL lib_error="); Serial.print(lib_error);
    Serial.print(", status_error="); Serial.println(status_error);
  }
  return ok;
}

bool readItem(uint8_t item, int32_t &value) {
  value = dxl.readControlTableItem(item, DXL_ID, 10);  // timeout [ms]
  return requireOk(dxl.getLastLibErrCode() == DXL_LIB_OK &&
                   dxl.getLastStatusPacketError() == 0, "DXL read failed");
}

void startRun() {
  if (running || faulted) return;
  // watchdog 오류를 지우고, 남아 있는 속도 명령을 0으로 만든 뒤 토크를 켠다.
  if (!requireOk(dxl.writeControlTableItem(BUS_WATCHDOG, DXL_ID, 0), "watchdog clear") ||
      !requireOk(dxl.setGoalVelocity(DXL_ID, 0, UNIT_RPM), "zero velocity") ||
      !requireOk(dxl.torqueOn(DXL_ID), "torque on") ||
      !requireOk(dxl.writeControlTableItem(BUS_WATCHDOG, DXL_ID, 5), "watchdog set")) return;
  if (!readItem(PRESENT_POSITION, origin_ticks)) return;
  const uint32_t estimated_ms = 12000UL +
      static_cast<uint32_t>(ceilf(3000.0f * fabsf(goal_rad) / speed_limit_rad_s));
  run_ms = estimated_ms > 60000UL ? estimated_ms : 60000UL;
  started_ms = millis();
  last_log_ms = started_ms;
  last_us = micros();
  running = true;
  Serial.println("START: current position = 0 deg.");
  printSettings();
  Serial.print("Run timeout [s]: "); Serial.println(run_ms / 1000.0f, 1);
}

void readCommands() {
  static char line[64];
  static uint8_t used = 0;
  static bool overflow = false;
  for (uint8_t n = 0; n < 32 && Serial.available(); ++n) {
    const char c = Serial.read();
    if (c == 'x') {  // 정지는 줄바꿈을 기다리지 않는다.
      used = 0; overflow = false;
      if (running) stopRun("user", false);
      continue;
    }
    if (c == '\r' || c == '\n') {
      line[used] = '\0';
      float value, gain, speed, angle;
      if (overflow) Serial.println("Command too long; discarded.");
      else if (used && faulted) Serial.println("FAULT: RESET required.");
      else if (used && running) Serial.println("Running: send x before changing settings.");
      else if (used && strcmp(line, "s") == 0) startRun();
      else if (used && parseRunCommand(line, gain, speed, angle)) {
        kp = gain; speed_limit_rad_s = speed * RAD_PER_DEG; goal_rad = angle * RAD_PER_DEG;
        startRun();
      } else if (used && parseSettingCommand(line, value)) {
        if (line[0] == 'k') kp = value;
        if (line[0] == 'v') speed_limit_rad_s = value * RAD_PER_DEG;
        if (line[0] == 'a') goal_rad = value * RAD_PER_DEG;
        printSettings();
      } else if (used) {
        Serial.print("Invalid setting. Kp (0, "); Serial.print(MAX_GAIN, 4);
        Serial.println("], speed 2..30 deg/s, angle -90..90 deg. Use k/v/a or s <gain> <speed> <angle>.");
      }
      used = 0; overflow = false;
    } else if (!overflow) {
      if (used < sizeof(line) - 1) line[used++] = c;
      else overflow = true;
    }
  }
}

void setup() {
  Serial.begin(115200);
  dxl.begin(DXL_BAUD);  // 라이브러리가 OpenCR의 DXL 전원도 켠다.
  dxl.setPortProtocolVersion(2.0);
  if (!requireOk(dxl.ping(DXL_ID), "ping: check ID/baud/power") ||
      !requireOk(dxl.getModelNumber(DXL_ID) == XM430_W210, "requires XM430-W210") ||
      !requireOk(dxl.torqueOff(DXL_ID), "torque off")) return;
  if (!requireOk(settingsSelfCheck(), "settings parser self-check")) return;
  int32_t value;
  if (!readItem(FIRMWARE_VERSION, value) ||
      !requireOk(value >= 38, "requires firmware >= 38")) return;
  if (!readItem(DRIVE_MODE, value) ||
      !requireOk((value & 4) == 0, "use velocity-based profile: Drive Mode bit 2 = 0")) return;
  if (!readItem(OPERATING_MODE, value)) return;
  if (value != OP_VELOCITY &&
      !requireOk(dxl.setOperatingMode(DXL_ID, OP_VELOCITY), "velocity mode")) return;
  // 매 실험에서 가속 프로파일을 동일하게 유지한다. XM430 raw 단위, 튜닝 가능.
  if (!requireOk(dxl.writeControlTableItem(PROFILE_ACCELERATION, DXL_ID, 5), "acceleration")) return;
  Serial.println("READY: s <gain> <speed_deg_s> <angle_deg>; k/v/a set; s start; x stop. Newline.");
  Serial.print("Max Kp: "); Serial.println(MAX_GAIN, 4);
  printSettings();
}

void loop() {
  readCommands();
  if (!running) return;
  const uint32_t now_us = micros();
  const uint32_t dt_us = now_us - last_us;  // unsigned 차분: micros() wrap 대응
  if (dt_us < PERIOD_US) return;
  if (dt_us > 5 * PERIOD_US) { stopRun("control loop late", true); return; }
  last_us = now_us;
  const uint32_t elapsed_ms = millis() - started_ms;
  if (elapsed_ms >= run_ms) { stopRun("time limit reached; torque off", false); return; }

  int32_t ticks;
  if (!readItem(PRESENT_POSITION, ticks)) return;
  // 32비트 signed 연속 위치를 차분한다. 0/360도 경계에서 각도를 접지 않는다.
  const float position_rad = static_cast<float>(static_cast<int64_t>(ticks) - origin_ticks)
                             * RAD_PER_TICK;
  if (position_rad < MIN_POSITION_RAD || position_rad > MAX_POSITION_RAD) {
    stopRun("travel limit", true); return;
  }

  const float target_rad = elapsed_ms < 2000 ? 0.0f : goal_rad;
  const float error_rad = target_rad - position_rad;
  const float speed_rad_s = feedbackVelocity(error_rad, kp, speed_limit_rad_s);
  const int32_t velocity_raw = velocityToRaw(speed_rad_s, speed_limit_rad_s);
  if (!requireOk(dxl.setGoalVelocity(DXL_ID, velocity_raw, UNIT_RAW),
                 "velocity write failed")) return;

  // ponytail: 동기식 단일 모터 폴링. 다축/더 빠른 주기가 필요하면 Sync Read/Write로 변경.
  if (millis() - last_log_ms >= 100 && Serial) {  // 10 Hz 로그, Arduino Serial Plotter
    last_log_ms = millis();
    Serial.print("target_deg:"); Serial.print(target_rad / RAD_PER_DEG, 3);
    Serial.print("\tposition_deg:"); Serial.print(position_rad / RAD_PER_DEG, 3);
    Serial.print("\terror_deg:"); Serial.print(error_rad / RAD_PER_DEG, 3);
    Serial.print("\tp_deg_s:"); Serial.print(kp * error_rad / RAD_PER_DEG, 3);
    Serial.print("\tu_deg_s:"); Serial.print(velocity_raw * RAD_S_PER_VELOCITY_RAW / RAD_PER_DEG, 3);
    Serial.print("\tv_limit_deg_s:"); Serial.print(speed_limit_rad_s / RAD_PER_DEG, 3);
    Serial.print("\tdt_ms:"); Serial.print(dt_us / 1000.0f, 3);
    Serial.print("\tkp:"); Serial.print(kp, 4);
    Serial.print("\tt_s:"); Serial.println(elapsed_ms / 1000.0f, 3);
  }
}
