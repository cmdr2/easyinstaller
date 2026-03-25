#pragma once

#if defined(_WIN32)
#if defined(EASYINSTALLER_NAME_EXPORTS)
#define EASYINSTALLER_NAME_API __declspec(dllexport)
#else
#define EASYINSTALLER_NAME_API __declspec(dllimport)
#endif
#elif defined(__GNUC__)
#define EASYINSTALLER_NAME_API __attribute__((visibility("default")))
#else
#define EASYINSTALLER_NAME_API
#endif

extern "C" EASYINSTALLER_NAME_API const char* easyinstaller_name();
