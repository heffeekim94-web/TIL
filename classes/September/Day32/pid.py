import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# 1. 시뮬레이션 설정 (지속 진동하는 상태의 파형 가정)
dt = 0.001          # 제어 주기 (1ms)
t = np.arange(0, 5, dt)

# 예시: 한계 이득(Ku) 상태에서 지속 진동하는 사인파형 (주기 Tu = 0.5초라고 가정)
Tu_true = 0.5       
y = np.sin(2 * np.pi * t / Tu_true) + 0.1 * np.random.randn(len(t)) # 노이즈 살짝 포함

# 2. SciPy를 이용해 봉우리(Peak) 자동 찾기
# distance: 너무 촘촘하게 잡히는 노이즈를 거르기 위해 최소 피크 간격 설정 (0.4초 기준)
peaks, _ = find_peaks(y, distance=int(0.4 / dt))

# 3. 봉우리들 사이의 시간 간격(주기) 계산
peak_times = t[peaks]
# 인접한 봉우리들 간의 시간 차이 계산
intervals = np.diff(peak_times)
Tu_measured = np.mean(intervals)

print(f"[자동 측정 결과]")
print(f"- 감지된 봉우리 시간들: {peak_times}")
print(f"- 측정된 한계 주기(Tu): {Tu_measured:.4f} 초")

# 4. 시각화 (그래프 그리기)
plt.figure(figsize=(10, 5))
plt.plot(t, y, label='System Response (Oscillation)', color='gray', alpha=0.7)
plt.plot(peak_times, y[peaks], "ro", label='Detected Peaks') # 찾은 봉우리를 빨간 점으로 표시

# 첫 번째와 두 번째 봉우리 사이에 화살표와 텍스트로 Tu 표시
if len(peaks) >= 2:
    t1, t2 = peak_times[0], peak_times[1]
    y1 = y[peaks[0]]
    plt.annotate(f'Tu = {Tu_measured:.3f}s', 
                 xy=((t1 + t2)/2, y1), xytext=((t1 + t2)/2, y1 + 0.5),
                 arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=6),
                 ha='center', fontsize=12, color='blue', weight='bold')

plt.title('Automatic Tu Detection using Peak Finding')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
plt.legend()
plt.grid(True)
plt.show()