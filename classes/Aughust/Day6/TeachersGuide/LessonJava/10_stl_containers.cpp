// 10_stl_containers.cpp — 8강 6절: STL
// 목적: vector · unordered_map · count_if(람다) · reserve()를 직접 실행해 보고,
//       reserve 유무에 따른 capacity() 변화(=재할당 여부)를 눈으로 확인한다.
//
// STL = Standard Template Library (스탠다드 템플릿 라이브러리). 5절(템플릿) 위에 세워진,
// 검증된 자료구조·알고리즘 모음이다. vector·map·set 등이 전부 STL 소속이다.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o stl_containers src/10_stl_containers.cpp
// 실행  : ./stl_containers

#include <algorithm>
#include <iostream>
#include <unordered_map>
#include <vector>

int main() {
    // ── 1. vector ───────────────────────────────────────────
    std::cout << "[1] std::vector — 5강 list에 대응\n";
    std::vector<double> scan = {0.3, 8.2, 0.5, 12.0};
    scan.push_back(1.1);   // 끝에 추가 (Python list.append()와 같은 자리)

    std::cout << "  scan = [";
    for (std::size_t i = 0; i < scan.size(); ++i) {
        std::cout << scan[i] << (i + 1 < scan.size() ? ", " : "");
    }
    std::cout << "]\n";

    // min_element는 "위치"(iterator, 이터레이터 — 컨테이너 안의 한 지점을 가리키는 객체,
    // 포인터와 비슷하게 생각하면 된다)를 돌려주므로 앞에 *를 붙여 실제 값을 꺼낸다.
    double closest = *std::min_element(scan.begin(), scan.end());
    std::cout << "  가장 가까운 거리(min_element) = " << closest << "\n\n";

    // ── 2. unordered_map ────────────────────────────────────
    std::cout << "[2] std::unordered_map — 5강 dict에 대응, 조회 O(1)\n";
    std::unordered_map<std::string, double> sensors;
    sensors["battery"] = 11.9;
    sensors["lidar_range"] = 12.0;

    if (sensors.count("battery")) {   // count(): 키가 있으면 1, 없으면 0
        std::cout << "  battery = " << sensors["battery"] << "\n";
    }
    if (!sensors.count("camera")) {
        std::cout << "  camera 키는 아직 없음 (count() == 0)\n\n";
    }

    // ── 3. count_if + 람다 ──────────────────────────────────
    std::cout << "[3] std::count_if + 람다 — 5강 리스트 컴프리헨션과 비슷한 역할\n";
    // [](double d){ return d < 1.0; } : 이름 없는 즉석 함수(람다). "d를 받아 d < 1.0을 반환"
    int near_count = std::count_if(scan.begin(), scan.end(),
                                    [](double d) { return d < 1.0; });
    std::cout << "  1.0m 이내로 측정된 개수 = " << near_count << "\n\n";

    // ── 4. reserve() — 실시간 코드에서의 힙 재할당 회피 ─────
    std::cout << "[4] reserve() — 미리 용량을 잡아 루프 중 재할당을 없앤다\n";

    std::vector<double> without_reserve;
    std::cout << "  reserve 없이 360번 push_back하며 capacity 변화(처음 8번만 출력):\n";
    std::size_t last_cap = 0;
    int printed = 0;
    for (int i = 0; i < 360; ++i) {
        without_reserve.push_back(static_cast<double>(i));
        if (without_reserve.capacity() != last_cap) {
            last_cap = without_reserve.capacity();
            if (printed < 8) {
                std::cout << "    size=" << without_reserve.size()
                          << " 에서 capacity가 " << last_cap << "로 재할당됨\n";
                ++printed;
            }
        }
    }
    std::cout << "  -> capacity가 여러 번 바뀌었다 = 그만큼 힙 재할당이 여러 번 일어났다는 뜻.\n\n";

    std::vector<double> with_reserve;
    with_reserve.reserve(360);   // 루프 밖에서 미리 360개 용량 확보
    std::size_t cap_before_loop = with_reserve.capacity();
    for (int i = 0; i < 360; ++i) {
        with_reserve.push_back(static_cast<double>(i));
    }
    std::cout << "  reserve(360) 후 360번 push_back: capacity가 루프 내내 "
              << cap_before_loop << "로 고정 (재할당 0회)\n";
    std::cout << "  -> Hard 실시간 제어 루프에서는 이렇게 루프 시작 전에 reserve로 재할당을 없앤다.\n";

    return 0;
}
