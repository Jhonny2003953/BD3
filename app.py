from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Proyecto bd3 funcionando"

if __name__ == '__main__':
    app.run(debug=True)