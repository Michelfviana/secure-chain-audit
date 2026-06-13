#!/usr/bin/env python3
import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CHAIN_FILE = BASE_DIR / "chain.json"
REQUIRED_FIELDS = {"id", "timestamp", "evento", "hash_anterior", "hash_atual"}


class BlockchainError(Exception):
    pass


@contextmanager
def _chain_lock():
    lock_file = CHAIN_FILE.with_suffix(CHAIN_FILE.suffix + ".lock")
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with lock_file.open("a", encoding="utf-8") as file:
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _block_hash(block):
    data = {
        "id": block["id"],
        "timestamp": block["timestamp"],
        "evento": block["evento"],
        "hash_anterior": block["hash_anterior"],
    }
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def carregar_cadeia(strict=True):
    if not CHAIN_FILE.exists():
        return []

    try:
        with CHAIN_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        if strict:
            raise BlockchainError(f"Nao foi possivel ler a blockchain: {error}") from error
        return []

    if not isinstance(data, list):
        if strict:
            raise BlockchainError("O arquivo da blockchain deve conter uma lista de blocos.")
        return []
    return data


def salvar_cadeia(chain):
    CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".chain-",
        suffix=".json",
        dir=CHAIN_FILE.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(chain, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, CHAIN_FILE)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def registrar_evento(evento):
    evento = str(evento).strip()
    if not evento:
        raise ValueError("O evento nao pode ser vazio.")

    with _chain_lock():
        chain = carregar_cadeia()
        problems = _validate(chain)
        if problems:
            raise BlockchainError(
                "Evento nao registrado porque a blockchain esta inconsistente: "
                + "; ".join(problems)
            )

        previous_hash = chain[-1]["hash_atual"] if chain else "0" * 64
        block = {
            "id": len(chain) + 1,
            "timestamp": _now_iso(),
            "evento": evento,
            "hash_anterior": previous_hash,
        }
        block["hash_atual"] = _block_hash(block)
        chain.append(block)
        salvar_cadeia(chain)
    return block


def _validate(chain):
    problems = []

    for index, block in enumerate(chain):
        position = index + 1
        if not isinstance(block, dict):
            problems.append(f"Posicao {position} nao contem um bloco valido.")
            continue

        missing = REQUIRED_FIELDS - block.keys()
        if missing:
            problems.append(
                f"Bloco na posicao {position} sem campos obrigatorios: "
                + ", ".join(sorted(missing))
                + "."
            )
            continue

        if block["id"] != position:
            problems.append(
                f"Bloco na posicao {position} possui id invalido: {block['id']}."
            )

        if not isinstance(block["evento"], str) or not block["evento"].strip():
            problems.append(f"Bloco {block['id']} possui evento invalido.")

        try:
            datetime.fromisoformat(block["timestamp"].replace("Z", "+00:00"))
        except (AttributeError, TypeError, ValueError):
            problems.append(f"Bloco {block['id']} possui timestamp invalido.")

        try:
            expected_hash = _block_hash(block)
        except (KeyError, TypeError):
            problems.append(f"Bloco {block.get('id', position)} nao pode ser recalculado.")
            continue

        if block.get("hash_atual") != expected_hash:
            problems.append(f"Bloco {block.get('id')} possui hash_atual invalido.")

        if index == 0:
            expected_previous = "0" * 64
        else:
            previous_block = chain[index - 1]
            expected_previous = (
                previous_block.get("hash_atual")
                if isinstance(previous_block, dict)
                else None
            )

        if block.get("hash_anterior") != expected_previous:
            problems.append(f"Bloco {block.get('id')} possui hash_anterior invalido.")

    return problems


def validar_cadeia():
    try:
        chain = carregar_cadeia()
    except BlockchainError as error:
        return [str(error)]
    return _validate(chain)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Blockchain de auditoria SecureChain")
    parser.add_argument("--event", help="Evento a registrar na blockchain")
    parser.add_argument("--validate", action="store_true", help="Valida a integridade da cadeia")
    args = parser.parse_args()

    try:
        if args.event:
            block = registrar_evento(args.event)
            print(f"Evento registrado no bloco {block['id']}")

        if args.validate:
            problems = validar_cadeia()
            if problems:
                print("ALERTA: blockchain inconsistente")
                for problem in problems:
                    print(f"- {problem}")
                raise SystemExit(1)
            print("Blockchain integra.")
    except (BlockchainError, ValueError) as error:
        raise SystemExit(f"Erro: {error}") from error


if __name__ == "__main__":
    main()
