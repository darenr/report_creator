all: kitchen_sink rougescore bertscore classification telemetry

kitchen_sink: examples/kitchen_sink.py
	PYTHONPATH=. python examples/kitchen_sink.py 

rougescore: examples/rougescore.py
	PYTHONPATH=. python examples/rougescore.py 

bertscore: examples/bertscore.py
	PYTHONPATH=. python examples/bertscore.py 

classification: examples/classification.py
	PYTHONPATH=. python examples/classification.py 

telemetry: examples/telemetry.py
	PYTHONPATH=. python examples/telemetry.py 
