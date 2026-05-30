.PHONY: run_serv run_cli

run_serv: servidor.py protocolo.py
	python3 servidor.py $(arg1) $(arg2) $(arg3)

run_cli: cliente.py protocolo.py
	python3 cliente.py $(arg1) $(arg2)