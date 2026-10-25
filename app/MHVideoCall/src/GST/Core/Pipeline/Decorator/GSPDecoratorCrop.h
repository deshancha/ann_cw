//
//  GSPDecoratorCrop.h
//  avatarcore_ios
//
//  Created by Chamika Deshan on 5/25/21.
//

#ifndef GSPDecoratorAspectRatio_hpp
#define GSPDecoratorAspectRatio_hpp

#include <stdio.h>
#include <iostream>

#include "GSPipelineBuilder.h"
#include "GSPipelineDecorator.h"
#include "GSPipeline.h"

namespace AvatarIniOS
{
    namespace core {

class GSPDecoratorCrop : public GSPipelineDecorator {
    friend class GSPipelineBuilder;

   public:
    virtual ~GSPDecoratorCrop();

    void init();

   protected:
    GSPDecoratorCrop(GSPipeline* inner, int left, int right, int top, int bottom);

    int v_left;
    int v_right;
    int v_top;
    int v_bottom;
};
}  // namespace media
}  // namespace avatarflow

#endif /* GSPDecoratorAspectRatio_hpp */
