#include "GSPDecoratorGLShader.h"
#include "IGSTCallback.h"

namespace AvatarIniOS
{
    namespace core {
    
        //------------------------------------------------------

        GSPDecoratorGLShader::GSPDecoratorGLShader(GSPipeline *inner, const char* frag, const char* vert) : GSPipelineDecorator(inner), mFrag(frag), mVert(vert){
            
        }

        GSPDecoratorGLShader::GSPDecoratorGLShader(GSPipeline *inner, const char* frag, const char* vert, const FloatUnifromMap &map) : GSPipelineDecorator(inner), mFrag(frag), mVert(vert), mUniformMap(map){

        }

        //------------------------------------------------------

        GSPDecoratorGLShader::~GSPDecoratorGLShader() {
        }

        //------------------------------------------------------
    
        void GSPDecoratorGLShader::init() {
            
            GSPipelineDecorator::init();

            GstElement* glShader = gst_bin_get_by_name(GST_BIN(GSPipelineDecorator::getPipeLine()), "glShader");

            if (mFrag != NULL)
                g_object_set(G_OBJECT(glShader), "fragment", mFrag, NULL);

            if (mVert != NULL)
                g_object_set(G_OBJECT(glShader), "vertex", mVert, NULL);

            // Passing unifroms to shader
            if (this->mUniformMap.size() > 0) {

                GstStructure* uniformsStruct = gst_structure_new_empty("SHADER_UNIFORM_MAP");

                for (const auto& [key, value] : mUniformMap) {
                    gst_structure_set(uniformsStruct, key.c_str(), G_TYPE_FLOAT, value, NULL);
                }

                g_object_set(G_OBJECT(glShader), "uniforms", uniformsStruct, NULL);

                gst_structure_free(uniformsStruct);
            }
        }
    }
}
