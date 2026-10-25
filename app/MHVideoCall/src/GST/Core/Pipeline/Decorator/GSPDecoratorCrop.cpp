//
//  GSPDecoratorCrop.cpp
//  avatarcore_ios
//
//  Created by Chamika Deshan on 5/25/21.
//

#include "GSPDecoratorCrop.h"
#include <gst/gst.h>

namespace AvatarIniOS
{
    namespace core {
    
        //------------------------------------------------------

        GSPDecoratorCrop::GSPDecoratorCrop(GSPipeline *inner, int left, int right, int top, int bottom) :
                GSPipelineDecorator(inner), v_left(left), v_right(right), v_top(top), v_bottom(bottom) {
            
        }

        //------------------------------------------------------

        GSPDecoratorCrop::~GSPDecoratorCrop() {
        }

        //------------------------------------------------------
    
        void GSPDecoratorCrop::init() {
            
            GSPipelineDecorator::init();
            
            GstElement* cropElement = gst_bin_get_by_name(GST_BIN(GSPipelineDecorator::getPipeLine()), "cropElement");
            
            g_object_set(cropElement, "left", v_left, NULL);
            g_object_set(cropElement, "right", v_right, NULL);
            g_object_set(cropElement, "top", v_top, NULL);
            g_object_set(cropElement, "bottom", v_bottom, NULL);
        }
    }
}
