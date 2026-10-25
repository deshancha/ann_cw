#ifndef ANDROIDPINT_H
#define ANDROIDPINT_H

#if defined(__ANDROID__)
#include <android/log.h>
#define printf(...) LOG_DEBUG("CORE-PRINTF", __VA_ARGS__);

#define LOG_INFO(...) __android_log_print(ANDROID_LOG_INFO, "APP-INF", __VA_ARGS__);
#define LOG_ERROR(...) __android_log_print(ANDROID_LOG_ERROR, "APP-ERR", __VA_ARGS__);
#define LOG_DEBUG(...) __android_log_print(ANDROID_LOG_WARN, "APP-WRN", __VA_ARGS__);

#endif

#endif
