default:
	conda activate quotient
	echo "Hello the options are: start-server, app, test, test-quick" 

start-server:
	ollama serve

app:
	python noam/app.py

test:
	cd noam && python simple_test.py

test-quick:
	cd noam && python simple_test.py --quick

test-pytest:
	cd noam && python run_tests.py

test-coverage:
	cd noam && python run_tests.py --coverage

