// sign_tower_rc.ino  (2026-11-13 최종판)
// 신호등 OpenCR + ROBOTIS RC-100 리모컨 (수신기 = OpenCR UART 포트, Serial2)
// 릴레이: 핀 5 = 빨강, 6 = 노랑, 7 = 초록 (LOW = 켜짐, HIGH = 꺼짐)
// 전원을 켜면 모두 꺼진 채로 기다림
//
// ---------- 리모컨 ----------
//   6 : 퍽 구성 입력 시작 (노란불 계속 켜짐)
//       1 = 빨강 직육면체, 2 = 빨강 원기둥, 3 = 초록 직육면체, 4 = 초록 원기둥
//       누른 횟수 = 개수 (누를 때마다 초록불 짧게)
//       6 을 다시 누르면 입력 끝 → 빨간불 빠르게 2번 = 저장 완료 (전원을 꺼도 남음)
//                                  빨간불 2초 = 실패, 예전 구성 그대로 (합이 12가 아니거나 풀 수 있는 신호 없음)
//   5 : 입력 중 실수 → 개수를 0 으로 하고 처음부터 다시 입력 (빨간불 짧게 1번, 노란불은 계속)
//   D : 저장된 구성 확인. 1 → 2 → 3 → 4 순서로 개수만큼 0.5초 켜짐 + 0.5초 꺼짐
//       빨강 직육면체 · 빨강 원기둥 = 빨간불, 초록 직육면체 · 초록 원기둥 = 초록불
//       종류 사이에는 노란불 1초 (0개인 종류는 노란불만)
//   U : 저장된 구성으로 mission.pdf v5 에 맞는 신호를 새로 랜덤으로 만들어 무한 반복
//       한 세트 = 12번 (1초 켜짐 + 1초 꺼짐), 12번째 뒤 3초 꺼짐, 그다음 같은 세트 반복
//       반복 중에 U 를 다시 누르면 새 랜덤 세트로 바꿔서 반복
//       R = 빨간 퍽만, G = 초록 퍽만, Y = 색은 섞여도 되고 모양은 하나로 통일, R·Y·G 각 1~6 · 합 12
//       풀 수 있는 신호가 없으면 빨간불 2초
//   R : 방금 전 랜덤 세트를 처음부터 다시 무한 반복 (3초 쉬고 반복). 전원을 꺼도 기억
//       아직 만든 세트가 없으면 U 와 같음
//   L : 모두 끄기. 입력 중(노란불)이어도 입력을 버리고 끔 (11/13)
//   입력 중(노란불)에는 1 2 3 4 5 6 과 L 만 받음
//
// 잘못된 신호 막기 (11/13): 리모컨을 끌 때 수신기가 이상한 값을 보내서 혼자 켜지던 문제
//   - 버튼 하나만 눌린 값(정상 버튼 10개 중 한 비트)만 받음, 여러 비트가 섞인 값은 무시
//   - 같은 값이 연속 CONFIRM_PACKETS 번 오거나, 그 값 뒤에 손 뗌(0) 이 오면 눌린 것으로 봄 (11/16)
//     (리모컨이 누를 때 한 번만 보내도 손을 떼면 인정. 끌 때 튀는 값 하나는 손 뗌이 안 와서 무시)
//
// 노트북 USB 시리얼(115200)을 열어 두면 U · R 때 정답(색 순서 12개, R/Y/G 횟수)을 찍음. ? = 현재 구성
// (노트북이 없으면 아무것도 안 찍음 → 깜빡임 시간에 영향 없음)

#include <RC100.h>
#include <EEPROM.h>

// ===================== 정의 (함수보다 먼저) =====================
const int RELAY_PIN[3] = {5, 6, 7};       // 0 빨강, 1 노랑, 2 초록
const int RED = 0, YELLOW = 1, GREEN = 2, NONE = -1;
const char COLOR_CHAR[3] = {'R', 'Y', 'G'};

const int SIGNAL_COUNT = 12;

// 퍽 종류: 0 빨강 직육면체, 1 빨강 원기둥, 2 초록 직육면체, 3 초록 원기둥
const char* PUCK_NAME[4] = {"red box", "red cyl", "green box", "green cyl"};
const int PUCK_COLOR[4] = {RED, RED, GREEN, GREEN};

// EEPROM 위치
const int EE_PUCK_MAGIC = 0;              // 0 = 확인 값, 1~4 = 개수
const int EE_SEQ_MAGIC  = 10;             // 10 = 확인 값, 11~22 = 마지막 세트
const uint8_t PUCK_MAGIC = 0xA8;
const uint8_t SEQ_MAGIC  = 0x5D;

