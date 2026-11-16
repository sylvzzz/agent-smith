def add(a, b):
    return a + b


# Função criada por agent-smith: calcula o fatorial de um número inteiro (n!)
def fatorial(n):
    if n < 0:
        raise ValueError("O fatorial não está definido para números negativos.")
    if n == 0 or n == 1:
        return 1
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado


if __name__ == "__main__":
    print(f"2 + 3 = {add(2, 3)}")
    print(f"5!    = {fatorial(5)}")