import hashlib 

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha_digitada, senha_banco):
    return senha_digitada == senha_banco or \
           hash_senha(senha_digitada) == senha_banco