import pathlib
import socket
import subprocess
import threading
import time
import unittest
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON = 'python3'
HOST = '127.0.0.1'

sys.path.insert(0, str(ROOT))

import protocolo


def free_udp_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def start_server(password='1234', nt='6'):
    port = free_udp_port()
    proc = subprocess.Popen(
        [PYTHON, str(ROOT / 'servidor.py'), str(port), password, nt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.5)
    return proc, port


def run_client(port, stdin_text):
    return subprocess.run(
        [PYTHON, str(ROOT / 'cliente.py'), HOST, str(port)],
        input=stdin_text,
        text=True,
        capture_output=True,
        timeout=10,
    )


def recv_parsed(sock, timeout=2.0):
    sock.settimeout(timeout)
    data, _ = sock.recvfrom(1024)
    return protocolo.parse(data)


class SenhaRedesTests(unittest.TestCase):
    def assert_server_finished(self, proc):
        out, err = proc.communicate(timeout=5)
        self.assertEqual(proc.returncode, 0, msg=f'server stdout={out!r} stderr={err!r}')

    def test_initialization_interaction_termination(self):
        proc, port = start_server()
        try:
            result = run_client(port, '1234\n')
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                [line.strip() for line in result.stdout.splitlines() if line.strip()],
                ['NA=4, NT=6', '1(5) ****', 'Senha=1234'],
            )

            second = run_client(port, '1234\n')
            self.assertEqual(second.returncode, 0, msg=second.stderr)
        finally:
            self.assert_server_finished(proc)

    def test_try_err(self):
        proc, port = start_server()
        try:
            result = run_client(port, '1111\n1234\n')
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                [line.strip() for line in result.stdout.splitlines() if line.strip()],
                ['NA=4, NT=6', 'RETRY 5', '1(5) ****', 'Senha=1234'],
            )

            second = run_client(port, '1234\n')
            self.assertEqual(second.returncode, 0, msg=second.stderr)
        finally:
            self.assert_server_finished(proc)

    def test_unexpected_type_err0(self):
        proc, port = start_server()
        addr = (HOST, port)
        temp = None
        sock = None
        sock2 = None
        try:
            temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp.settimeout(2.0)
            temp.sendto(protocolo.monta_try(1, [1, 2, 3, 4]), addr)
            msg = recv_parsed(temp)
            self.assertEqual(msg['tipo'], protocolo.ERR)
            self.assertEqual(msg['numseq'], 0)
            temp.close()

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(protocolo.monta_hel(), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 6)

            sock.sendto(protocolo.monta_try(1, [1, 2, 3, 4]), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 5)

            sock.sendto(protocolo.monta_bye(1), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], -1)

            sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock2.sendto(protocolo.monta_hel(), addr)
            msg = recv_parsed(sock2)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 6)
            sock2.sendto(protocolo.monta_try(1, [1, 2, 3, 4]), addr)
            msg = recv_parsed(sock2)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 5)
            sock2.sendto(protocolo.monta_bye(1), addr)
            msg = recv_parsed(sock2)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], -1)
            sock2.close()
        finally:
            if temp is not None:
                temp.close()
            if sock is not None:
                sock.close()
            if sock2 is not None:
                sock2.close()
            self.assert_server_finished(proc)

    def test_hel_duplicate_replies_again(self):
        proc, port = start_server()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (HOST, port)
        try:
            sock.sendto(protocolo.monta_hel(), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 6)

            sock.sendto(protocolo.monta_hel(), addr)
            msg_dup = recv_parsed(sock)
            self.assertEqual(msg_dup['tipo'], protocolo.RES)
            self.assertEqual(msg_dup['numseq'], 6)

            sock.sendto(protocolo.monta_bye(0), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], -1)

            sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock2.settimeout(2.0)
            sock2.sendto(protocolo.monta_hel(), addr)
            msg = recv_parsed(sock2)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 6)
            sock2.sendto(protocolo.monta_bye(0), addr)
            msg = recv_parsed(sock2)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], -1)
            sock2.close()
        finally:
            sock.close()
            self.assert_server_finished(proc)

    def test_last_try_moves_to_bye(self):
        proc, port = start_server(nt='1')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (HOST, port)
        try:
            sock.sendto(protocolo.monta_hel(), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 1)

            sock.sendto(protocolo.monta_try(1, [1, 2, 3, 4]), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 0)

            sock.sendto(protocolo.monta_try(2, [1, 2, 3, 4]), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.ERR)
            self.assertEqual(msg['numseq'], 0)

            sock.sendto(protocolo.monta_bye(1), addr)
            msg = recv_parsed(sock)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], -1)

            sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock2.settimeout(2.0)
            sock2.sendto(protocolo.monta_hel(), addr)
            msg = recv_parsed(sock2)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], 1)
            sock2.sendto(protocolo.monta_bye(0), addr)
            msg = recv_parsed(sock2)
            self.assertEqual(msg['tipo'], protocolo.RES)
            self.assertEqual(msg['numseq'], -1)
            sock2.close()
        finally:
            sock.close()
            self.assert_server_finished(proc)

    def test_client_ignores_invalid_input_line(self):
        proc, port = start_server()
        try:
            result = run_client(port, 'abcd\n1234\n')
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                [line.strip() for line in result.stdout.splitlines() if line.strip()],
                ['NA=4, NT=6', '1(5) ****', 'Senha=1234'],
            )

            second = run_client(port, '1234\n')
            self.assertEqual(second.returncode, 0, msg=second.stderr)
        finally:
            self.assert_server_finished(proc)

    def test_loss_corruption_and_duplication(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        srv.bind((HOST, 0))
        port = srv.getsockname()[1]
        state = {'hel_count': 0, 'try_count': 0}

        def fake_server():
            while True:
                data, addr = srv.recvfrom(1024)
                msg = protocolo.parse(data)
                if msg is None:
                    continue
                if msg['tipo'] == protocolo.HEL:
                    state['hel_count'] += 1
                    if state['hel_count'] == 1:
                        continue
                    srv.sendto(protocolo.monta_res(6, ['?'] * 4 + [' '] * 4), addr)
                elif msg['tipo'] == protocolo.TRY:
                    state['try_count'] += 1
                    if state['try_count'] == 1:
                        bad = bytearray(protocolo.monta_res(5, ['*', '*', '*', '*', ' ', ' ', ' ', ' ']))
                        bad[1] ^= 0xFF
                        srv.sendto(bytes(bad), addr)
                    srv.sendto(protocolo.monta_res(5, ['*', '*', '*', '*', ' ', ' ', ' ', ' ']), addr)
                elif msg['tipo'] == protocolo.BYE:
                    srv.sendto(protocolo.monta_res(-1, list('1234') + [' '] * 4), addr)
                    break

        thread = threading.Thread(target=fake_server, daemon=True)
        thread.start()
        try:
            result = run_client(port, '1234\n')
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                [line.strip() for line in result.stdout.splitlines() if line.strip()],
                ['NA=4, NT=6', '1(5) ****', 'Senha=1234'],
            )
        finally:
            srv.close()

    def test_concurrent_clients(self):
        proc, port = start_server()
        results = []

        def job():
            results.append(run_client(port, '1234\n'))

        threads = [threading.Thread(target=job) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        try:
            self.assertEqual(len(results), 2)
            for result in results:
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertEqual(
                    [line.strip() for line in result.stdout.splitlines() if line.strip()],
                    ['NA=4, NT=6', '1(5) ****', 'Senha=1234'],
                )
        finally:
            self.assert_server_finished(proc)


if __name__ == '__main__':
    unittest.main(verbosity=2)
