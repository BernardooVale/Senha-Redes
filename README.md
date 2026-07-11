# Password Guessing Game — Bernardo Vale dos Santos Bento and Pedro Henrique Egito Aguiar

## 🇺🇸 English

### Files

| File | Purpose |
|---|---|
| `protocolo.py` | Builds, parses, and validates message checksums |
| `servidor.py` | Game logic, manages up to 2 simultaneous clients |
| `cliente.py` | Reads guesses from stdin and prints feedback |

---

### How to Run

```bash
# Server
python servidor.py <port> <password> <NT>

# Client (in another terminal)
python cliente.py <host> <port>
```

**Examples:**
```bash
python servidor.py 5000 3142 6   # fixed password
python servidor.py 5000 0000 6   # random password (all zeros)
```

### Password Restrictions

- 4–8 digits
- No repeated digits
- If all digits are `0`, the server generates a random password with unique digits

---

## Protocol (UDP)

All messages use an XOR checksum. Two message sizes are supported:

| Size | Messages |
|---|---|
| 4 bytes | `HEL`, `BYE`, `ERR` |
| 12 bytes | `TRY`, `RES` |

### Header Structure (4 bytes)

```
+--------+--------+--------+--------+
|  type  |   cs   |     seqnum      |
| 1 byte | 1 byte |     2 bytes     |
+--------+--------+--------+--------+
```

- `cs` = XOR of all bytes with `cs = 0`
- `seqnum = 0xFFFF` → interpreted as `-1` (used in the final `RES` message)

### Message Types

| Type | Value | Direction | Payload |
|---|---|---|---|
| `HEL` | 1 | Client → Server | — |
| `TRY` | 2 | Client → Server | 8 bytes: digits (0–9) |
| `RES` | 3 | Server → Client | 8 bytes: pattern using `*`, `+`, `-`, `?`, ` ` |
| `BYE` | 4 | Client → Server | — |
| `ERR` | 5 | Server → Client | — |

### Feedback Pattern (`RES` payload)

| Character | Meaning |
|---|---|
| `*` | Correct digit in the correct position |
| `+` | Correct digit in the wrong position |
| `-` | Digit is not present in the password |
| `?` | Position not yet revealed (response to `HEL`) |
| ` ` | Padding (positions beyond the password length) |

`seqnum` in `RES` = remaining attempts (`-1` = BYE, password revealed)

---

## Game Flow

```
Client                           Server
   |--- HEL (seqnum=0) ----------->|
   |<-- RES (NT, "????    ") -------|

   |--- TRY (seqnum=1, digits) ---->|
   |<-- RES (NT-1, "*+-*    ") -----|

   |--- TRY (seqnum=2, digits) ---->|
   |<-- RES (NT-2, "****    ") -----|   ← no attempts left or session ended

   |--- BYE (last_seqnum) --------->|
   |<-- RES (seqnum=-1, password) --|
```

- Duplicate messages are detected and answered by resending the previous response.
- The client retries each message up to 3 times before printing `NO RES` and terminating.

---

## Client Output

```
NA=4, NT=6          # password length, number of attempts
1(5) *+-*           # attempt 1, 5 remaining, feedback
2(4) **-*
3(3) ****           # no attempts left or session ended
Password=3142       # revealed after BYE
```

### Errors

| Message | Cause |
|---|---|
| `ERROR` | `ERR` with seqnum=0 (fatal protocol error) |
| `RETRY N` | `ERR` with seqnum>0 (invalid attempt, N attempts remaining) |
| `NO RES` | Three consecutive timeouts without a response |

---

## Error Conditions (Server Sends `ERR`)

| Situation | `seqnum` in `ERR` |
|---|---|
| Out-of-order message / invalid message type | 0 |
| Invalid digit (>9) in a guess | Remaining attempts |
| Repeated digits in a guess | Remaining attempts |

---

## Dependencies

Python 3.10+ (uses `dict | None` type hints). Standard library only: `socket`, `struct`, `random`, `sys`, `time`.

---

# 🇧🇷 Português

## Arquivos

