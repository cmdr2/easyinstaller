#include <iostream>

#include "easyinstaller_name.h"

int main() {
    std::cout << "Hello " << easyinstaller_name() << '\n';
    std::cout << "Press Enter to continue...";
    std::cin.get();
    return 0;
}
