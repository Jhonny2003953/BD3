from flask import Flask, render_template, request, jsonify
import redis
import boto3
from datetime import datetime

app = Flask(__name__)

# --- INFRAESTRUCTURA ---
cache_keydb = redis.Redis(host='localhost', port=6379, decode_responses=True)
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='bolt',
    aws_secret_access_key='bolt'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/votar', methods=['POST'])
def registrar_voto():
    try:
        ci = request.form.get('voter_id')
        candidato = request.form.get('candidate')
        eleccion = request.form.get('eleccion_tipo').lower()

        # 1. VALIDACIÓN DE IDENTIDAD (Redis -> DynamoDB)
        user_data = cache_keydb.hgetall(f"ciudadano:{ci}")
        if not user_data:
            table_id = dynamodb.Table('Votacion_Identidad')
            response = table_id.get_item(Key={'CI': ci})
            if 'Item' in response:
                user_data = response['Item']
                cache_keydb.hset(f"ciudadano:{ci}", mapping=user_data)
            else:
                return jsonify({"status": "error", "message": "CI no habilitado"}), 404

        # 2. SEGURIDAD: Voto Único
        if not cache_keydb.sadd(f"padron:ha_votado:{eleccion}", ci):
            return jsonify({"status": "error", "message": f"Ya votó para {eleccion}"}), 403

        # 3. REDIS: Pipeline de Contadores Geográficos
        prov = user_data.get('provincia', 'desconocida').lower()
        pipe = cache_keydb.pipeline()
        pipe.incr(f"votos:{eleccion}:nac:partido:{candidato}")
        pipe.incr(f"votos:{eleccion}:nac:tipo:valido")
        pipe.incr(f"votos:{eleccion}:prov:{prov}:partido:{candidato}")
        pipe.execute()

        # 4. DYNAMODB: Persistencia en Escrutinio
        table_esc = dynamodb.Table('Votacion_Escrutinio')
        table_esc.put_item(Item={
            'PK': f"ELECCION#{eleccion.upper()}",
            'SK': f"PROV#{prov.upper()}#MESA#{user_data.get('mesa_asignada','0')}",
            'voter_ci': ci,
            'voto': candidato,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({"status": "success", "message": "Voto registrado"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/resultados_completos')
def obtener_resultados():
    provincias = ['murillo', 'ingavi', 'omaysuyos', 'cercado', 'andres_ibanez']
    geo_data = {}
    for p in provincias:
        geo_data[p] = {
            "presi_A": int(cache_keydb.get(f"votos:presidente:prov:{p}:partido:A") or 0),
            "presi_B": int(cache_keydb.get(f"votos:presidente:prov:{p}:partido:B") or 0),
            "gober_X": int(cache_keydb.get(f"votos:gobernador:prov:{p}:partido:X") or 0),
            "gober_Y": int(cache_keydb.get(f"votos:gobernador:prov:{p}:partido:Y") or 0)
        }
    return jsonify({
        "presidente": {
            "A": int(cache_keydb.get("votos:presidente:nac:partido:A") or 0),
            "B": int(cache_keydb.get("votos:presidente:nac:partido:B") or 0),
            "total": int(cache_keydb.get("votos:presidente:nac:tipo:valido") or 0)
        },
        "gobernador": {
            "X": int(cache_keydb.get("votos:gobernador:nac:partido:X") or 0),
            "Y": int(cache_keydb.get("votos:gobernador:nac:partido:Y") or 0),
            "total": int(cache_keydb.get("votos:gobernador:nac:tipo:valido") or 0)
        },
        "provincias": geo_data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)