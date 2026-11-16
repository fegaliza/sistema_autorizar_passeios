import getpass
import hashlib
import secrets

senha = getpass.getpass("Digite a senha administrativa: ")
confirmacao = getpass.getpass("Confirme a senha: ")
if not senha or senha != confirmacao:
    raise SystemExit("Senha vazia ou confirmação diferente.")
salt = secrets.token_bytes(16)
iteracoes = 600_000
resultado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, iteracoes)
print("\nConfigure ADMIN_PASSWORD_HASH com o valor abaixo (não publique):\n")
print(f"pbkdf2_sha256${iteracoes}${salt.hex()}${resultado.hex()}")
