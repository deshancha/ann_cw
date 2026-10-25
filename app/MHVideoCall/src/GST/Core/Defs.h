#ifndef DEFS_H
#define DEFS_H

#include <string>

enum RenderType {
    NONE,           // No render, only for send video
    GLSINK,         // GLsink Renderer : Use GLSinkView
    APPSINK_OPENGL, // Appsink OpenGL Renderer : Use AppSinkGLView
    APPSINK_CG      // Appsink Apple Core Graphics Renderer
    
};

typedef struct  {
    bool sendVideo;
    bool sendAudio;
    bool receiveAudio;
    bool receiveVideo;
    RenderType receiveRenderType;
    RenderType senderRenderType;
    bool useLowBandWidth;
    
} Configuration;




// ======= Other ======

#define TAG std::string

static TAG V_RECEV_TAG = "RECEIVER_VIDEO";
static TAG V_SEND_TAG = "SENDER_VIDEO";
static TAG A_RECEV_TAG = "RECEIVER_AUDIO";
static TAG A_SEND_TAG = "SENDER_AUDIO";

#endif
