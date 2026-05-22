from src.pipeline.pipe import Pipeline


def main(directory_path: str = "./inputs", mode: str = "jsonl"):
    PP = Pipeline()
    PP.execute(directory_path, mode=mode)


if __name__ == "__main__":
    main()
