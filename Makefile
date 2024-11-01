all: setup kitchen_sink

setup:
	@python3 -m pip install --upgrade pip
	@python3 -m pip install -qr requirements.txt -U

kitchen_sink: examples/kitchen_sink.py
	PYTHONPATH=. python examples/kitchen_sink.py 
