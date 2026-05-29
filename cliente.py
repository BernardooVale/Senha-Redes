# Bernardo Vale e Pedro Aguiar
import socket
import sys
import time

import protocolo


class Cliente:
	def __init__(self, host, porta):
		self.host = host
		self.porta = porta
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.NT = 0
		self.NA = 0
		self.ultimo_numseq = 0
		self.proximo_numseq = 1

	def _envia_e_recebe(self, msg):
		tentativas_timeout = 0
		endereco = (self.host, self.porta)

		while tentativas_timeout < 3:
			self.sock.sendto(msg, endereco)
			fim_espera = time.monotonic() + 1.0

			while True:
				restante = fim_espera - time.monotonic()
				if restante <= 0:
					tentativas_timeout += 1
					break

				self.sock.settimeout(restante)
				try:
					dados, _ = self.sock.recvfrom(12)
				except socket.timeout:
					tentativas_timeout += 1
					break

				resposta = protocolo.parse(dados)
				if resposta is None:
					continue

				return resposta

		print("NO RES")
		sys.exit(1)

	def handshake(self):
		msg = protocolo.monta_hel()
		resposta = self._envia_e_recebe(msg)
		self.NT = resposta['numseq']
		self.NA = resposta['payload'][:8].count(ord('?'))
		print("NA=%d, NT=%d" % (self.NA, self.NT), flush=True)

	def jogar(self):
		entrada = iter(sys.stdin)

		while True:
			if self.proximo_numseq > self.NT:
				self.encerrar(self.ultimo_numseq)

			try:
				linha = next(entrada)
			except (StopIteration, EOFError):
				self.encerrar(self.ultimo_numseq)

			digitos = [int(c) for c in linha.strip()]
			resposta = self._envia_e_recebe(
				protocolo.monta_try(self.proximo_numseq, digitos)
			)

			if resposta['tipo'] == protocolo.RES:
				padrao_str = bytes(resposta['payload'][:self.NA]).decode('ascii')
				print(
					"%d(%d) %s" % (self.proximo_numseq, resposta['numseq'], padrao_str),
					flush=True,
				)
				self.ultimo_numseq = self.proximo_numseq
				self.proximo_numseq += 1
				continue

			if resposta['tipo'] == protocolo.ERR:
				if resposta['numseq'] > 0:
					print("RETRY %d" % resposta['numseq'], flush=True)
					continue

				print("ERRO", flush=True)
				sys.exit(1)

	def encerrar(self, ultimo_numseq):
		resposta = self._envia_e_recebe(protocolo.monta_bye(ultimo_numseq))
		senha_str = bytes(resposta['payload'][:self.NA]).decode('ascii')
		print("Senha=%s" % senha_str, flush=True)
		sys.exit(0)


def main():
	if len(sys.argv) != 3:
		sys.exit(1)

	cliente = Cliente(sys.argv[1], int(sys.argv[2]))
	try:
		cliente.handshake()
		cliente.jogar()
	finally:
		cliente.sock.close()


if __name__ == "__main__":
	main()
