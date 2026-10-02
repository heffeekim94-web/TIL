


```cpp
// 직전 오차와 현재 오차를 비교하여 피크(방향이 바뀌는 지점)를 감지하는 간단한 로직 예시
static float prev_error = 0;
static uint32_t last_peak_ms = 0;

// 오차의 부호가 바뀌거나 극대/극소점이 될 때의 시간을 측정
if ((prev_error > 0 && error_rad <= 0) || (prev_error < 0 && error_rad >= 0)) {
    uint32_t now_ms = millis();
    if (last_peak_ms != 0) {
        uint32_t half_period_ms = now_ms - last_peak_ms;
        float measured_Tu = (half_period_ms * 2) / 1000.0f; // 반쪽 주기를 합쳐서 전체 주기(Tu) 계산
        
        Serial.print("--> [Measured Tu]: "); 
        Serial.print(measured_Tu); 
        Serial.println(" s");
    }
    last_peak_ms = now_ms;
}
prev_error = error_rad;
```