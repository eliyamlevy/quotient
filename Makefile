default:
	conda activate quotient
	echo "Hello the options are: start-server, app" 

start-server:
	llama-server -m Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf --jinja --temp 0.15 --top-k -1 --top-p 1.00 -ngl 99

app:
	python noam/app.py

