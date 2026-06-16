# linkedin-auto-post

Script Python para publicar posts no LinkedIn de forma automática usando a API oficial. Sem nenhuma biblioteca externa, só Python puro.

## O que precisa

- Python 3.x instalado
- Uma conta no LinkedIn
- Um app criado no LinkedIn Developer Portal

## Configurando o app no LinkedIn

1. Acesse linkedin.com/developers/apps e crie um novo app (vai precisar de uma página de empresa vinculada, pode criar uma fictícia)
2. Na aba **Products**, ative:
   - **Share on LinkedIn**
   - **Sign In with LinkedIn using OpenID Connect**
3. Na aba **Auth**, adicione essa URL em "Authorized redirect URLs":
   ```
   http://localhost:8080/callback
   ```
4. Ainda na aba **Auth**, copie o **Client ID** e o **Client Secret**

## Configurando o script

Abra o arquivo `linkedin_post.py` e preencha as variáveis no topo:

```python
CLIENT_ID = "seu_client_id"
CLIENT_SECRET = "seu_client_secret"
```

Coloque o texto que quer publicar na variável `POST_TEXT`.

Para publicar com imagem, coloque o caminho do arquivo em `IMAGE_PATH`:

```python
IMAGE_PATH = r"C:\Users\seu_usuario\Pictures\foto.jpg"
```

Deixe `None` para postar só texto.

## Rodando

```
python linkedin_post.py
```

O navegador vai abrir automaticamente para você fazer login no LinkedIn e autorizar o app. Depois disso o post é publicado e aparece no terminal a confirmação.

## Como funciona

O script sobe um servidor local na porta 8080, abre o navegador para autenticação OAuth, captura o token que volta, extrai o ID do perfil direto do token sem precisar de chamada extra na API e publica o post. Se tiver imagem configurada, faz o upload antes de criar o post.
