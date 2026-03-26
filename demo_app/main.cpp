#include <portable-file-dialogs.h>

#include <iostream>
#include <string>
#include <string_view>

#include "demo_name.h"

int main(int argc, char* argv[]) {
    bool headless = false;
    for (int index = 1; index < argc; ++index) {
        if (std::string_view(argv[index]) == "--headless") {
            headless = true;
        }
    }

    const std::string greeting = std::string("Hello ") + demo_name();
    std::cout << greeting << '\n';
    if (!headless) {
        pfd::message("DemoEasyInstaller", greeting, pfd::choice::ok, pfd::icon::info).result();
    }
    return 0;
}
