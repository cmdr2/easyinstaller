#include <iostream>
#include <string_view>

#include "easyinstaller_name.h"

int main(int argc, char* argv[]) {
    bool headless = false;
    for (int index = 1; index < argc; ++index) {
        if (std::string_view(argv[index]) == "--headless") {
            headless = true;
        }
    }

    std::cout << "Hello " << easyinstaller_name() << '\n';
    if (!headless) {
        std::cout << "Press Enter to continue...";
        std::cin.get();
    }
    return 0;
}
