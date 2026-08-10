# C++ grammer

## Install C++ language

```bash

# update
haeminkim@pa:~/Desktop$ sudo apt update

# enter passcode
[sudo] haeminkim 암호: 


# running program looks like:
기존:1 http://kr.archive.ubuntu.com/ubuntu jammy InRelease
기존:2 http://kr.archive.ubuntu.com/ubuntu jammy-updates InRelease                                       
기존:3 http://kr.archive.ubuntu.com/ubuntu jammy-backports InRelease                                     
기존:4 https://dl.google.com/linux/chrome-stable/deb stable InRelease                                    
기존:5 http://packages.ros.org/ros2/ubuntu jammy InRelease                                               
기존:6 http://security.ubuntu.com/ubuntu jammy-security InRelease                                        
기존:7 https://packagecloud.io/slacktechnologies/slack/debian jessie InRelease
기존:8 https://linux.teamviewer.com/deb stable InRelease                      
패키지 목록을 읽는 중입니다... 완료                   
의존성 트리를 만드는 중입니다... 완료
상태 정보를 읽는 중입니다... 완료        
188 패키지를 업그레이드할 수 있습니다. 확인하려면 'apt list --upgradable'를 실행하십시오.

# c++ language installation 
haeminkim@pa:~/Desktop$ sudo apt install -y build-essential cmake gdb valgrind git

# running program looks like:
패키지 목록을 읽는 중입니다... 완료
의존성 트리를 만드는 중입니다... 완료
상태 정보를 읽는 중입니다... 완료        
패키지 build-essential는 이미 최신 버전입니다 (12.9ubuntu3).
build-essential 패키지는 수동설치로 지정합니다.
패키지 cmake는 이미 최신 버전입니다 (3.22.1-1ubuntu1.22.04.2).
cmake 패키지는 수동설치로 지정합니다.
패키지 gdb는 이미 최신 버전입니다 (12.1-0ubuntu1~22.04.2).
gdb 패키지는 수동설치로 지정합니다.
패키지 git는 이미 최신 버전입니다 (1:2.34.1-1ubuntu1.17).
git 패키지는 수동설치로 지정합니다.
다음 패키지가 자동으로 설치되었지만 더 이상 필요하지 않습니다:
  libfwupd2 libfwupdplugin5 libgcab-1.0-0 libsmbios-c2
'sudo apt autoremove'를 이용하여 제거하십시오.
다음의 추가 패키지가 설치될 것입니다 :
  libc6-i386
제안하는 패키지:
  valgrind-dbg valgrind-mpi kcachegrind alleyoop valkyrie
다음 새 패키지를 설치할 것입니다:
  libc6-i386 valgrind
0개 업그레이드, 2개 새로 설치, 0개 제거 및 188개 업그레이드 안 함.
16.9 M바이트 아카이브를 받아야 합니다.
이 작업 후 91.8 M바이트의 디스크 공간을 더 사용하게 됩니다.
받기:1 http://kr.archive.ubuntu.com/ubuntu jammy-updates/main amd64 libc6-i386 amd64 2.35-0ubuntu3.14 [2,838 kB]
받기:2 http://kr.archive.ubuntu.com/ubuntu jammy/main amd64 valgrind amd64 1:3.18.1-1ubuntu2 [14.1 MB]
40% [2 valgrind 3,543 kB/14.1 MB 25%]^C

# check version
haeminkim@pa:~/Desktop$ g++ --version

# shows version
g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
Copyright (C) 2021 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# check cmake version
haeminkim@pa:~/Desktop$ cmake --version


cmake version 3.22.1
CMake suite maintained and supported by Kitware (kitware.com/cmake).

# check gdb version
haeminkim@pa:~/Desktop$ gdb --version

# shows gdb version
GNU gdb (Ubuntu 12.1-0ubuntu1~22.04.2) 12.1
Copyright (C) 2022 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

# chceck valgrind version
haeminkim@pa:~/Desktop$ valgrind --version

# shows vlgrind version
명령어 'valgrind' 을(를) 찾을 수 없습니다. 그러나 다음을 통해 설치할 수 있습니다:
sudo snap install valgrind  # version 3.26.0, or
sudo apt  install valgrind  # version 1:3.18.1-1ubuntu2
'snap info valgrind'에서 추가적인 버전을 확인하십시오.

```


