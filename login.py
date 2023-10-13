from flask import Flask, request

app = Flask(__name)

# Rota para lidar com a resposta de autenticação do Google
@app.route('/auth/google/callback')
def google_auth_callback():
    # Recupere os parâmetros da resposta de autenticação do Google
    code = request.args.get('code')
    state = request.args.get('state')

    # Faça o processamento necessário com os parâmetros da resposta, como trocar o código por um token de acesso

    # Retorne uma resposta para indicar que a autenticação foi concluída
    return "Autenticação com o Google concluída. Você pode fechar esta página e voltar ao aplicativo."

if __name__ == '__main__':
    app.run()
    