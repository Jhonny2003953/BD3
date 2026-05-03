import redis
import boto3
from botocore.exceptions import ClientError

# 1. CONFIGURACIÓN DE MEMURAI (CACHÉ Y CONCURRENCIA)
# Se utiliza el puerto 6379 por defecto para la gestión de votos en tiempo real.
try:
    cache_keydb = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True,
        socket_timeout=5
    )
    # Prueba de conexión rápida
    cache_keydb.ping()
    print("✅ Memurai (KeyDB) conectado exitosamente en el puerto 6379.")
except redis.ConnectionError:
    print("❌ Error: No se pudo conectar a Memurai. Asegúrate de que el servicio esté activo.")

# 2. CONFIGURACIÓN DE DYNAMODB LOCAL (PERSISTENCIA Y AUDITORÍA)
# Configurado para apuntar al puerto 8000 donde corre tu base de datos de misión crítica.
dynamodb_resource = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='bolt',     # Credenciales para entorno local
    aws_secret_access_key='bolt'
)

def get_db_table(table_name):
    """Retorna el objeto de la tabla de DynamoDB."""
    return dynamodb_resource.Table(table_name)

# 3. UTILIDAD DE INICIALIZACIÓN (OPCIONAL)
# Puedes usar esto para verificar que las tablas existan al arrancar.
def verificar_tablas():
    tablas_necesarias = ['Votacion_Escrutinio', 'Votacion_Identidad']
    client = boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='bolt',
        aws_secret_access_key='bolt'
    )
    try:
        existentes = client.list_tables()['TableNames']
        for tabla in tablas_necesarias:
            if tabla not in existentes:
                print(f"⚠️ Advertencia: La tabla {tabla} no existe. Créala desde el PartiQL Editor.")
            else:
                print(f"✅ Tabla {tabla} detectada correctamente.")
    except Exception as e:
        print(f"❌ Error al conectar con DynamoDB Local: {e}")

if __name__ == "__main__":
    verificar_tablas()