struct Combo { int r, y, g; bool yBox, yCyl; };   // 풀 수 있는 (R, Y, G) 횟수
struct Step  { int color; unsigned int onMs; unsigned int offMs; };

const int CONFIRM_PACKETS = 2;            // 같은 값이 몇 번 연속 와야 버튼으로 인정할지
const uint16_t VALID_BUTTONS = 0x03FF;    // U D L R 1 2 3 4 5 6

// ===================== 상태 =====================
RC100 rc;
uint16_t rcCandidate = 0;                 // 지금 들어오고 있는 값
int rcSameCount = 0;                      // 그 값이 연속으로 온 횟수
bool rcHandled = false;                   // 이번 누름을 이미 처리했는지

int pucks[4] = {6, 3, 1, 2};              // 저장된 값이 없을 때 기본값
Combo combos[36];
int nCombos = 0;

bool inputMode = false;
int inputPucks[4] = {0, 0, 0, 0};

int seq[SIGNAL_COUNT];                    // 마지막 랜덤 세트 (0 빨강, 1 노랑, 2 초록)
bool haveSeq = false;

// 깜빡임 재생기: steps 를 차례로 켜고 끔. repeat 이면 끝나고 처음부터
Step steps[40];
int nSteps = 0;
int stepIdx = 0;
bool stepLit = false;
bool playing = false;
bool repeatPlay = false;
unsigned long stepStart = 0;

// ===================== 시리얼 출력 (노트북이 열려 있을 때만) =====================
void logText(const char* s)   { if (Serial) Serial.print(s); }
void logChar(char c)          { if (Serial) Serial.print(c); }
void logNum(int v)            { if (Serial) Serial.print(v); }
void logLine(const char* s)   { if (Serial) Serial.println(s); }

// ===================== 불 =====================
void allOff() {
  for (int i = 0; i < 3; i++) digitalWrite(RELAY_PIN[i], HIGH);
}

void showLight(int color) {               // RED / YELLOW / GREEN, 그 외 = 모두 끄기
  allOff();
  if (color >= 0 && color < 3) digitalWrite(RELAY_PIN[color], LOW);
}

// 짧은 알림 (입력 확인용, 기다리며 깜빡임)
void blinkWait(int color, int times, unsigned long onMs, unsigned long offMs) {
  for (int i = 0; i < times; i++) {
    showLight(color);
    delay(onMs);
    allOff();
    delay(offMs);
  }
}

// ===================== 재생기 =====================
void stopPlay() {
  playing = false;
  allOff();
}

void startPlay(bool repeat) {
  if (nSteps == 0) { stopPlay(); return; }
  repeatPlay = repeat;
  playing = true;
  stepIdx = 0;
  stepLit = true;
  showLight(steps[0].color);
  stepStart = millis();
}

void updatePlay() {
  if (!playing) return;
  unsigned long now = millis();
  const Step& s = steps[stepIdx];
  if (stepLit) {
    if (now - stepStart >= s.onMs) {
      allOff();
      stepLit = false;
      stepStart = now;
    }
  } else if (now - stepStart >= s.offMs) {
    stepIdx++;
    if (stepIdx >= nSteps) {
      if (!repeatPlay) { stopPlay(); return; }
      stepIdx = 0;
    }
    showLight(steps[stepIdx].color);
    stepLit = true;
    stepStart = now;
  }
}

void addStep(int color, unsigned int onMs, unsigned int offMs) {
  if (nSteps >= 40) return;
  steps[nSteps].color = color;
  steps[nSteps].onMs = onMs;
  steps[nSteps].offMs = offMs;
  nSteps++;
}

// ===================== 퍽 구성 → 풀 수 있는 신호 =====================
// Y 는 한 모양(직육면체 또는 원기둥)으로 통일, 색은 섞어도 됨. 남은 빨강 = R, 남은 초록 = G
int computeCombos(const int p[4], Combo* out) {
  int red = p[0] + p[1], green = p[2] + p[3];
  int n = 0;
  if (red + green != SIGNAL_COUNT) return 0;
  for (int r = 1; r <= 6; r++) {
    for (int g = 1; g <= 6; g++) {
      int y = SIGNAL_COUNT - r - g;
      if (y < 1 || y > 6) continue;
      int yr = red - r, yg = green - g;    // Y 로 보낼 빨강 · 초록 개수
      if (yr < 0 || yg < 0) continue;
      bool box = (yr <= p[0] && yg <= p[2]);
      bool cyl = (yr <= p[1] && yg <= p[3]);
      if (!box && !cyl) continue;
      if (out) {
        out[n].r = r; out[n].y = y; out[n].g = g;
        out[n].yBox = box; out[n].yCyl = cyl;
      }
      n++;
    }
  }
  return n;
}

