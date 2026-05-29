# Bernardo Vale e Pedro Aguiar

import sys
import random
import socket

import protocolo

class Servidor:
    def __init__(self, porta, senha, numeroTentativas):
        self.porta = porta
        self.tamanhoSenha = len(senha)
        self.senha = self._valida_ou_gera(senha)
        self.numeroTentativas = numeroTentativas
        self.tamanhoSenha = len(self.senha)
        self.sock = self._cria_socket()
        self.NA = len(self.senha)

    def _valida_ou_gera(self, senha):
        if not (4 <= len(senha) <= 8): # senha muito pequena ou grande
            sys.exit(1)

        if not senha.isdigit(): # digitos invalidos
            sys.exit(1)

        if all(c == '0' for c in senha): # senha aleatoria
            digitos = random.sample(range(10), len(senha))
            return [str(d) for d in digitos]

        if len(set(senha)) != len(senha): # digitos repetidos
            sys.exit(1)

        return list(senha)
    
    def _cria_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', self.porta))
        return sock
    
    def _processa_erro(self, codigoErro, endereco):
        
        resposta = protocolo.monta_err(codigoErro)
        self.sock.sendto(resposta, endereco)
        return resposta
    
    def _processa_hel(self, msg, endereco, cliente):

        if msg['tipo'] != protocolo.HEL or msg['numseq'] != 0:
            cliente['ultima_resposta'] = self._processa_erro(0, endereco)
            return

        padrao = ['?'] * self.NA + [' '] * (8 - self.NA)
        resp = protocolo.monta_res(self.numeroTentativas, padrao)
        self.sock.sendto(resp, endereco)

        cliente['ultima_resposta'] = resp
        cliente['ultimo_tipo'] = protocolo.HEL
        cliente['fase'] = 'TRY'
        cliente['numseq_esperado'] = 1
        return
    
    def _processa_try(self, msg, endereco, cliente):
        
        if msg['tipo'] != protocolo.TRY:
            cliente['ultima_resposta'] = self._processa_erro(0, endereco)
            return

        if msg['numseq'] != cliente['numseq_esperado']:
            cliente['ultima_resposta'] = self._processa_erro(0, endereco)
            return

        digitos = list(msg['payload'][:self.NA])
        tentativasRestantes = self.numeroTentativas - msg['numseq']

        # valida: valores 0-9
        if any(d > 9 for d in digitos):
            cliente['ultima_resposta'] = self._processa_erro(tentativasRestantes, endereco)
            return

        # valida: sem repetição
        if len(set(digitos)) != len(digitos):
            cliente['ultima_resposta'] = self._processa_erro(tentativasRestantes, endereco)
            return

        # calcula feedback
        senhaInt = [int(c) for c in self.senha]
        padrao = []
        for i in range(self.NA):
            if digitos[i] == senhaInt[i]:
                padrao.append('*')
            elif digitos[i] in senhaInt:
                padrao.append('+')
            else:
                padrao.append('-')
        padrao += [' '] * (8 - self.NA)
        resp = protocolo.monta_res(tentativasRestantes, padrao)
        self.sock.sendto(resp, endereco)

        cliente['ultima_resposta'] = resp
        cliente['ultimo_tipo'] = protocolo.TRY
        cliente['numseq_esperado'] += 1
        return
    
    def _processa_bye(self, msg, endereco, cliente):
        
        if msg['tipo'] != protocolo.BYE:
            cliente['ultima_resposta'] = self._processa_erro(0, endereco)
            return 0

        padrao = list(self.senha) + [' '] * (8 - self.NA)
        resp = protocolo.monta_res(-1, padrao)
        self.sock.sendto(resp, endereco)

        cliente['ultima_resposta'] = resp
        cliente['ultimo_tipo'] = protocolo.BYE
        cliente['fase'] = 'FIM'
        return 1
    
    def jogo(self):
        
        clientes = {}
        clientesFinalizados = 0

        while clientesFinalizados < 2:
            dados, endereco = self.sock.recvfrom(12)

            msg = protocolo.parse(dados)
            if msg is None:
                continue

            if endereco not in clientes:
                clientes[endereco] = {
                    'fase': 'HEL',
                    'numseq_esperado': 0,
                    'ultima_resposta': None,
                    'ultimo_tipo': None
                }

            cliente = clientes[endereco]

            # duplicata -> reenvia
            if (
                cliente['ultima_resposta']
                and msg['tipo'] == cliente['ultimo_tipo']
                and msg['numseq'] == cliente['numseq_esperado'] - 1
            ):
                self.sock.sendto(cliente['ultima_resposta'], endereco)
                continue

            if msg['tipo'] == protocolo.BYE and cliente['fase'] in ('HEL', 'TRY'):
                clientesFinalizados += self._processa_bye(msg, endereco, cliente)
            elif cliente['fase'] == 'HEL':
                self._processa_hel(msg, endereco, cliente)
            elif cliente['fase'] == 'TRY':
                self._processa_try(msg, endereco, cliente)

        self.sock.close()

def main():
    if len(sys.argv) != 4:
        # srv.py <porta> <senha> <NT>
        sys.exit(1)

    porta = int(sys.argv[1])
    senha = sys.argv[2]
    numeroTentativas = int(sys.argv[3])

    srv = Servidor(porta, senha, numeroTentativas)
    srv.jogo()

if __name__ == "__main__":
    main()