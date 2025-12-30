"""
Script de prueba para verificar que el agente consulta datos reales de la BD
"""
import requests
import json

# URL del servidor local
BASE_URL = "http://127.0.0.1:8080"

def test_query(pregunta):
    """Envía una pregunta al agente y muestra la respuesta"""
    print("\n" + "="*80)
    print(f"❓ PREGUNTA: {pregunta}")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": pregunta},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🤖 RESPUESTA DEL AGENTE:")
        print(data['response'])
        print(f"\n📊 ¿Usó contexto de BD? {'✅ SÍ' if data.get('context_used') else '❌ NO'}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def main():
    print("\n" + "="*80)
    print("  PRUEBA DE CONSULTAS REALES A LA BASE DE DATOS")
    print("="*80)
    
    # Verificar que el servidor está corriendo
    try:
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code == 200:
            print("✅ Servidor corriendo correctamente\n")
        else:
            print("⚠️ Servidor respondió con error")
            return
    except Exception as e:
        print(f"❌ No se pudo conectar al servidor: {e}")
        print("   Asegúrate de que el servidor esté corriendo en http://127.0.0.1:8080")
        return
    
    # Prueba 1: Pregunta sobre apósitos (debe traer datos reales de la BD)
    test_query("¿Qué hospitales necesitarán apósitos este mes?")
    
    # Prueba 2: Pregunta sobre guantes
    test_query("¿Cuál es la demanda estimada de guantes médicos?")
    
    # Prueba 3: Pregunta general
    test_query("¿Qué hospitales tienen mayor demanda de insumos?")
    
    print("\n" + "="*80)
    print("✅ PRUEBAS COMPLETADAS")
    print("="*80)
    print("\n💡 VERIFICA que las respuestas incluyan:")
    print("   - Nombres específicos de hospitales")
    print("   - Números exactos de demanda")
    print("   - Fechas o períodos")
    print("   - Niveles de confianza (90.21%)")
    print("\n")

if __name__ == "__main__":
    main()
