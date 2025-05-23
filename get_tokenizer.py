import transformers

tokenizer = transformers.AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")

tokenizer.save_pretrained("tokenizers/llama")
