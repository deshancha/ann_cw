# ann_cw
- CNN Unet+mobilenetv1 with apple core ml backed segmentation. 
- UNet + Mobilenetv3 transfer learning

# Run MODEL creation

```
source .venv/bin/activate
python model_creation/main.py --env config/train/.env.quick --task train
python model_creation/main.py --env config/train/.env.quick --task validate
python model_creation/main.py --env config/train/.env.quick --task visualize
python model_creation/main.py --env config/train/.env.quick --task export_coreml
python model_creation/main.py --env config/train/.env.quick --task export_tflite
python model_creation/main.py --env config/train/.env.quick --task pipeline

python model_creation/main.py --env config/test/.env.v1.0 --task test
python model_creation/main.py --env config/test/.env.v1.1 --task test
python model_creation/main.py --env config/test/.env.v1.2 --task test
python model_creation/main.py --env config/test/.env.v1.3 --task test

python model_creation/main.py --env config/benchmark/.env.v1.0 --task benchmark
python model_creation/main.py --env config/benchmark/.env.v1.1 --task benchmark
python model_creation/main.py --env config/benchmark/.env.v1.2 --task benchmark
python model_creation/main.py --env config/benchmark/.env.v1.3 --task benchmark

```

# Fetch all models

From [Hugging Face](https://huggingface.co/deshanc/unet-mobilenet-portrait-segmentation).

```bash
# 1. Fetch ALL 4 trained checkpoints into model_creation/output/all_trained/
sh ./config/hf_get_all.sh

# 2. Fetch specific version into iOS app (v1.0, v1.1, v1.2, v1.3)
sh ./app/config/hf_get.sh v1.2    # app/core_ios/Model/UNetMobileNetFull.mlpackage
```

# Publish Model to Hugging Face

## .env.secret

```
HF_TOKEN=HUGGING_FACE_WRITABLE_ACCESS_TOKEN_HERE
```

```bash
# Upload to Hugging Face
sh ./app/config/hf_push.sh v1.4

# Can use HF CLI directly
hf upload deshanc/unet-mobilenet-portrait-segmentation ./model_creation/output/checkpoints/ v1.4

# Add to git for reproducability purposes
git commit -m "Model v1.4: xxx"
git tag -a v1.4 -m "v1.4 release"
git push origin developer --tags
```

# Fetch Model via Hugging Face Hub

Hosted on [Hugging Face](https://huggingface.co/deshanc/unet-mobilenet-portrait-segmentation).

```bash
# Fetch v1.2 (default)`
sh ./app/config/hf_get.sh

# Fetch a version (v1.0, v1.1, v1.2, v1.3)
sh ./app/config/hf_get.sh v1.2    #app/core_ios/Model/UNetMobileNetFull.mlpackage
```