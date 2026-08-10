// 03_control_loops.cpp — 기본 문법 ③: 조건문과 반복문
// 목적: if/else, switch, for(전통/범위기반), while, do-while, break/continue,
//       중첩 반복문까지 로봇 코드에서 실제로 쓰는 제어 흐름 패턴을 전부 훑는다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o control_loops src/03_control_loops.cpp
// 실행  : ./control_loops

#include <iostream>

int main() {
    // ── 1. if / else if / else ──────────────────────────────
    int battery_percent = 42;
    std::cout << "[1] if / else if / else (battery_percent = 42)\n";
    if (battery_percent < 20) {
        std::cout << "  배터리 부족 — 충전소로 복귀\n";
    } else if (battery_percent < 50) {
        std::cout << "  배터리 보통\n";
    } else {
        std::cout << "  배터리 충분\n";
    }
    std::cout << "\n";

    // ── 2. switch — 정수/문자/enum처럼 "값 하나"를 여러 갈래로 분기할 때 ──
    char sensor_code = 'L';
    std::cout << "[2] switch (sensor_code = 'L')\n";
    switch (sensor_code) {
        case 'L':
            std::cout << "  LiDAR 센서\n";
            break;   // break가 없으면 아래 case로 "그대로 흘러 내려간다"(fallthrough) — 실수하기 쉬운 지점
        case 'I':
            std::cout << "  IMU 센서\n";
            break;
        case 'C':
            std::cout << "  카메라 센서\n";
            break;
        default:
            std::cout << "  알 수 없는 센서 코드\n";
    }
    std::cout << "\n";

    // ── 3. for — 전통적인 형태(인덱스 직접 관리) ─────────────
    int readings[5] = {12, 8, 15, 3, 9};
    std::cout << "[3] 전통적인 for (인덱스로 접근)\n  ";
    for (int idx = 0; idx < 5; ++idx) {
        std::cout << "[" << idx << "]=" << readings[idx] << " ";
    }
    std::cout << "\n\n";

    // ── 4. 범위 기반 for — Python의 for x in ... 와 가장 비슷 ──
    std::cout << "[4] 범위 기반 for (원소를 직접 순회)\n  ";
    for (int r : readings) {
        std::cout << r << " ";
    }
    std::cout << "\n\n";

    // ── 5. while — 조건을 먼저 검사 ──────────────────────────
    int countdown = 3;
    std::cout << "[5] while (조건이 먼저, 0번 실행될 수도 있음)\n  ";
    while (countdown > 0) {
        std::cout << countdown << " ";
        --countdown;
    }
    std::cout << "발사!\n\n";

    // ── 6. do-while — 몸통을 먼저 한 번 실행하고 나서 조건 검사 ──
    // "최소 한 번은 실행되어야 하는" 로직에 쓴다 (예: 센서 초기 연결 재시도).
    int attempt = 0;
    std::cout << "[6] do-while (최소 1회 실행 보장)\n";
    do {
        ++attempt;
        std::cout << "  연결 시도 #" << attempt << "\n";
    } while (attempt < 3);
    std::cout << "\n";

    // ── 7. break / continue ─────────────────────────────────
    std::cout << "[7] break / continue\n";
    std::cout << "  break 예시 — 이상값(-1)을 만나면 즉시 루프 종료:\n  ";
    int scan[6] = {5, 4, 3, -1, 2, 1};
    for (int v : scan) {
        if (v == -1) {
            std::cout << "(중단) ";
            break;   // 루프 전체를 즉시 빠져나간다
        }
        std::cout << v << " ";
    }
    std::cout << "\n";

    std::cout << "  continue 예시 — 이상값(-1)만 건너뛰고 계속 진행:\n  ";
    for (int v : scan) {
        if (v == -1) {
            continue;   // 이번 회차만 건너뛰고 다음 원소로 진행
        }
        std::cout << v << " ";
    }
    std::cout << "\n\n";

    // ── 8. 중첩 반복문(nested loop) — 반복문 안에 반복문, 2차원 격자(그리드) 순회 ──
    std::cout << "[8] 중첩 반복문 (3x3 그리드 좌표 순회)\n";
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            std::cout << "(" << row << "," << col << ") ";
        }
        std::cout << "\n";
    }

    return 0;
}
