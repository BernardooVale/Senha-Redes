import sys
import random
import socket

class Servidor:
    def __init__(self, porta, senha, numeroTentativas):
        self.porta = porta
        self.senha = self._valida_ou_gera(senha)
        self.numeroTentativas = numeroTentativas
        self.tamanhoSenha = len(self.senha)
        self.sock = self._cria_socket()

    def _valida_ou_gera(self, senha):
        if not (4 <= len(senha) <= 8):
            # senha muito pequena ou grande
            sys.exit(1)

        if not senha.isdigit():
            # digitos invalidos
            sys.exit(1)

        if all(c == '0' for c in senha):
            digitos = random.sample(range(10), self.tamanhoSenha)
            return [str(d) for d in digitos]

        if len(set(senha)) != self.tamanhoSenha:
            # digitos repetidos
            sys.exit(1)

        return list(senha)
    
    def _cria_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind('0.0.0.0', self.porta)
        return sock
    
    def _processa_hel(self, dados, endereco, cliente):
        pass
    
    def _processa_try(self, dados, endereco, cliente):
        pass
    
    def _processa_bye(self, dados, endereco, cliente):
        pass
    
    def jogo(self):
        
        clientes = {}
        clientes_finalizados = 0

        while clientes_finalizados < 2:
            dados, endereco = self.sock.recvfrom(12)

            if not self._valida_checksum(dados):
                continue

            if endereco not in clientes:
                clientes[endereco] = {
                    'fase': 'HEL',
                    'numseq_esperado': 0,
                    'tentativas_usadas': 0,
                    'ultima_resposta': None
                }

            cliente = clientes[endereco]
            tipo, numseq = self._parse_tipo_numseq(dados)

            # duplicata → reenvia
            if numseq == cliente['numseq_esperado'] - 1 and cliente['ultima_resposta']:
                self.sock.sendto(cliente['ultima_resposta'], endereco)
                continue

            if cliente['fase'] == 'HEL':
                clientes_finalizados += self._processa_hel(dados, endereco, cliente)
            elif cliente['fase'] == 'TRY':
                clientes_finalizados += self._processa_try(dados, endereco, cliente)
            elif cliente['fase'] == 'BYE':
                clientes_finalizados += self._processa_bye(dados, endereco, cliente)
            else:
                self._envia_err(endereco, 0)

        self.sock.close()

def main():
    if len(sys.argv) != 4:
        # srv.py <porto> <senha> <NT>
        sys.exit(1)

    porto = int(sys.argv[1])
    senha = sys.argv[2]
    numeroTentativas = int(sys.argv[3])

    srv = Servidor(porto, senha, numeroTentativas)

if __name__ == "__main__":
    main()