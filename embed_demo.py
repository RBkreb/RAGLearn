from src.pipeline.pipe import Pipeline

def main(filepath):
	PP=Pipeline()
	PP.execute(filepath)
if __name__=="__main__":
	main("inputs/documents.txt")