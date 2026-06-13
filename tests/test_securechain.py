import json
import threading
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from auditoria import monitor
from blockchain import blockchain
from usuarios import auth


class SecureChainTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.chain_file = self.root / "blockchain" / "chain.json"
        self.users_file = self.root / "usuarios" / "users.json"
        self.session_file = self.root / "usuarios" / "session.json"
        self.access_log = self.root / "logs" / "acessos.log"
        self.documents = self.root / "documentos"
        self.state_file = self.root / "auditoria" / "hashes.json"
        self.documents.mkdir(parents=True)

        self.patchers = [
            patch.object(blockchain, "CHAIN_FILE", self.chain_file),
            patch.object(auth, "USERS_FILE", self.users_file),
            patch.object(auth, "SESSION_FILE", self.session_file),
            patch.object(auth, "LOG_FILE", self.access_log),
            patch.object(auth, "registrar_evento", blockchain.registrar_evento),
            patch.object(monitor, "DOCUMENTS_DIR", self.documents),
            patch.object(monitor, "STATE_FILE", self.state_file),
            patch.object(monitor, "registrar_evento", blockchain.registrar_evento),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.temporary.cleanup()

    def test_blockchain_detects_tampering(self):
        blockchain.registrar_evento("evento inicial")
        chain = blockchain.carregar_cadeia()
        chain[0]["evento"] = "evento adulterado"
        blockchain.salvar_cadeia(chain)

        problems = blockchain.validar_cadeia()

        self.assertTrue(any("hash_atual invalido" in item for item in problems))
        with self.assertRaises(blockchain.BlockchainError):
            blockchain.registrar_evento("nao deve ser gravado")

    def test_invalid_json_is_reported(self):
        self.chain_file.parent.mkdir(parents=True)
        self.chain_file.write_text("{invalido", encoding="utf-8")

        problems = blockchain.validar_cadeia()

        self.assertTrue(any("Nao foi possivel ler" in item for item in problems))

    def test_concurrent_events_are_preserved(self):
        threads = [
            threading.Thread(
                target=blockchain.registrar_evento,
                args=(f"evento {index}",),
            )
            for index in range(20)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        chain = blockchain.carregar_cadeia()
        self.assertEqual(len(chain), 20)
        self.assertEqual(blockchain.validar_cadeia(), [])

    def test_authentication_and_profile_authorization(self):
        auth.cadastrar_usuario("admin1", "admin", "senha123")
        auth.cadastrar_usuario("visitante1", "visitante", "senha123")
        self.assertTrue(auth.login("visitante1", "senha123"))
        self.assertEqual(auth.require_permission("reports_read")["profile"], "visitante")
        with self.assertRaises(PermissionError):
            auth.require_permission("backup")

        self.assertTrue(auth.login("admin1", "senha123"))
        self.assertEqual(auth.require_permission("backup")["profile"], "admin")

    def test_monitor_detects_include_change_and_delete(self):
        first = self.documents / "primeiro.txt"
        first.write_text("versao 1", encoding="utf-8")
        monitor.initialize()

        first.write_text("versao 2", encoding="utf-8")
        (self.documents / "novo.txt").write_text("novo", encoding="utf-8")
        self.assertTrue(monitor.check(update_reference=True))

        first.unlink()
        self.assertTrue(monitor.check())

        events = [block["evento"] for block in blockchain.carregar_cadeia()]
        self.assertIn("Arquivo alterado: primeiro.txt", events)
        self.assertIn("Arquivo incluido: novo.txt", events)
        self.assertIn("Arquivo excluido: primeiro.txt", events)

    def test_last_admin_cannot_be_removed(self):
        auth.cadastrar_usuario("admin1", "admin", "senha123")
        with self.assertRaises(ValueError):
            auth.remover_usuario("admin1")

        auth.cadastrar_usuario("admin2", "admin", "senha123")
        auth.remover_usuario("admin2")
        users = json.loads(self.users_file.read_text(encoding="utf-8"))
        self.assertNotIn("admin2", users)


if __name__ == "__main__":
    unittest.main()
