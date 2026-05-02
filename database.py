import boto3
import redis
from botocore.config import Config

def get_db_connections():
    """
    Inicializa y retorna las conexiones para DynamoDB Local 
    y Memurai/KeyDB (Velocidad).
    """
    
    # 1. Configuración de Memurai / KeyDB (Local)
    try:
        cache_keydb = redis.Redis(
            host='localhost', 
            port=6379, 
            db=0, 
            decode_responses=True
        )
        # Probamos la conexión inmediata
        cache_keydb.ping()
    except Exception as e:
        print(f"Aviso: Memurai no detectado ({e})")
        cache_keydb = None

    # 2. Configuración de Amazon DynamoDB LOCAL
    # Usamos una configuración ligera para evitar problemas con Python 3.13
    try:
        local_config = Config(
            region_name='us-east-1',
            retries={'max_attempts': 1}
        )
        
        db_dynamo = boto3.resource(
            'dynamodb',
            endpoint_url="http://localhost:8000",
            aws_access_key_id='123',
            aws_secret_access_key='123',
            config=local_config
        )
        
        # Validamos la conexión intentando listar tablas (opcional)
        # list(db_dynamo.tables.all())
        
    except Exception as e:
        print(f"Error conectando a DynamoDB Local: {e}")
        db_dynamo = None

    return db_dynamo, cache_keydb

# Script de prueba independiente
if __name__ == "__main__":
    dynamo, keydb = get_db_connections()
    print("\n--- Verificación de Infraestructura ---")
    
    if keydb:
        print("[OK] Memurai (Redis) conectado.")
    else:
        print("[!] Memurai no responde. Verifica que el servicio esté activo.")
        
    if dynamo:
        print("[OK] DynamoDB Local detectado en el puerto 8000.")
    else:
        print("[!] DynamoDB Local no responde. Verifica que el archivo .jar esté corriendo.")