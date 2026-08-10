#include <iostream>
#include <string>
#include <cmath>

int add(int a, int b){
        return a + b;
}

int subt(int a, int b){
    return a - b;
}

int mult(int a, int b){
    return a * b;
}

int divide(int a, int b){
    return a / b;
}

int main() {
    int num1, num2;
    std::string method;

    
    std::cout << "Enter method you'd like to calc: +,-,*,/: ";
    std::cin >> method;

    std::cout << "Enter two integers: ";
    std::cin >> num1 >> num2;
    
    if (method == "+"){
        int sum = add(num1, num2);
        std::cout << "The Sum is: " << sum << std::endl;
        
    }

    else if (method == "-"){
        int subtract = subt(num1,num2);
        std::cout << "The Subtraction is: " << subtract << std::endl;
    
    }

    else if (method == "*"){
        int multiple = mult(num1,num2);
        std::cout << "The Multiplication of " << num1 << "and" << num2 << "is " << multiple << std::endl;
    }
    
    else if (method == "/"){
        if (num2 == 0) {
            std::cout << "Cannot divide by zero." << std::endl;
        }
        else {
            int division = divide(num1, num2);
            std::cout << "The Division is: " << division << std::endl;
        } 
    
    }

    else {
        std::cout << "Calculation process unrecognizable.";
    }

    return 0;
    // instead of while loop, you can use a for loop to achieve the same result:
}