//
// Created by Chamika Deshan on 5/27/21.
//

#ifndef ANDROID_GSPDECORATORFAKE_H
#define ANDROID_GSPDECORATORFAKE_H

#include <gst/gst.h>

#include "GSPipelineBuilder.h"
#include "GSPipelineDecorator.h"
#include "GSPipeline.h"

namespace AvatarIniOS
{
    namespace core {

        class GSPDecoratorFake : public GSPipelineDecorator {
            friend class GSPipelineBuilder;

        public:
            virtual ~GSPDecoratorFake();

            void init();

        protected:
            GSPDecoratorFake(GSPipeline *inner);
        };

    }  // namespace media
}  // namespace avatarflow


#endif //ANDROID_GSPDECORATORFAKE_H
