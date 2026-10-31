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
        default="config/train/.env.quick",
        help="config/train/.env.quick or config/test/.env.v1.3",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="train",
        choices=[
            "train",
            "validate",
            "test",
            "visualize",
            "export_coreml",
            "export_tflite",
            "pipeline",
            "check_timm",
            "benchmark",
        ],
        help="Task (default: train)",
    )
    args = parser.parse_args()

    # Resolve and load .env file
    root_dir = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
    candidate_paths = [
        args.env,
        os.path.join(root_dir, args.env),
        os.path.join(root_dir, "config", "train", args.env),
        os.path.join(root_dir, "config", "test", args.env),
        os.path.join(root_dir, "config", "benchmark", args.env),
        os.path.join(CURRENT_DIR, args.env),
    ]
    env_file = next((os.path.abspath(p) for p in candidate_paths if os.path.isfile(p)), None)

    if not env_file:
        raise FileNotFoundError(
            f"Config file not found for '{args.env}'. "
            f"Please specify a valid file in config/train/ or config/test/ (e.g. --env config/train/.env.quick or --env .env.quick)"
        )

    load_dotenv(dotenv_path=env_file, override=True)
    print(f"Loaded config: {env_file}")

    # Load global config (.env.global)
    global_candidates = [
        os.path.join(root_dir, "config", ".env.global")
    ]
    global_env_file = next((p for p in global_candidates if os.path.isfile(p)), None)
    if global_env_file:
        load_dotenv(dotenv_path=global_env_file, override=False)
        print(f"Loaded global config: {global_env_file}")

    cfg = {
        "model_type": os.getenv("MODEL_TYPE", "mobilenetv3"),
        "epochs": int(os.getenv("EPOCHS", "3")),
        "batch_size": int(os.getenv("BATCH_SIZE", "16")),
        "learning_rate": float(os.getenv("LEARNING_RATE", "0.001")),
        "img_size": int(os.getenv("IMG_SIZE", "224")),
        "seed": int(os.getenv("SEED", "42")),
        "width": float(os.getenv("WIDTH_MULTIPLIER", "1.0")),
        "device": os.getenv("DEVICE", "mps"),
        "max_train_samples": int(os.getenv("MAX_TRAIN_SAMPLES", "0")),
        "max_val_samples": int(os.getenv("MAX_VAL_SAMPLES", "0")),
        "max_test_samples": int(os.getenv("MAX_TEST_SAMPLES", "0")),
        "segmentation_data_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("SEGMENTATION_DATA_DIR", "data/supervisely_person"))
        ),
        "matting_data_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("MATTING_DATA_DIR", "data/matting_human"))
        ),
        "checkpoints_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("CHECKPOINTS_DIR", "model_creation/output/checkpoints"))
        ),
        "output_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("OUTPUT_DIR", "model_creation/output/gen_images"))
        ),
        "metrics_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("METRICS_DIR", "model_creation/output/metrics"))
        ),
        "experiments_dir": os.path.abspath(
            os.path.join(CURRENT_DIR, "..", os.getenv("EXPERIMENTS_DIR", "model_creation/output/experiments"))
        ),
        "checkpoint_path": os.getenv("CHECKPOINT_PATH", ""),
    }

    container = AppContainer()
    container.config.from_dict({"training": cfg})

    loader = container.matting_human_loader()
    model_type = cfg["model_type"]
    best_pt_path = os.path.join(cfg["checkpoints_dir"], f"unet_{model_type}_best.pt")
    target_pt_path = (
        os.path.abspath(os.path.join(CURRENT_DIR, "..", cfg["checkpoint_path"]))
        if cfg["checkpoint_path"]
        else best_pt_path
    )

    # 1: Train
    if args.task == "train":
        usecase = container.train_model_usecase(data_loader=loader)
        usecase.execute(
            model_type=model_type,
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
            model_type=model_type,
            batch_size=cfg["batch_size"],
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            metrics_dir=cfg["metrics_dir"],
            max_val_samples=cfg["max_val_samples"],
        )

    # 2b: Test
    elif args.task == "test":
        usecase = container.test_model_usecase(data_loader=loader)
        usecase.execute(
            checkpoint_path=target_pt_path,
            model_type=model_type,
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            output_dir=cfg["metrics_dir"],
            max_test_samples=cfg["max_test_samples"],
        )

    # 3: Visualize Result
    elif args.task == "visualize":
        usecase = container.visualize_validation_result_usecase(data_loader=loader)
        usecase.execute(
            checkpoint_path=best_pt_path,
            model_type=model_type,
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            output_dir=cfg["output_dir"],
        )

    # 4: Export CoreML
    elif args.task == "export_coreml":
        usecase = container.export_coreml_usecase()
        ml_path = os.path.join(cfg["checkpoints_dir"], f"UNet_{model_type}.mlpackage")
        usecase.execute(
            checkpoint_path=best_pt_path,
            output_path=ml_path,
            model_type=model_type,
            img_size=cfg["img_size"],
            width=cfg["width"],
        )

    # 5: Export TFLite
    elif args.task == "export_tflite":
        usecase = container.export_tflite_usecase()
        tflite_path = os.path.join(cfg["checkpoints_dir"], f"{model_type}_segm_256.tflite")
        usecase.execute(
            checkpoint_path=best_pt_path,
            output_path=tflite_path,
            model_type=model_type,
            img_size=256,
            width=cfg["width"],
        )

    # All: 1 -> 2 -> 3 -> 4 -> 5
    elif args.task == "pipeline":
        print(f"-------------- Train Model ({model_type}) ----------------\n")
        train_uc = container.train_model_usecase(data_loader=loader)
        train_res = train_uc.execute(
            model_type=model_type,
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

        print(f"-------------- Validate Model ({model_type}) --------------\n")
        val_uc = container.validate_model_usecase(data_loader=loader)
        val_uc.execute(
            checkpoint_path=pt_to_use,
            model_type=model_type,
            batch_size=cfg["batch_size"],
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            metrics_dir=cfg["metrics_dir"],
            max_val_samples=cfg["max_val_samples"],
        )

        print(f"-------------- Visualize Validation Result ({model_type}) --------------\n")
        vis_uc = container.visualize_validation_result_usecase(data_loader=loader)
        vis_uc.execute(
            checkpoint_path=pt_to_use,
            model_type=model_type,
            img_size=cfg["img_size"],
            width=cfg["width"],
            device=cfg["device"],
            output_dir=cfg["output_dir"],
        )

        print(f"-------------- Export Apple CoreML ({model_type}) --------------\n")
        coreml_uc = container.export_coreml_usecase()
        ml_path = os.path.join(cfg["checkpoints_dir"], f"UNet_{model_type}.mlpackage")
        coreml_uc.execute(
            checkpoint_path=pt_to_use,
            output_path=ml_path,
            model_type=model_type,
            img_size=cfg["img_size"],
            width=cfg["width"],
        )

        print(f"-------------- Export TensorFlow Lite ({model_type}) --------------\n")
        tflite_uc = container.export_tflite_usecase()
        tflite_path = os.path.join(cfg["checkpoints_dir"], f"{model_type}_segm_256.tflite")
        tflite_uc.execute(
            checkpoint_path=pt_to_use,
            output_path=tflite_path,
            model_type=model_type,
            img_size=256,
            width=cfg["width"],
        )

    elif args.task == "check_timm":
        usecase = container.check_timm_usecase()
        usecase.execute()

    elif args.task == "benchmark":
        usecase = container.eval_grabcut_benchmark_usecase()
        samples = int(os.getenv("MAX_BENCHMARK_SAMPLES", "50"))
        usecase.execute(
            checkpoint_path=target_pt_path,
            model_type=model_type,
            width=cfg["width"],
            img_size=cfg["img_size"],
            device=cfg["device"],
            num_samples=samples,
            output_dir=cfg["output_dir"],
        )


if __name__ == "__main__":
    main()
