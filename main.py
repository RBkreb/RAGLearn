from src.chain import chain_pipeline

def main():
	pipeline=chain_pipeline()
	response=pipeline.execute("普京和非洲和平代表团干了什么")
	print(response)
if __name__=="__main__":
	main()