void printPucks() {
  logText("pucks =");
  for (int i = 0; i < 4; i++) { logText(" "); logText(PUCK_NAME[i]); logText(" "); logNum(pucks[i]); }
  logText("\npossible (R-Y-G) =");
  for (int k = 0; k < nCombos; k++) {
    logText(" "); logNum(combos[k].r); logText("-"); logNum(combos[k].y); logText("-"); logNum(combos[k].g);
  }
  logText("\n");
}

void printSequence() {
  int cnt[3] = {0, 0, 0};
  logText("signal = ");
  for (int i = 0; i < SIGNAL_COUNT; i++) {
    logChar(COLOR_CHAR[seq[i]]);
    logText(i < SIGNAL_COUNT - 1 ? " " : "\n");
    cnt[seq[i]]++;
  }
  logText("count  = R"); logNum(cnt[0]); logText(" Y"); logNum(cnt[1]); logText(" G"); logNum(cnt[2]); logText("\n");
  for (int k = 0; k < nCombos; k++) {
    if (combos[k].r != cnt[0] || combos[k].y != cnt[1] || combos[k].g != cnt[2]) continue;
    logText("Y = red "); logNum(pucks[0] + pucks[1] - combos[k].r);
    logText(" + green "); logNum(pucks[2] + pucks[3] - combos[k].g);
    logText(", shape = ");
    logLine(combos[k].yBox && combos[k].yCyl ? "box or cylinder" : (combos[k].yBox ? "box" : "cylinder"));
  }
}

void loadSaved() {
  if (EEPROM.read(EE_PUCK_MAGIC) == PUCK_MAGIC) {
    for (int i = 0; i < 4; i++) pucks[i] = EEPROM.read(EE_PUCK_MAGIC + 1 + i);
  }
  nCombos = computeCombos(pucks, combos);
  haveSeq = false;
  if (EEPROM.read(EE_SEQ_MAGIC) == SEQ_MAGIC) {
    haveSeq = true;
    for (int i = 0; i < SIGNAL_COUNT; i++) {
      int v = EEPROM.read(EE_SEQ_MAGIC + 1 + i);
      if (v > 2) { haveSeq = false; break; }
      seq[i] = v;
    }
  }
}

// ===================== 신호 (U · R) =====================
bool makeRandomSet() {
  if (nCombos == 0) return false;
  randomSeed(micros());
  const Combo& c = combos[random(nCombos)];
  int n = 0;
  for (int i = 0; i < c.r; i++) seq[n++] = RED;
  for (int i = 0; i < c.y; i++) seq[n++] = YELLOW;
  for (int i = 0; i < c.g; i++) seq[n++] = GREEN;
  for (int i = SIGNAL_COUNT - 1; i > 0; i--) {     // 섞기 (Fisher-Yates)
    int j = random(i + 1);
    int t = seq[i]; seq[i] = seq[j]; seq[j] = t;
  }
  for (int i = 0; i < SIGNAL_COUNT; i++) EEPROM.update(EE_SEQ_MAGIC + 1 + i, (uint8_t)seq[i]);
  EEPROM.update(EE_SEQ_MAGIC, SEQ_MAGIC);
  haveSeq = true;
  return true;
}

// newSet = true (U) 새 랜덤 세트, false (R) 마지막 세트
void playSignal(bool newSet) {
  stopPlay();
  if (newSet || !haveSeq) {
    if (!makeRandomSet()) {
      logLine("no possible signal for these pucks");
      printPucks();
      blinkWait(RED, 1, 2000, 300);
      return;
    }
  }
  logLine(newSet ? "U: new signal (repeat)" : "R: last signal (repeat)");
  printSequence();                         // 기록을 먼저 찍고 깜빡임 시작
  nSteps = 0;
  for (int i = 0; i < SIGNAL_COUNT; i++) {
    addStep(seq[i], 1000, (i < SIGNAL_COUNT - 1) ? 1000 : 3000);   // 12번째 뒤 3초 꺼짐
  }
  startPlay(true);
}

// ===================== 구성 확인 (D) =====================
void showPucks() {
  stopPlay();
  nSteps = 0;
  for (int k = 0; k < 4; k++) {
    for (int i = 0; i < pucks[k]; i++) addStep(PUCK_COLOR[k], 500, 500);
    if (k < 3) addStep(YELLOW, 1000, 500);          // 종류 사이 노란불
  }
  printPucks();
  startPlay(false);
}

