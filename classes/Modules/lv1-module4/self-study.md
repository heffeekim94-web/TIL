Date 2026 Sept 8일

### ffmpeg : 소프트웨어/ 도구, 프로그램 + 라이브러리
- 영상 포맷 변환, 영상 압축, 해상도 변경, 영상 자르기/합치기, 소리 추출, 프레임을 이미지로 추출, 카메라 영상 녹화/ 스트리밍
- 영상, 카메라 분야

사용 코드:
```bash
ffmpeg -i input.mp4 output.avi
```

- 영상과 소리를 터미널에서 가공하는 도구
- FF = fast forward
- MPEG = 영상,음성 앞축 표준을 만드는 그룹 이름.

사용 라이브러리:
- libavcodec
- libavformat


---

### OpenC : library
- Open Source Computer Vision Library
- 컴퓨터가 카메라나 사진을 보고 이해하도록 도와주는 라이브러리

Python:
```python
import cv2

img = cv2.imread("robot_camera.jpg")
```

Keywords:
`OpenCV`, `cv2`, `cv_bridge`, `sensor_msgs/Image`

---

### OpenCV vs FFmpeg
- FFmpeg : 영상을 저장, 변환, 압축하는 데 강함
- OpenCV : 영상 안에 무엇이 있는지 처리, 분석하는 데 강함 

---

### SLERP : 계산 방법
- Spherical Linear Interpolation
- 구면 선형 보간
- 시작 회전과 목표 회전 사이의 중간 회전 자세를 부드럽게 계산하는 방법

사용 수학:
- 쿼터니언

Keywords:
`quaternion`, `tf2`, 로봇팔 trajectory

---

### PCA : 분석
- Principal Component Analysis
- 주성분 분석
    - "이 점들이 전체적으로 어느 방향으로 퍼져 있지?" 를 찾는 방법
    - 물체가 어느 방향으로 놓여 있는지, 데이터가 어느 축으로 많이 퍼져 있는지 등 

Before:
```
y
│
│        •
│      •
│    •
│  •
│•
└──────────── x
```

After PCA use:
```
        •
      •
    •     ↗  ← PCA가 찾은 주된 방향
  •
•
```

---

### Kabsch : Calculating Algorithm
- Kabsh alorithm
- "두 점 집합을 가장 잘 겹치게 하려면 얼마나 회전시켜야 하는지"

1st measure:
```
A:

•       •
    •

•
```
- scattered points

2nd measure:
```
B:

    •
       •
  •
       •
```
- 위치와 방향이 달라짐

Kabsch does:
- A -> B 가 되는 회전행렬 R을 찾는다.
- 위치 이동까지 맞출때: 각 점 집합의 중심을 빼서 -> 회전을 구한 뒤 -> translation $t$도 계산한다.

---

### PCA vs Kabsch

|          | PCA                  | Kabsch                    |
| -------- | -------------------- | ------------------------- |
| 질문       | 점들이 **어느 방향으로 퍼졌나?** | 두 점 집합을 **어떻게 회전하면 겹치나?** |
| 입력       | 보통 하나의 점 집합          | 대응되는 두 점 집합               |
| 주로 구하는 것 | 주성분/주축               | 회전 \(R\), 그리고 보통 이동 \(t\) |
| 로봇 예시    | 물체 방향 추정             | 두 자세의 포인트 정합              |

PCA : 점들의 구조/방향 파악
Kabsh : 두 점군 사이의 자세 변환 계산

Key terms:
LiDar → Point Cloud -> SLAM

Keyword:
SVD(특이값 분해)