| Arquivo | Função |
|---|---|
| `protocolo.py` | Montagem, parse e checksum de mensagens |
| `servidor.py` | Lógica do jogo, gerencia até 2 clientes simultâneos |
| `cliente.py` | Lê tentativas do stdin, imprime feedback |

---

## Como rodar

```bash
# Servidor
python servidor.py <porta> <senha> <NT>

# Cliente (outro terminal)
python cliente.py <host> <porta>
```

**Exemplos:**
```bash
python servidor.py 5000 3142 6   # senha fixa
python servidor.py 5000 0000 6   # senha aleatória (todos zeros)
```

### Restrições da senha

- 4–8 dígitos
- Sem dígitos repetidos
- Todos `0` → servidor gera senha aleatória com dígitos únicos

---

## Protocolo (UDP)

Todas as mensagens usam checksum XOR. Dois tamanhos possíveis:

| Tamanho | Mensagens |
|---|---|
| 4 bytes | `HEL`, `BYE`, `ERR` |
| 12 bytes | `TRY`, `RES` |

### Estrutura do cabeçalho (4 bytes)

```
+--------+--------+--------+--------+
|  tipo  |   cs   |     numseq      |
| 1 byte | 1 byte |     2 bytes     |
+--------+--------+--------+--------+
```

- `cs` = XOR de todos os bytes com `cs = 0`
- `numseq = 0xFFFF` → interpretado como `-1` (usado em `RES` final)

### Tipos de mensagem

| Tipo | Valor | Direção | Payload |
|---|---|---|---|
| `HEL` | 1 | Cliente → Servidor | — |
| `TRY` | 2 | Cliente → Servidor | 8 bytes: dígitos (0–9) |
| `RES` | 3 | Servidor → Cliente | 8 bytes: padrão `*`, `+`, `-`, `?`, ` ` |
| `BYE` | 4 | Cliente → Servidor | — |
| `ERR` | 5 | Servidor → Cliente | — |

### Padrão de feedback (RES payload)

| Char | Significado |
|---|---|
| `*` | Dígito certo, posição certa |
| `+` | Dígito certo, posição errada |
| `-` | Dígito ausente na senha |
| `?` | Posição ainda não revelada (resposta ao HEL) |
| ` ` | Padding (posições além do tamanho da senha) |

`numseq` em `RES` = tentativas restantes (`-1` = BYE, revela senha)

---

## Fluxo do jogo

```
Cliente                          Servidor
   |--- HEL (numseq=0) ------------>|
   |<-- RES (NT, "????    ") --------|

   |--- TRY (numseq=1, digitos) ---->|
   |<-- RES (NT-1, "*+-*    ") ------|

   |--- TRY (numseq=2, digitos) ---->|
   |<-- RES (NT-2, "****    ") ------|   ← tentativas esgotadas ou fim de sessão no terminal

   |--- BYE (ultimo_numseq) -------->|
   |<-- RES (numseq=-1, senha) ------|
```

- Duplicata detectada → servidor reenvia última resposta
- Cliente tenta até 3× por mensagem antes de imprimir `NO RES` e encerrar

---

## Saída do cliente

```
NA=4, NT=6          # tamanho da senha, número de tentativas
1(5) *+-*           # tentativa 1, 5 restantes, feedback
2(4) **-*
3(3) ****           # tentativas esgotadas ou fim de sessão no terminal
Senha=3142          # revelada no BYE
```

### Erros

| Mensagem | Causa |
|---|---|
| `ERRO` | ERR com numseq=0 (erro fatal de protocolo) |
| `RETRY N` | ERR com numseq>0 (tentativa inválida, N restantes) |
| `NO RES` | 3 timeouts consecutivos sem resposta |

---

## Condições de erro (servidor envia ERR)

| Situação | numseq em ERR |
|---|---|
| Mensagem fora de ordem / tipo errado | 0 |
| Dígito inválido (>9) na tentativa | tentativas restantes |
| Dígitos repetidos na tentativa | tentativas restantes |

---

## Dependências

Python 3.10+ (usa `dict | None` em type hint). Só biblioteca padrão: `socket`, `struct`, `random`, `sys`, `time`.
