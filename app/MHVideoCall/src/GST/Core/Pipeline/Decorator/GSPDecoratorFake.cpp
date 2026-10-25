//
// Created by Chamika Deshan on 5/27/21.
//

#include "GSPDecoratorFake.h"

namespace AvatarIniOS
{
    namespace core {
//------------------------------------------------------

GSPDecoratorFake::GSPDecoratorFake(GSPipeline *inner) : GSPipelineDecorator(inner){

}

//------------------------------------------------------

GSPDecoratorFake::~GSPDecoratorFake() {
}

//------------------------------------------------------

void GSPDecoratorFake::init() {

    GSPipelineDecorator::init();
}

}  // namespace media
}  // namespace avatarflow