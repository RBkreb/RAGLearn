from src.pipeline.pipe import Pipeline


def main(directory_path: str = "./inputs"):
    PP = Pipeline()
    PP.execute(directory_path)


if __name__ == "__main__":
    main()
