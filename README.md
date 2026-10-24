# ann_cw
CNN Unet+mobilenetv1 with apple core ml backed segmentation


Train model -> matix create at matrics dir

```bash`
dvc add checkpoints
dvc push

# add to git
git commit -m "Model v1.1: xxx"
git tag -a v1.1 -m "v1.1 weights"
git push origin developer --tags
```

From ios app side 
```
sh ./config/dvc_get.sh v1.1
```


