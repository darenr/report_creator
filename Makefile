all: setup kitchen_sink rougescore bertscore telemetry

setup:
	pip install -qr requirements.txt -U
	pip install -qr requirements-examples.txt -U

kitchen_sink: examples/kitchen_sink.py
	PYTHONPATH=. python examples/kitchen_sink.py 

rougescore: examples/rougescore.py
	PYTHONPATH=. python examples/rougescore.py 

bertscore: examples/bertscore.py
	PYTHONPATH=. python examples/bertscore.py 

telemetry: examples/telemetry.py
	PYTHONPATH=. python examples/telemetry.py 
