//
// Created by Chamika Deshan on 05/19/21.
//

#include "AppLog.h"
#include <stdio.h>
#include <stdarg.h>




void AppLog::enable(bool enabled) {
    this->mLogEnabled = enabled;
}

void AppLog::logInfo(const char * format, ...) {
    if (mLogEnabled) {
        va_list argptr;
        va_start(argptr, format);
        printf("LOG_INF:");
        vfprintf(stdout, format, argptr);
        printf("\n");
        va_end(argptr);
        
    }
}

void AppLog::logWarn(const char * format, ...) {
    if (mLogEnabled) {
        va_list argptr;
        va_start(argptr, format);
        printf("LOG_WRN:");
        vfprintf(stdout, format, argptr);
        printf("\n");
        va_end(argptr);
        
    }
}

void AppLog::logError(const char * format, ...) {
    if (mLogEnabled) {
        va_list argptr;
        va_start(argptr, format);
        printf("LOG_ERR:");
        vfprintf(stderr, format, argptr);
        printf("\n");
        va_end(argptr);
        
    }
}

