# ann_cw
CNN Unet+mobilenetv1 with apple core ml backed segmentation

# Important stuff at begning 
```bash`
source .venv/bin/activate
caffeinate -i python model_creation/main.py --task train_full --dataset matting_human --epochs 1
```


Train model -> matix create at matrics dir

```bash`
dvc add model_creation/output/checkpoints
dvc push

# add to git
git commit -m "Model v1.1: xxx"
git tag -a v1.1 -m "v1.1 weights"
git push origin developer --tags
```

From ios app side 
```bash
cd '/Users/chamikadeshan/Documents/Projects/Avatarin/avatarin_ios_app'
sh ./config/dvc_get.sh v1.2
```

```
source .venv/bin/activate
python model_creation/main.py --env .env.quick --task train
python model_creation/main.py --env .env.quick --task validate
python model_creation/main.py --env .env.quick --task visualize
python model_creation/main.py --env .env.quick --task export_coreml
python model_creation/main.py --env .env.quick --task export_tflite
python model_creation/main.py --env .env.quick --task pipeline
```