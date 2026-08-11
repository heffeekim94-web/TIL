Date: 2026 Aug 10, Monday

# Coding with C++ language

In order to have C++ language running in VS Code,
first we have to install the C++,

1. [Installing C++ Language](/Installing-Clang.md)

then create a file extended with '.cpp'.

2. [Hello-World]

To try and run the comiling system, g++ code must be inputed in 
bash terminal to see the immediate compiling result.

This will have the code just as follows:

3. g++ code
```bash
g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp
```

This command tells the compiler to use the C++17 standard, enable all warnings, 
and output an executable named `hello` from the source file `hello_world.cpp`.
make sure the file is saved before running the command.

To execute, need to write a command to run one last code on terminal

4. executing code
```bash
./hello
```

So whenever compiling is needed, repetition of these two code execution is
all it takes. 
```bash
g++ -Wall -Wextra -std=c++17 -o hello ./hello_world.cpp
./hello
```

The print will be:
```bash
Hello, World!
```

The result will shows up in the terminal.


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


