from src.chain import chain_pipeline

def main():
	pipeline=chain_pipeline()
	response=pipeline.execute("岁月史书中说了什么")
	print(response)
if __name__=="__main__":
	main()