// 00_hello_world.cpp
// 목적: g++가 정상적으로 설치되어 컴파일·실행이 되는지 확인하는 최소 프로그램.
//
// 컴파일: g++ -Wall -Wextra -std=c++17 -o hello src/00_hello_world.cpp
// 실행  : ./hello

#include <iostream>  // 표준 입출력(std::cout 등)을 쓰기 위한 헤더

int main() {
    // std::cout : 표준 출력(화면)으로 내보내는 스트림
    // <<        : "이 값을 스트림에 흘려보내라"는 연산자, 여러 번 이어 쓸 수 있다
    // std::endl : 줄바꿈 + 출력 버퍼 비우기
    std::cout << "Hello, Physical AI!" << std::endl;

    // 컴파일러·표준 버전을 확인해 두면 나중에 "왜 이 문법이 안 되지?" 를 줄일 수 있다.
    std::cout << "__cplusplus (컴파일된 C++ 표준) = " << __cplusplus << std::endl;

    // main()의 반환값 0은 "정상 종료"를 운영체제에 알리는 관례다.
    return 0;
}
