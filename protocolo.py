# Bernardo Vale dos Santos Bento
# Pedro Henrique Egito Aguiar

import struct

HEL = 1
TRY = 2
RES = 3
BYE = 4
ERR = 5

TAMANHO_CURTO = 4   # HEL, BYE, ERR
TAMANHO_LONGO = 12  # TRY, RES

def _checksum(dados: bytes) -> int:
    result = 0
    for b in dados:
        result ^= b
    return result

def _monta(tipo: int, numseq: int, payload: bytes = b'') -> bytes:
    # monta com checksum zerado, calcula XOR, substitui
    msg = struct.pack('!BBH', tipo, 0, numseq) + payload
    cs = _checksum(msg)
    return struct.pack('!BBH', tipo, cs, numseq) + payload

def monta_hel() -> bytes:
    return _monta(HEL, 0)

def monta_try(numseq: int, digitos: list) -> bytes:
    # digitos: lista de ints, ex [2,1,5,4]
    payload = bytes(digitos[:8]) + bytes(8 - len(digitos))
    return _monta(TRY, numseq, payload)

def monta_res(numseq: int, padrao: list) -> bytes:
    # padrao: lista de chars, ex ['*','-','+','*']
    numseq_u16 = numseq & 0xFFFF
    chars = [ord(c) for c in padrao]
    payload = bytes(chars[:8]) + bytes(8 - len(chars))
    return _monta(RES, numseq_u16, payload)

def monta_bye(numseq: int) -> bytes:
    return _monta(BYE, numseq)

def monta_err(numseq: int) -> bytes:
    return _monta(ERR, numseq)

def parse(dados: bytes) -> dict | None:
    
    if len(dados) not in (TAMANHO_CURTO, TAMANHO_LONGO):
        return None

    tipo, cs, numseq = struct.unpack('!BBH', dados[:4])

    # valida checksum: zera byte do cs e recalcula
    dados_sem_cs = struct.pack('!BBH', tipo, 0, numseq) + dados[4:]
    if _checksum(dados_sem_cs) != cs:
        return None
    
    numseq = -1 if numseq == 0xFFFF else numseq

    payload = dados[4:] if len(dados) == TAMANHO_LONGO else b''

    return {
        'tipo': tipo,
        'numseq': numseq,
        'payload': payload
    }