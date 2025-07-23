default:
	conda activate quotient
	echo "Hello the options are: start-server, app" 

start-server:
	ollama serve

app:
	python noam/app.py

