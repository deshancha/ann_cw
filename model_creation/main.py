# Author: Chamika Deshan
# Model Creation Main Runner

import argparse
import os
import sys
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from di.container import AppContainer


def main():
    parser = argparse.ArgumentParser(description="Human Segmentation Pipeline Runner")
    parser.add_argument(
        "--env",
        type=str,
        default=".env",
        help="Config (default: .env, or .env.quick)",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="train",
        choices=[
            "train",
            "validate",
            "visualize",
            "export_coreml",
            "export_tflite",
            "pipeline",
            "check_timm",
        ],
        help="Task (default: train)",
    )
    args = parser.parse_args()

    # Load .env file
    env_file = os.path.join(CURRENT_DIR, os.path.basename(args.env))
    load_dotenv(dotenv_path=env_file, override=True)

    cfg = {
        "epochs": int(os.getenv("EPOCHS", "3")),
        "batch_size": int(os.getenv("BATCH_SIZE", "16")),
        "learning_rate": float(os.getenv("LEARNING_RATE", "0.001")),
        "img_size": int(os.getenv("IMG_SIZE", "224")),
        "seed": int(os.getenv("SEED", "42")),
        "width": float(os.getenv("WIDTH_MULTIPLIER", "1.0")),
        "device": os.getenv("DEVICE", "mps"),
        "max_train_samples": int(os.getenv("MAX_TRAIN_SAMPLES", "0")),
        "max_val_samples": int(os.getenv("MAX_VAL_SAMPLES", "0")),
        "segmentation_data_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("SEGMENTATION_DATA_DIR", "data/supervisely_person"))
        ),
        "matting_data_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("MATTING_DATA_DIR", "data/matting_human"))
        ),
        "checkpoints_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("CHECKPOINTS_DIR", "checkpoints"))
        ),
        "output_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("OUTPUT_DIR", "outputs"))
        ),
        "metrics_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("METRICS_DIR", "metrics"))
        ),
    }

    container = AppContainer()
    container.config.from_dict({"training": cfg})

    loader = container.matting_human_loader()
    best_pt_path = os.path.join(cfg["checkpoints_dir"], "unet_mobilenetv1_full_best.pt")

    # 1: Train
    if args.task == "train":
        usecase = container.train_model_usecase(data_loader=loader)
        usecase.execute(
            epochs=cfg["epochs"],
            batch_size=cfg["batch_size"],
            learning_rate=cfg["learning_rate"],
            img_size=cfg["img_size"],
            width=cfg["width"],
            seed=cfg["seed"],
            device=cfg["device"],
            checkpoints_dir=cfg["checkpoints_dir"],
            max_train_samples=cfg["max_train_samples"],
            max_val_samples=cfg["max_val_samples"],
        )

    # 2: Validate
    elif args.task == "validate":
        usecase = container.validate_model_usecase(data_loader=loader)
        usecase.execute(
            checkpoint_path=best_pt_path,
            batch_size=cfg["batch_size"],
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            metrics_dir=cfg["metrics_dir"],
            max_val_samples=cfg["max_val_samples"],
        )

    # 3: Visualize Result
    elif args.task == "visualize":
        usecase = container.visualize_validation_result_usecase(data_loader=loader)
        usecase.execute(
            checkpoint_path=best_pt_path,
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            output_dir=cfg["output_dir"],
        )

    # 4: Export CoreML
    elif args.task == "export_coreml":
        usecase = container.export_coreml_usecase()
        ml_path = os.path.join(cfg["checkpoints_dir"], "UNetMobileNetV1Full.mlpackage")
        usecase.execute(
            checkpoint_path=best_pt_path,
            output_path=ml_path,
            img_size=cfg["img_size"],
            width=cfg["width"],
        )

    # 5: Export TFLite
    elif args.task == "export_tflite":
        usecase = container.export_tflite_usecase()
        tflite_path = os.path.join(cfg["checkpoints_dir"], "mobilenet_v3_segm_256.tflite")
        usecase.execute(
            checkpoint_path=best_pt_path,
            output_path=tflite_path,
            img_size=256,
            width=cfg["width"],
        )

    # All: 1 -> 2 -> 3 -> 4 -> 5
    elif args.task == "pipeline":
        print("-------------- Train Model----------------\n")
        train_uc = container.train_model_usecase(data_loader=loader)
        train_res = train_uc.execute(
            epochs=cfg["epochs"],
            batch_size=cfg["batch_size"],
            learning_rate=cfg["learning_rate"],
            img_size=cfg["img_size"],
            width=cfg["width"],
            seed=cfg["seed"],
            device=cfg["device"],
            checkpoints_dir=cfg["checkpoints_dir"],
            max_train_samples=cfg["max_train_samples"],
            max_val_samples=cfg["max_val_samples"],
        )

        pt_to_use = train_res["best_pt"]

        print("-------------- Validate Model--------------\n")
        val_uc = container.validate_model_usecase(data_loader=loader)
        val_uc.execute(
            checkpoint_path=pt_to_use,
            batch_size=cfg["batch_size"],
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            metrics_dir=cfg["metrics_dir"],
            max_val_samples=cfg["max_val_samples"],
        )

        print("-------------- Visualize Validation Result--------------\n")
        vis_uc = container.visualize_validation_result_usecase(data_loader=loader)
        vis_uc.execute(
            checkpoint_path=pt_to_use,
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            output_dir=cfg["output_dir"],
        )

        print("-------------- Export Apple CoreML--------------\n")
        coreml_uc = container.export_coreml_usecase()
        ml_path = os.path.join(cfg["checkpoints_dir"], "UNetMobileNetV1Full.mlpackage")
        coreml_uc.execute(
            checkpoint_path=pt_to_use,
            output_path=ml_path,
            img_size=cfg["img_size"],
            width=cfg["width"],
        )

        print("-------------- Export TensorFlow Lite--------------\n")
        tflite_uc = container.export_tflite_usecase()
        tflite_path = os.path.join(cfg["checkpoints_dir"], "mobilenet_v3_segm_256.tflite")
        tflite_uc.execute(
            checkpoint_path=pt_to_use,
            output_path=tflite_path,
            img_size=256,
            width=cfg["width"],
        )

    elif args.task == "check_timm":
        usecase = container.check_timm_usecase()
        usecase.execute()


if __name__ == "__main__":
    main()
