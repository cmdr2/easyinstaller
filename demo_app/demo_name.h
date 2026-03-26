#pragma once

#if defined(_WIN32)
#if defined(DEMO_NAME_BUILD_SHARED)
#define DEMO_NAME_API __declspec(dllexport)
#else
#define DEMO_NAME_API __declspec(dllimport)
#endif
#elif defined(__GNUC__)
#define DEMO_NAME_API __attribute__((visibility("default")))
#else
#define DEMO_NAME_API
#endif

DEMO_NAME_API const char* demo_name();