// ===================== 구성 입력 (6) =====================
void startInput() {
  stopPlay();
  inputMode = true;
  for (int i = 0; i < 4; i++) inputPucks[i] = 0;
  showLight(YELLOW);
  logLine("input start: 1 red box, 2 red cyl, 3 green box, 4 green cyl, 5 restart, 6 done");
}

void addInput(int k) {
  inputPucks[k]++;
  logText(PUCK_NAME[k]); logText(" = "); logNum(inputPucks[k]); logText("\n");
  allOff();
  blinkWait(GREEN, 1, 120, 60);
  showLight(YELLOW);
}

void restartInput() {
  for (int i = 0; i < 4; i++) inputPucks[i] = 0;
  logLine("input restart");
  allOff();
  blinkWait(RED, 1, 300, 100);
  showLight(YELLOW);
}

void finishInput() {
  inputMode = false;
  allOff();
  delay(300);
  logText("input = "); for (int i = 0; i < 4; i++) { logNum(inputPucks[i]); logText(" "); } logText("\n");
  if (computeCombos(inputPucks, 0) == 0) {
    logLine("input error (total must be 12 and a signal must be possible) -> kept old pucks");
    blinkWait(RED, 1, 2000, 300);
    return;
  }
  for (int i = 0; i < 4; i++) {
    pucks[i] = inputPucks[i];
    EEPROM.update(EE_PUCK_MAGIC + 1 + i, (uint8_t)pucks[i]);
  }
  EEPROM.update(EE_PUCK_MAGIC, PUCK_MAGIC);
  EEPROM.update(EE_SEQ_MAGIC, 0);          // 구성이 바뀌면 예전 세트는 버림
  haveSeq = false;
  nCombos = computeCombos(pucks, combos);
  logLine("input saved");
  printPucks();
  blinkWait(RED, 2, 150, 150);             // 빨강 빠르게 2번 = 저장 완료
}

// ===================== 버튼 =====================
void turnAllOff() {
  if (inputMode) logLine("input cancelled");
  inputMode = false;
  stopPlay();
  allOff();
  logLine("off");
}

void handleButton(uint16_t pressed) {
  if (pressed & RC100_BTN_L) { turnAllOff(); return; }   // L 은 언제나 모두 끄기
  if (inputMode) {
    if (pressed & RC100_BTN_6)      finishInput();
    else if (pressed & RC100_BTN_1) addInput(0);
    else if (pressed & RC100_BTN_2) addInput(1);
    else if (pressed & RC100_BTN_3) addInput(2);
    else if (pressed & RC100_BTN_4) addInput(3);
    else if (pressed & RC100_BTN_5) restartInput();
    return;
  }
  if (pressed & RC100_BTN_6)      startInput();
  else if (pressed & RC100_BTN_U) playSignal(true);
  else if (pressed & RC100_BTN_R) playSignal(false);
  else if (pressed & RC100_BTN_D) showPucks();
}

void setup() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(RELAY_PIN[i], HIGH);
    pinMode(RELAY_PIN[i], OUTPUT);
  }
  Serial.begin(115200);
  rc.begin(1);                             // 1 = Serial2 (수신기 포트)
  loadSaved();
  allOff();
}

void loop() {
  // 리모컨: 버튼 하나짜리 값이 연속 CONFIRM_PACKETS 번 오면 한 번 처리, 손을 떼면(0) 다음 누름을 기다림
  while (Serial2.available() > 0) {
    if (!rc.available()) continue;
    uint16_t data = rc.readData();
    bool oneButton = data != 0 && (data & ~VALID_BUTTONS) == 0 && (data & (data - 1)) == 0;
    if (data == 0) {                       // 손 뗌: 아직 처리 안 한 버튼이 있으면 지금 처리
      if (rcCandidate != 0 && !rcHandled) handleButton(rcCandidate);
      rcCandidate = 0;
      rcSameCount = 0;
      rcHandled = false;
      continue;
    }
    if (!oneButton) {                      // 여러 비트 · 이상한 값 → 버림
      rcCandidate = 0;
      rcSameCount = 0;
      rcHandled = false;
      continue;
    }
    if (data != rcCandidate) {
      rcCandidate = data;
      rcSameCount = 1;
      rcHandled = false;
    } else if (rcSameCount < CONFIRM_PACKETS) {
      rcSameCount++;
    }
    if (!rcHandled && rcSameCount >= CONFIRM_PACKETS) {   // 누르고 있는 동안 계속 보내는 리모컨
      rcHandled = true;
      handleButton(data);
    }
  }

  // 노트북 시리얼: ? = 현재 구성과 마지막 세트
  while (Serial.available() > 0) {
    if (Serial.read() == '?') {
      printPucks();
      if (haveSeq) printSequence();
    }
  }

  updatePlay();
}
