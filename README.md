# ann_cw
CNN Unet+mobilenetv1 with apple core ml backed segmentation

# Important stuff at begning 

```
source .venv/bin/activate
caffeinate -i python model_creation/main.py --task train_full --dataset matting_human --epochs 1
```

# Run MODEL creation

```
source .venv/bin/activate
python model_creation/main.py --env .env.quick --task train
python model_creation/main.py --env .env.quick --task validate
python model_creation/main.py --env .env.quick --task visualize
python model_creation/main.py --env .env.quick --task export_coreml
python model_creation/main.py --env .env.quick --task export_tflite
python model_creation/main.py --env .env.quick --task pipeline
```

# Train model -> matix create at matrics dir

```
source .venv/bin/activate
dvc add model_creation/output/checkpoints
dvc push

# add to git
git commit -m "Model v1.1: xxx"
git tag -a v1.1 -m "v1.1 weights"
git push origin developer --tags
```

# Fetch Model via Hugging Face Hub

Models are hosted on [Hugging Face: deshanc/unet-mobilenet-portrait-segmentation](https://huggingface.co/deshanc/unet-mobilenet-portrait-segmentation).

Download and prepare the CoreML model for the iOS app without needing DVC or credentials:

```bash
# Fetch latest/v1.3 (default):
sh ./app/config/hf_get.sh

# Or fetch a specific version (v1.0, v1.1, v1.2, v1.3):
sh ./app/config/hf_get.sh v1.2    #app/core_ios/Model/UNetMobileNetFull.mlpackage
```