## Start Java

```java

#include <iostream>
int main() { //appropriate place to have opening { to reduce a line
    std::cout << "Hello, World!" << std::endl;
    return 0;
}


//The print function in C++ is typically done using the `std::cout` object from the `<iostream>` header. 
//In your code, you are using `std::cout` to print "Hello, World!" to the console. 
//The `std::endl` is used to insert a newline character and flush the output buffer.

//"" has to match the opening quote, so it should be `""` instead of `""`.

//std::endl is a manipulator that inserts a newline character and flushes the output /buffer, 
//ensuring that the output is displayed immediately.

//g++ is to compile the C++ code. You can use the following command to compile your `hello_world.cpp` file:


//input in the terminal to compile the code:

```


```bash

g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp

# This command tells the compiler to use the C++17 standard, enable all warnings, 
# and output an executable named `hello` from the source file `hello_world.cpp`.
# make sure the file is saved before running the command.

./hello

# This command runs the compiled executable, which should print "Hello, World!" to the console.

Hello, World!

# result shows up in the terminal after running the executable.

```


```java

#include <iostream>
#include <string>

int main() {
    short count = 10;
    // short is for small integers, typically used for memory efficiency.
    // could also have negative values, but with a smaller range than int.
    int battery = 220;
    // int is for size 4 bytes, commonly used for general-purpose integer storage.
    long distance = 1000000;
    // long is for larger integers, typically used when the range of int is insufficient.
    unsigned int age = 25;
    // unsigned int is for non-negative integers, often used when negative values are not needed.
    // usually used for counting or indexing for those variable that cannot be negative.

    std::cout << "Count: " << count << std::endl;
    std::cout << "Battery: " << battery << std::endl;
    std::cout << "Distance: " << distance << std::endl;
    std::cout << "Age: " << age << std::endl;

    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
Count: 10
Battery: 220
Distance: 1000000
Age: 25

---

#include <iostream>
#include <string>

int main() {
    float number = 3.14f;
    // float is 4 bytes in size
    // 'f' at the end means that the number is a float literal.
    double largeNumber = 3.14159265358979323846;
    // double is 8 bytes in size
    // in usaual cases using 'double' is recommended for better precision.

    std::cout << " number: " << number << std::endl;
    std::cout << " largeNumber: " << largeNumber << std::endl;

    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
 number: 3.14
 largeNumber: 3.14159

---

#include <iostream>
#include <string>

int main() {
    bool robotstate = true;
    char sensor = 'A';
    // char is for single character, string is for multiple characters.
    std::string message = "Hello, World!";
    // std::string is a class in C++ that represents a sequence of characters.

    std::cout << "Robot state: " << (robotstate ? "Active" : "Inactive") << std::endl;
    std::cout << "Sensor Type: " << sensor << std::endl;
    std::cout << "Message: " << message << std::endl;
    
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
 Robot state: Active
Sensor Type: A
Message: Hello, World!

---

#include <iostream>
#include <string>

int main() {
    int readings[5] = {10, 20, 30, 40, 50};
    // must input the lenght of the array and then input the values of the array.
    // if the data type of the array is int, then the values must be integers.
    // if else, the result will return an error message.
    // double will allow float type to be shown
    std::cout << "Sensor readings: " << readings[0] << ", " 
    << readings[1] << ", " << readings[2] << ", " << readings[3] << ", " << readings[4] << std::endl;
    
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
Sensor readings: 10, 20, 30, 40, 50

---

#include <iostream>
#include <string>

int main() {
    double readings[5] = {10, 20, 30, 40, 50};
    std::cout << "readings[0] size is: " << sizeof(readings[0]) << " bytes" << std::endl;
    // will print the size of the first element in the readings array, 
    //which is a double (typically 8 bytes on most systems).
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
readings[0] size is: 8 bytes

---

#include <iostream>
#include <string>

int main() {
    const long array_size = 5;
    // const in the front means the variable is constant and cannot be changed after initialization.
    constexpr long array_size2 = 5;
    // fixed when compiled. 

    std::cout << "Array size: " << array_size << std::endl;
    std::cout << "Array size2: " << array_size2 << std::endl;
    
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
Array size: 5
Array size2: 5

---

#include <iostream>
#include <string>

int main() {
    auto name = "World";
    // automatically decides a name
    // not reccomanded
    std::cout << "Hello, " << name << "!" << std::endl;
    
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
Hello, World!

---

#include <iostream>
#include <string>


int main() {
    int number = 2;
    std::cout << "number" << std::endl;
    {
        int number = 3;
        std::cout << "number" << std::endl;
        //block scope
    }
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:

---

#include <iostream>
#include <string>


int main() {
    int a = 7, b = 3;
    // with comma operator, we can combine multiple expressions into a single statement
    std::cout << a+b << std::endl; // output: 10
    std::cout << a-b << std::endl; // output: 4
    std::cout << a*b << std::endl; // output: 21
    std::cout << a/b << std::endl; // output: 2
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
10
4
21
2

---

#include <iostream>
#include <string>


int main() {
    float a = 7, b = 3;
    // with comma operator, we can combine multiple expressions into a single statement
    // ****this will become important issue in future. 
    std::cout << a+b << std::endl; // output: 10
    std::cout << a-b << std::endl; // output: 4
    std::cout << a*b << std::endl; // output: 21
    std::cout << a/b << std::endl; // output: 2
    std::cout << fmod(a, b) << std::endl; // output: 1. remaining value after division
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
10
4
21
2.33333

---

#include <iostream>
#include <string>


int main() {
    int count = 100;
    count += 50; std::cout << count << std::endl; // output: 30
    // adding 50 to count variable
    count -= 25; std::cout << count << std::endl; // output: 30
    count *= 2;  std::cout << count << std::endl; // output: 30
    count /= 5;  std::cout << count << std::endl; // output: 30
    // always make a habit of saving the end resuld of value in a variable and then print it out to the terminal.


    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
150
125
250
50

---

#include <iostream>
#include <string>


int main() {
    int i = 5;
    int result_i = i++; 
    // could also be --i or i--
    // --i and i-- means different things.
    // --i means subtract 1 from i 'before' the value of i is assigned to result_i
    // i-- means subtract 1 from i 'after' the value of i is assigned to result_i
    // ++i means add 1 to i 'before' the value of i is assigned to result_i
    std::cout << "Result of i++: " << result_i << "," << " i after increment: " << i << std::endl;
    // This means add 1 to i before the value of i is assigned to result_i
    int j = 5;
    int result_j = ++j;
    std::cout << "Result of ++j: " << result_j << "," << " j after increment: " << j << std::endl;

    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:

---

#include <iostream>
#include <string>


int main() {
    double batteryVoltage = 3.7;
    bool lidar_isOK = true, imu_isOK = true;
    std::cout << "batteryVoltage < 50 = " << std::boolalpha << (batteryVoltage < 50) << std::endl;
    std::cout << "batteryVoltage <= 50 = " << std::boolalpha << (batteryVoltage <= 50) << std::endl;
    std::cout << "lidar_isOK = " << std::boolalpha << lidar_isOK << std::endl;
    std::cout << "imu_isOK = " << std::boolalpha << imu_isOK << std::endl; 

    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
batteryVoltage < 50 = true
batteryVoltage <= 50 = true
lidar_isOK = true
imu_isOK = true

---

#include <iostream>
#include <string>


int main() {
    bool lidar_isOK = true, imu_isOK = true;
    std::cout << "robot State : " << (lidar_isOK || imu_isOK ? "OK" : "Not OK") << std::endl;
    std::cout << "robot State : " << (!lidar_isOK) << std::endl;
    
    // && is logical AND operator, it returns true if both operands are true, otherwise it returns false.
    // || is logical OR operator, it returns true if at least one of the operands is true, otherwise it returns false.

    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
robot State : OK
robot State : 0

---

#include <iostream>
#include <string>
#include <cmath> // Include the cmath library for sqrt function


int main() {
    double dx = 5.0, dy = 10.0;
    double distance = std::sqrt(dx * dx + dy * dy);
    // sqrt is a function from the <cmath> library, so we need to include it
    // it will square root the sum of squares of dx and dy to calculate the distance
    // need to include the cmath library to use the sqrt function
    
    std::cout << "Distance: " << distance << std::endl;
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
Distance: 11.1803

---

#include <iostream>
#include <string>
#include <cmath> // Include the cmath library for sqrt function


int main() {
    int batteryLevel = 100; // Initialize battery level to 100%
    std::cout << "batteryLevel: if / elseif else (battery = 100)"; 
    if (batteryLevel == 100) {
        std::cout << "Battery is fully charged." << std::endl;
    } else if (batteryLevel >=50) {
        std::cout << "Battery is more that half charged." << std::endl;
    } else if (batteryLevel > 0) {
        std::cout << "Battery is low." << std::endl;
    } else {
        std::cout << "Battery is empty." << std::endl;
    }
    // reading in order matters
    // must read beggining from top to bottom.


    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:

---

#include <iostream>
#include <string>
#include <cmath> // Include the cmath library for sqrt function


int main() {
    char lidar_code = 'F';
    std::cout << "lidar_code = ";
    switch (lidar_code) {
        case 'A':
            std::cout << "Lidar code A: Basic Lidar" << std::endl;
            break;
        case 'B':
            std::cout << "Lidar code B: Advanced Lidar" << std::endl;
            break;
        case 'C':
            std::cout << "Lidar code C: High-Resolution Lidar" << std::endl;
            break;
        case 'D':
            std::cout << "Lidar code D: Long-Range Lidar" << std::endl;
            break;
        case 'E':
            std::cout << "Lidar code E: Multi-Beam Lidar" << std::endl;
            break;
        case 'F':
            std::cout << "Lidar code F: Solid-State Lidar" << std::endl;
            break;
        default:
            std::cout << "Unknown Lidar code" << std::endl;
    }

    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:

---

#include <iostream>
#include <string>
#include <cmath> // Include the cmath library for sqrt function


int main() {
    int readings[5] = {30, 13, 45, 2, 1};
    for (int i = 0; i < 5; i++) {
        std::cout << readings[i] << std::endl;
    }
    // i < 5 is the returning amount of elements in the array readings.

    for(int i : readings) {
        std::cout << i << std::endl;
    }
    // for loop returning the amount of elements in the array readings.

    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:

---

#include <iostream>
#include <string>
#include <cmath> // Include the cmath library for sqrt function


int main() {
    int number: 0; // Declare an integer variable to store the input number
    while (1) {
        std::cout << "Hello, World!" << number << std::endl; 
        number++; // Increment the number by 1
        delay(1000); // Delay for 1 second (1000 milliseconds)
        std::this_thread::sleep_for(std::chrono::milliseconds(1000)); // Use std::this_thread::sleep_for for delay
    }
    return 0;
    
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:

---

#include <iostream>
#include <string>
#include <cmath> // Include the cmath library for sqrt function


int main() {
    int number: 0; // Declare an integer variable to store the input number
    do {
        ++number;
        std::cout << "Hello, World! " << number << std::endl; // Print "Hello, World!" followed by the current number
    } while (number < 5);
    return 0;
    // instead of while loop, you can use a for loop to achieve the same result:
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:

---

#include <iostream>
#include <string>
#include <cmath> // Include the cmath library for sqrt function


int add(int a, int b) {
    return a + b;
}

int main() {
    int num1, num2;
    std::cout << "Enter two integers: ";
    std::cin >> num1 >> num2;
    
    int sum = add(num1, num2);
    std::cout << "The Sum is: " << sum << std::endl;
    return 0;
    // instead of while loop, you can use a for loop to achieve the same result:
}

//after adjusting the file need to re-run 'g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp'
//in bash termial.

// run ./hello

// resultes showing in bash terminal:
Enter two integers: 2 3
The Sum is: 5

---

#include <iostream>
#include <vector>

class Motor {
public:
    Motor() {
        std::cout << "Motor initialized" << std::endl;
    }   
    ~Motor() {
    // Destructor
        std::cout << "Motor destroyed!" << std::endl;
    }
};


void control_loop() {
    std::cout << "Starting control loop..." << std::endl;
    double time_step = 0.1;
    Motor motor_ptr;
    // Create an instatnce of the Motor class
    (void) time_step;
}

int main() {
    control_loop();
    Motor* motor_ptr = new Motor();
    std::cout << "Control loop finished." << std::endl;

    delete motor_prt; // Don't forget to free the allocated memory
     
    std::
    return 0;


```

C language is important dealing with memory space

controlling memory is important beacuse sometimes it brings
extra datas and accumulates unimportant datas and this will 
give troubles in programs in the future.

in Python thses are automatic
in C++, we have to manually input the function

![alt text](image.png)

