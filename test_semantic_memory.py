# test_semantic_memory.py
# Script de prueba para normalización + memoria semántica

from actions.acciones_llm import normalize_chat_text
from actions.actions_semantic_memory import store_message, retrieve_similar


def main():
    print("=== Test de normalización + memoria semántica ===")

    # 1) Texto original "sucio"
    original = "kiero aprnder contabilidad basica"
    normalizado = normalize_chat_text(original)

    print("\n[1] Normalización")
    print("  Original   :", original)
    print("  Normalizado:", normalizado)

    # 2) Guardar en memoria
    print("\n[2] Guardando en memoria...")
    store_message(original)
    print("  ✅ Mensaje guardado.")

    # 3) Consultar algo parecido
    consulta = "quiero aprender contabilidad básica"
    print("\n[3] Recuperando similar")
    print("  Consulta  :", consulta)
    similar = retrieve_similar(consulta)
    print("  Resultado :", similar)

    print("\n=== Fin del test ===")


if __name__ == "__main__":
    main()
