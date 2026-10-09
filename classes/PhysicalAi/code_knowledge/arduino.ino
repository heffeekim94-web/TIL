# include <math.h>
// 라이브러리 불러오기: 아두이노의 헤더 파일. 함수와 변수 존재. 설계도 선언, Declaration
// math.c를 불러온다.
# include <math.c>
// 물리학 관련 함수들을 정의한 파일을 포함. 헤더 파일에 적힌 설계도를 바탕으로 실제 기능 (정의, Definition)
// 실제로 파일을 main.c 처럼 이름을 이렇게 새긴다.
    // 함수가 반드시 필요함
    // main.c 참조

constexpr 
// 프로그램 실행 속도 향상 (최적화)
// 컴파일러가 프로그램을 만드는 도중 계산을 끝냄
// 상수가 필요할때 - 컴파일때는 미리 결정된 상수만 갖고 올 수 있음

constexpr uint8_t //1 byte = 8bit, 0~255, 1byte
constexpr uint16_t // 2byte = 16bit, 0~65535 정수, 2byte
constexpr uint32_t // 4byte = 32bit, 0~4294967295 정수, 4byte
constexpr float // 4byte = 32bit, 소수점 포함, 4byte
constexpr int32_t // 4byte = 32bit, -2147483648~2147483647 정수, 4byte
// 이 데이타를 사용할 쪽도 같은 양의 데이타를 불러와야함. (같은 설계도, 헤더파일을 불러와야함)


namespace Headname {
    int containedName = 1
}// 이름은 같지만 충돌하지 않음

void
// 반환값이 없을 때 

.read 