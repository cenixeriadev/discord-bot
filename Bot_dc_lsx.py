import discord
import cohere
import re
import requests
import random
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import  threading
from flask import Flask



load_dotenv()

co = cohere.ClientV2(os.getenv('COHERE_TOKEN'))

# Configura el cliente de Discord
intents = discord.Intents.default()
intents.message_content = True  # Necesario para leer el contenido de los mensajes
client = discord.Client(intents=intents)


# Evento de inicio del bot
@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')


# Evento para responder a preguntas
@client.event
async def on_message(message):
    # Evita que el bot responda a sí mismo
    """
    Maneja los eventos de mensaje en el servidor de Discord.

    Revisa cada mensaje que se envía en el servidor y responde a los que comienzan con
    "!lsx". El contenido del mensaje se envía a la API de OpenAI para obtener una respuesta.
    Si se produce un error, se notifica al usuario y se imprime el error en la consola para
    depuración.
    """
    if message.author == client.user:
        return

    # Comprobamos si el mensaje comienza con "!lsx" para filtrar las preguntas
    if message.content.startswith("!lsx"):
        # Extraemos la pregunta quitando el prefijo "!lsx"
        pregunta = message.content[len("!lsx"):].strip()

        # Llama a la API de OpenAI para obtener la respuesta
        try:
            respuesta = co.chat(
                model="command-r-plus",
                messages=[
                    {
                        "role": "user",
                        "content": pregunta,
                    }
                ],
                temperature=0.8,
                max_tokens=4096
            )
            extracted_text = ""

            # Verificar si la respuesta contiene elementos
            if hasattr(respuesta.message, 'content') and isinstance(respuesta.message.content, list):
                for item in respuesta.message.content:
                    if hasattr(item, 'type') and item.type == 'text' and hasattr(item, 'text'):
                        extracted_text += item.text.replace("\\n", "\n")
            else:
                # Fallback: Usar el contenido completo si no se encuentra una coincidencia
                extracted_text = str(respuesta.message.content).replace("\\n", "\n")

            max_length = 2000
            chunks = [extracted_text[i:i + max_length] for i in range(0, len(extracted_text), max_length)]

            # Enviar cada parte como un mensaje separado
            for chunk in chunks:
                await message.channel.send(chunk)

        except Exception as e:
            await message.channel.send("Lo siento, ocurrió un error al obtener la respuesta. Inténtalo de nuevo.")
            print(e)  # Imprimir el error en la consola para depuración
    elif message.content.startswith("!smeme"):

        url = "https://api.memegen.link/templates"

        op = random.randrange(200)
        try:
            # Realizar la solicitud GET y obtener el contenido

            res = requests.get(url)
            res.raise_for_status()
            response = res.json()

            link = response[op]["example"]["url"]
            resp = requests.get(link)
            image = BytesIO(resp.content)
            await message.channel.send(file=discord.File(fp=image, filename="meme.png"))
        except requests.exceptions.RequestException as e:
            print("Error ", e)

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot corriendo"

def run_web():
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)


threading.Thread(target=run_web).start()

# Ejecuta el bot
client.run(os.getenv('DISCORD_TOKEN'))