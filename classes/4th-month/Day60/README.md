Date: 2026 Oct 30, Friday

## 오늘 배운 것
- [로봇팔 제어와 정책학습 (MoveIt 2 · cuMotion · Isaac Lab)](class.md)
- [강의](https://app.notion.com/p/409796969395802ba81dc9ab4657aeed)
- [수업 자료](https://docs.google.com/presentation/d/1HuyJI1gvsZrXSdgijeE4Y8bBrIvQ5ILEh8RjF5t9I9E/edit)




<br>

## 오늘 한 것 

- [비전 작업 일지 (10/30)](vision_log.md)
- 1단계 시작 epoch 원인 실험 → 1단계 33 epoch 고정 모델(real_ft_fixed33)을 최종 모델로
- 팀 레포 yolo/wide 정리 (README, hyp.yaml, 스크립트 8개, train.ipynb) → PR
- 경량화 비교 (PyTorch / ONNX FP32 · FP16 · INT8) → ONNX FP16 채택
- perception 인지 노드를 C++ (ONNX Runtime) 로 전환 → PR



<br>

## 문제점
- 2단계 설정이 같은데 시작 모델에 따라 실제 test 가 0.907 ~ 0.969 로 달라짐
- 기존 최종 모델(0.969)은 레포에 없는 real_v4 val 로 1단계 epoch 를 골라 재현이 안 됨
- 노트북 출력에 실험 폴더 경로(real_v5 등)가 그대로 찍힘
- INT8 양자화 모델의 mAP 가 0
- 팀 요청: Python 인지 노드를 C++ 로, 패키지 구조(perception/perception, resource/)도 C++ 방식으로




<br>

## 해결 방법

- 2단계는 그대로 두고 1단계 시작점만 바꿔 비교 → 작은 val(68장)로 고른 best epoch(9)가 원인
- 1단계를 33 epoch 으로 고정(patience 0, last.pt) → real_v5 만으로 재현되는 방법을 README 표준으로
- prepare_data.py 가 바로가기 링크를 풀지 않게(`.absolute()`) 고침
- 마지막 출력에 상자 좌표(0~960)와 점수(0~1)가 같이 있어 int8 눈금 하나로 뭉개짐 → Detect 층만 FP32
- ONNX Runtime C++ 로 추론, `src/` 에 C++ 파일, `resource/` · `setup.py` 삭제(ament_package 가 대신 등록)


<br>

## 결과

- 최종 모델 real_ft_fixed33: 실제 test mAP50 0.949 / mAP50-95 0.705, 어두운 사진 0.995, conf 0.5 오검출 0
- ONNX FP16: 5.1 MB, 5.24 ms(191 FPS), 정확도 손실 없음 (PyTorch 5.81 ms, ONNX FP32 6.37 ms)
- INT8 (CPU): 85.5 ms 로 FP32 (82.6 ms) 보다 빠르지 않음
- perception_node C++: 빌드 경고 0, gtest 10개 통과, 실제 모델로 토픽 출력 확인
- PR 2개 (feat/yolo-wide, feat/perception-node)




<br>

## 느낀 점

- 이렇게 다 되는거라면 뭐라도 다 할 수 있을것 같다. 





<br>

## 할 일

- PR 리뷰 · 머지
- PC 에 ONNX Runtime C++ 설치 → perception_node 를 실제 광각 카메라로 실행
- Jetson 으로 모델 scp → TensorRT FP16 엔진 · 속도 측정
- 옆에서 본 · 멀리 있는 퍽 사진 라벨링 (red_box 놓침 6개)
- pa06 bringup → 키보드 조종 → cartographer
- 손목 카메라로 집은 퍽이 고정돼 있는지 보고 집기 성공 · 실패 판단 (수업에서 나온 비전 할 일)




