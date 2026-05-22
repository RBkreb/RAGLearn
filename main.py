from src.chain import chain_pipeline

def main():
	pipeline=chain_pipeline()
	response=pipeline.execute("Which film featured Destiny's Child's first major single?")
	print(response)
if __name__=="__main__":
	main()