all: setup kitchen_sink

setup:
	pip install -qr requirements.txt -U

kitchen_sink: examples/kitchen_sink.py
	PYTHONPATH=. python examples/kitchen_sink.py 
