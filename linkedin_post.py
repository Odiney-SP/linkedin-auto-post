import http.server
import webbrowser
import urllib.parse
import urllib.request
import json
import threading
import sys
import base64

CLIENT_ID = "SEU_CLIENT_ID"
CLIENT_SECRET = "SEU_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8080/callback"
SCOPE = "openid profile w_member_social"

IMAGE_PATH = None  # Ex: r"C:\Users\seu_usuario\Pictures\foto.jpg" -- deixe None para post sem imagem

POST_TEXT = """Coloque aqui o texto do seu post"""

auth_code = None

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Autorizado! Pode fechar esta aba e voltar ao terminal.</h2>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Erro na autorizacao.")

    def log_message(self, format, *args):
        pass


def get_token_data(code):
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def decode_jwt_sub(jwt):
    try:
        parts = jwt.split(".")
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        return decoded.get("sub")
    except Exception:
        return None


def get_person_urn(token_data):
    id_token = token_data.get("id_token")
    if id_token:
        sub = decode_jwt_sub(id_token)
        if sub:
            return f"urn:li:person:{sub}"

    access_token = token_data.get("access_token", "")
    if access_token.count(".") == 2:
        sub = decode_jwt_sub(access_token)
        if sub:
            return f"urn:li:person:{sub}"

    return None


def upload_image(token, person_urn, image_path):
    init_payload = json.dumps({
        "initializeUploadRequest": {"owner": person_urn}
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.linkedin.com/rest/images?action=initializeUpload",
        data=init_payload,
        method="POST"
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("LinkedIn-Version", "202506")
    req.add_header("X-Restli-Protocol-Version", "2.0.0")

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())
        upload_url = data["value"]["uploadUrl"]
        image_urn = data["value"]["image"]

    with open(image_path, "rb") as f:
        image_data = f.read()

    upload_req = urllib.request.Request(upload_url, data=image_data, method="PUT")
    upload_req.add_header("Content-Type", "application/octet-stream")
    urllib.request.urlopen(upload_req)

    return image_urn


def make_post(token, person_urn, text, image_urn=None):
    url = "https://api.linkedin.com/rest/posts"

    body = {
        "author": person_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    if image_urn:
        body["content"] = {"media": {"id": image_urn}}

    payload = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("LinkedIn-Version", "202506")
    req.add_header("X-Restli-Protocol-Version", "2.0.0")

    with urllib.request.urlopen(req) as response:
        return response.status


def main():
    server = http.server.HTTPServer(("localhost", 8080), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPE)}"
    )

    print("Abrindo navegador para autorizacao...")
    webbrowser.open(auth_url)
    print("Faca login no LinkedIn e autorize o app.")

    thread.join()

    if not auth_code:
        print("Erro: nao foi possivel obter o codigo de autorizacao.")
        sys.exit(1)

    print("Obtendo access token...")
    token_data = get_token_data(auth_code)
    access_token = token_data["access_token"]

    print("Obtendo perfil...")
    person_urn = get_person_urn(token_data)

    if not person_urn:
        print("Erro: nao foi possivel obter o ID do perfil.")
        sys.exit(1)

    print(f"Perfil: {person_urn}")

    image_urn = None
    if IMAGE_PATH:
        print("Fazendo upload da imagem...")
        image_urn = upload_image(access_token, person_urn, IMAGE_PATH)

    print("Publicando post...")
    status = make_post(access_token, person_urn, POST_TEXT, image_urn)

    if status == 201:
        print("\nPost publicado com sucesso!")
    else:
        print(f"\nResposta inesperada: {status}")


if __name__ == "__main__":
    main()
