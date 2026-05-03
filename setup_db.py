import boto3

# Configuración de conexión local
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='123',
    aws_secret_access_key='123'
)

def create_tables():
    # 1. Tabla Votacion_Escrutinio (Jerarquía Geográfica)
    try:
        print("Creando tabla Votacion_Escrutinio...")
        table_escrutinio = dynamodb.create_table(
            TableName='Votacion_Escrutinio',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},  # ELECCION#{Tipo}
                {'AttributeName': 'SK', 'KeyType': 'RANGE'} # PROV#...#MUN#...#MESA#...
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        table_escrutinio.wait_until_exists()
        print("Votacion_Escrutinio creada con éxito.")
    except Exception as e:
        print(f"Error o tabla ya existente: {e}")

    # 2. Tabla Votacion_Identidad (Gestión de Ciudadanos)
    try:
        print("\nCreando tabla Votacion_Identidad...")
        table_identidad = dynamodb.create_table(
            TableName='Votacion_Identidad',
            KeySchema=[
                {'AttributeName': 'CI', 'KeyType': 'HASH'} # Partition Key simple
            ],
            AttributeDefinitions=[
                {'AttributeName': 'CI', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        table_identidad.wait_until_exists()
        print("Votacion_Identidad creada con éxito.")
    except Exception as e:
        print(f"Error o tabla ya existente: {e}")

if __name__ == "__main__":
    # Opcional: Función para borrar antes de crear si quieres reiniciar todo
    # delete_existing_tables() 
    create_tables()