[简体中文](../../README.md) | [English](../EN/README_EN.md) | [pt-BR](../pt-BR/README_pt-BR.md) | [Italian](../IT/README_IT.md) | Spanish

---

[Enlace de invitación a Discord](https://discord.gg/mTh5Cu5Bqm) | Cuenta de WeChat: Buscar "pyvideotrans"

---

# Herramienta de Traducción y Doblaje de Vídeos

>
> Esta es una herramienta de traducción y doblaje de vídeos, que puede traducir vídeos de un idioma a otro idioma específico, generando automáticamente y añadiendo subtítulos y doblaje en ese idioma.
>
> El reconocimiento de voz soporta los modelos `faster-whisper`, `openai-whisper` y `GoogleSpeech`, `zh_recogn modelo de reconocimiento de voz en chino de Alibaba`.
>
> La traducción de texto soporta `Traducción de Microsoft|Traducción de Google|Traducción de Baidu|Traducción de Tencent|ChatGPT|AzureAI|Gemini|DeepL|DeepLX|Traducción offline OTT`
>
> La síntesis de texto a voz soporta `Microsoft Edge tts`, `Google tts`, `Azure AI TTS`, `Openai TTS`, `Elevenlabs TTS`, `API de servidor TTS personalizado`, `GPT-SoVITS`, [clone-voice](https://github.com/jianchang512/clone-voice), `[ChatTTS-ui](https://github.com/jianchang512/ChatTTS-ui)` [CosyVoice](https://github.com/FunAudioLLM/CosyVoice)
>
> Permite mantener la música de fondo (basado en uvr5)
> 
> Idiomas soportados: Chino simplificado y tradicional, inglés, coreano, japonés, ruso, francés, alemán, italiano, español, portugués, vietnamita, tailandés, árabe, turco, húngaro, hindi, ucraniano, kazajo, indonesio, malayo, checo,Polish,nl,sw

# Principales Usos y Métodos de Uso

【Traducción de vídeos y doblaje】Traducir el audio de los vídeos a otro idioma y añadir subtítulos en ese idioma.

【Convertir audio o vídeo a subtítulos】Identificar el habla humana en archivos de audio o vídeo y exportarla como archivos de subtítulos srt.

【Creación de doblaje a partir de subtítulos en lote】Crear doblajes a partir de archivos de subtítulos srt existentes localmente, soporta subtítulos individuales o en lote.

【Traducción de subtítulos en lote】Traducir uno o más archivos de subtítulos srt a subtítulos en otro idioma.

【Combinar audio, vídeo y subtítulos】Combinar archivos de audio, vídeo y subtítulos en un único archivo de vídeo.

【Extraer audio de vídeos】Separar el vídeo en un archivo de audio y un vídeo sin sonido.

【Descargar vídeos de YouTube】Descargar vídeos desde YouTube.

----

https://github.com/jianchang512/pyvideotrans/assets/3378335/3811217a-26c8-4084-ba24-7a95d2e13d58

# Versión Preempaquetada (solo para Windows 10/Windows 11, uso del código fuente para MacOS/Linux)

> Empaquetado con pyinstaller, sin hacer indetectable o firmar, lo cual podría ser detectado por software antivirus. Por favor, añada a la lista de permitidos o use el código fuente para la implementación.

0. [Haz clic para descargar la versión preempaquetada, descomprime en un directorio en inglés sin espacios y después haz doble clic en sp.exe](https://github.com/jianchang512/pyvideotrans/releases)

1. Descomprime en una ruta en inglés y asegúrate de que la ruta no contenga espacios. Después de descomprimir, haz doble clic en sp.exe (si encuentras problemas de permisos, puedes abrirlo como administrador con clic derecho).

4. Nota: Debe ser usado después de descomprimir, no puede ser utilizado directamente desde el paquete comprimido ni mover el archivo sp.exe a otro lugar después de descomprimir.

# Implementación del Código Fuente en MacOS

0. Abre una ventana de terminal y ejecuta los siguientes comandos uno por uno
	
	> Asegúrate de haber instalado Homebrew antes de ejecutar, si no lo has instalado, debes hacerlo primero.
	>
	> Ejecuta el comando para instalar Homebrew:  `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
	>
	> Después de instalar, ejecuta: `eval $(brew --config)`
	>

    ```
    brew install libsndfile

    brew install ffmpeg

    brew install git

    brew install python@3.10

    ```

    Continúa ejecutando

    ```
    export PATH="/usr/local/opt/python@3.10/bin:$PATH"

    source ~/.bash_profile 
	
	source ~/.zshrc

    ```



1. Crea un directorio sin espacios ni caracteres chinos, y entra en él desde la terminal.
2. En la terminal, ejecuta el comando `git clone https://github.com/jianchang512/pyvideotrans `
3. Ejecuta el comando `cd pyvideotrans`
4. Continúa ejecutando `python -m venv venv`
5. Sigue ejecutando el comando `source ./venv/bin/activate` para activar el entorno virtual. Asegúrate de que el prompt de la terminal ahora comienza con `(venv)`. Todos los comandos subsiguientes deben ser ejecutados asegurándote de que el prompt de la terminal comience con `(venv)`.

6. Ejecuta `pip install -r requirements.txt `

    Luego intenta ejecutar nuevamente. Si todavía tienes problemas después de cambiar al espejo de Alibaba, intenta ejecutar `pip install -r requirements.txt`

7. `python sp.py` para abrir la interfaz del software.

[Esquema Detallado de Implementación en MacOS](https://pyvideotrans.com/mac.html)


# Implementación del Código Fuente en Linux

0. Para sistemas CentOS/RHEL, ejecuta los siguientes comandos en secuencia para instalar python3.10

```

sudo yum update

sudo yum groupinstall "Development Tools"

sudo yum install openssl-devel bzip2-devel libffi-devel

cd /tmp

wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz

tar xzf Python-3.10.4.tgz

cd Python-3.10.4

./configure — enable-optimizations

sudo make && sudo make install

sudo alternatives — install /usr/bin/python3 python3 /usr/local/bin/python3.10 1

sudo yum install -y ffmpeg

```

1. Para sistemas Ubuntu/Debian, ejecuta los siguientes comandos para instalar python3.10

```

apt update && apt upgrade -y

apt install software-properties-common -y

add-apt-repository ppa:deadsnakes/ppa

apt update

sudo apt-get install libxcb-cursor0

apt install python3.10

curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

<<<<<<< HEAD
sudo update-alternatives --install /usr/bin/python python /usr/local/bin/python3.10  1
=======

sudo update-alternatives --install /usr/bin/python python /usr/local/bin/python3.10 
>>>>>>> 9485b1096d6a40a3fb6962a49df128397f10bdd5

sudo update-alternatives --config python

apt-get install ffmpeg

```

**Abre cualquier terminal y ejecuta `python3 -V`. Si muestra “3.10.4”, significa que la instalación fue exitosa. De lo contrario, fracasó.**


1. Crea un directorio sin espacios ni caracteres chinos, y abre esa carpeta desde la terminal.
2. En la terminal, ejecuta el comando `git clone https://github.com/jianchang512/pyvideotrans`
3. Continúa ejecutando el comando `cd pyvideotrans`
4. Sigue con `python -m venv venv`
5. Continúa con el comando `source ./venv/bin/activate` para activar el entorno virtual. Verifica que el prompt de la terminal ahora empiece con `(venv)`. Todos los siguientes comandos deben ser ejecutados asegurándote de que el prompt de la terminal empiece con `(venv)`.
6. Ejecuta `pip install -r requirements.txt`. Si encuentras algún error, ejecuta los siguientes dos comandos para cambiar el espejo de pip al espejo de Alibaba

    ```

    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com

    ```

    Intenta ejecutar nuevamente. Si todavía tienes problemas después de cambiar al espejo de Alibaba, intenta ejecutar `pip install -r requirements.txt`
7. Si deseas usar aceleración CUDA, ejecuta por separado

    `pip uninstall -y torch torchaudio`


    `pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118`

    `pip install nvidia-cublas-cu11 nvidia-cudnn-cu11`

8. Si deseas habilitar la aceleración CUDA en Linux, es necesario tener una tarjeta gráfica Nvidia y haber configurado correctamente el entorno CUDA11.8+. Busca "Instalación de CUDA en Linux" para más información.


9. `python sp.py` para abrir la interfaz del software.

# Implementación del Código Fuente en Windows 10/11

0. Abre https://www.python.org/downloads/ y descarga Windows 3.10. Después de descargarlo, haz doble clic y sigue las instrucciones, asegurándote de marcar "Agregar a PATH" (Add to PATH).

   **Abre un cmd y ejecuta `python -V`. Si la salida no es `3.10.4`, significa que hubo un error en la instalación o no se agregó a "PATH". Por favor, reinstala.**

1. Abre https://github.com/git-for-windows/git/releases/download/v2.45.0.windows.1/Git-2.45.0-64-bit.exe, descarga Git y sigue las instrucciones de instalación.
2. Elige un directorio sin espacios ni caracteres chinos, escribe `cmd` en la barra de direcciones y presiona Enter para abrir la terminal. Todos los comandos siguientes deben ser ejecutados en esta terminal.
3. Ejecuta el comando `git clone https://github.com/jianchang512/pyvideotrans`
4. Continúa con el comando `cd pyvideotrans`
5. Sigue con `python -m venv venv`
6. Continúa con el comando `.\venv\scripts\activate`. Después de ejecutarlo, verifica que el comienzo de la línea de comandos haya cambiado a `(venv)`. De lo contrario, significa que hubo un error.
7. Ejecuta `pip install -r requirements.txt  `. Si encuentras algún error, ejecuta los siguientes dos comandos para cambiar el espejo de pip al espejo de Alibaba

    ```

    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com

    ```

    Prueba ejecutar nuevamente. Si todavía tienes problemas después de cambiar al espejo de Alibaba, intenta ejecutar `pip install -r requirements.txt `
8. Si deseas usar aceleración CUDA, ejecuta por separado

    `pip uninstall -y torch torchaudio`

    `pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118`

9. Si deseas habilitar la aceleración CUDA en Windows, es necesario tener una tarjeta gráfica Nvidia y haber configurado correctamente el entorno CUDA11.8+. Consulta [Soporte de Aceleración CUDA](https://pyvideotrans.com/gpu.html) para obtener detalles sobre la instalación.

10. Descomprime ffmpeg.zip en el directorio actual del código fuente. Si se solicita reemplazar, hazlo. Después de descomprimir, asegúrate de que en el directorio del código fuente puedas ver ffmpeg.exe, ffprobe.exe, ytwin32.exe,

11. `python sp.py` para abrir la interfaz del software.

# Explicación de los Problemas de Implementación del Código Fuente

1. Por defecto, se usa la versión ctranslate2 4.x, que solo soporta la versión CUDA12.x. Si tu versión de CUDA es inferior a 12 y no puedes actualizar a CUDA12.x, ejecuta el siguiente comando para desinstalar ctranslate2 y luego reinstalar

```

pip uninstall -y ctranslate2

pip install ctranslate2==3.24.0

```

2. Si encuentras errores como `xx module not found`, abre requirements.txt, busca el módulo xx y elimina el "==" y el número de versión que le sigue.

# Guía de Uso y Documentación

Consulta https://pyvideotrans.com/guide.html para la guía de uso y documentación.

# Modelos de Reconocimiento de Voz:

   Enlace de descarga: https://pyvideotrans.com/model.html

   Explicación y diferencias entre modelos: https://pyvideotrans.com/02.html

# Tutoriales en Vídeo (Terceros)

[Implementación del código fuente en Mac/Bilibili](https://www.bilibili.com/video/BV1tK421y7rd/)

[Método de configuración de traducción de vídeo con API Gemini/Bilibili](https://b23.tv/fED1dS3)

[Cómo descargar e instalar](https://www.bilibili.com/video/BV1Gr421s7cN/)

# Capturas de Pantalla del Software

![image](https://github.com/jianchang512/pyvideotrans/assets/3378335/c3abb561-1ab5-47f9-bfdc-609245445190)


# Proyectos Relacionados

[OTT: Herramienta de Traducción de Texto Offline Local](https://github.com/jianchang512/ott)

[Herramienta de Clonación de Voz: Sintetización de Voz con Cualquier Tono](https://github.com/jianchang512/clone-voice)

[Herramienta de Reconocimiento de Voz: Herramienta de Transcripción de Voz a Texto Offline Local](https://github.com/jianchang512/stt)

[Herramienta de Separación de Voz y Música de Fondo](https://github.com/jianchang512/vocal-separate)

[Versión mejorada de api.py para GPT-SoVITS](https://github.com/jianchang512/gptsovits-api)

[  CosyVoice   api.py](https://github.com/jianchang512/cosyvoice-api)

# Agradecimientos

> Este programa depende principalmente de varios proyectos de código abierto

1. [ffmpeg](https://github.com/FFmpeg/FFmpeg)
2. [PySide6](https://pypi.org/project/PySide6/)
3. [edge-tts](https://github.com/rany2/edge-tts)
4. [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
5. [openai-whisper](https://github.com/openai/whisper)
6. [pydub](https://github.com/jiaaro/pydub)
