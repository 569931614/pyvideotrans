[简体中文](../../README.md) | English | [pt-BR](../pt-BR/README_pt-BR.md) | [Italian](../IT/README_IT.md) | [Spanish](../ES/README_ES.md)

---



---

# Video Translation and Voiceover Tool

>
> This is a video translation and voiceover tool that can translate videos from one language into a specified language, automatically generating and adding subtitles and voiceovers in that language.
>
> Voice recognition supports `faster-whisper` model, `openai-whisper` model, and `GoogleSpeech`, `zh_recogn`Ali Chinese speech recognition model.
>
> Text translation supports `Microsoft Translator|Google Translate|Baidu Translate|Tencent Translate|ChatGPT|AzureAI|Gemini|DeepL|DeepLX|Offline Translation OTT`
>
> Text-to-speech synthesis supports `Microsoft Edge tts`, `Google tts`, `Azure AI TTS`, `Openai TTS`, `Elevenlabs TTS`, `Custom TTS server API`, `GPT-SoVITS`, `clone-voice`, `ChatTTS-ui`, `Fish TTS`, `CosyVoice`
>
> Allows for the retention of background accompaniment music, etc. (based on uvr5)
>
> Supported languages: Simplified and Traditional Chinese, English, Korean, Japanese, Russian, French, German, Italian, Spanish, Portuguese, Vietnamese, Thai, Arabic, Turkish, Hungarian, Hindi, Ukrainian, Kazakh, Indonesian, Malay, Czech,Polish,Nl,sw

# Main Uses and Methods of Use

[Translate Video and Dubbing] Translate the audio in a video into another language's dubbing and embed the subtitles in that language.

[Audio or Video to Subtitles] Convert human speech in audio or video files into text and export as srt subtitle files.

[Batch Subtitle Creation and Dubbing] Create dubbing based on existing local srt subtitle files, supporting both single and batch subtitles.

[Batch Subtitle Translation] Translate one or more srt subtitle files into subtitles in other languages.

[Audio, Video, and Subtitles Merge] Merge audio files, video files, and subtitle files into one video file.

[Extracting Audio from Video] Separate a video into audio files and silent video.

[Download YouTube Videos] Download videos from YouTube.

----


# Pre-packaged Version (Only for win10/win11, MacOS/Linux use source code deployment)

> Packaged using pyinstaller, not made undetectable and unsigned, antivirus may alert, please add to the whitelist or deploy using the source code

0. Download the pre-packaged version, unzip to an English directory without spaces, then double-click sp.exe

1. Unzip to an English path and make sure the path does not contain spaces. After unzipping, double-click sp.exe (If encountering permission issues, right-click to open as administrator)

4. Note: Must be used after unzipping, do not directly click inside the compressed package, and do not move the sp.exe file to other locations after unzipping.


# MacOS Source Code Deployment

0. Open a terminal window and execute the following commands one by one

    > Make sure you have installed Homebrew before executing. If you have not installed Homebrew, you need to install it first.
    >
    > After installation, execute: `eval $(brew --config)`
    >

    ```
    brew install libsndfile

    brew install ffmpeg

    brew install git

    brew install python@3.10

    ```

    Continue executing

    ```
    export PATH="/usr/local/opt/python@3.10/bin:$PATH"

    source ~/.bash_profile 
	
	source ~/.zshrc

    ```


1. Create a folder without spaces or Chinese characters, then navigate to that folder in the terminal.
2. Extract or clone the BDvideoTrans source code
3. Execute `cd BDvideoTrans`
4. Continue with `python -m venv venv`
5. Execute `source ./venv/bin/activate` and ensure the terminal prompt begins with `(venv)`, following commands must ensure the terminal prompt starts with `(venv)`
6. Execute `pip install -r requirements.txt`


    Then re-execute. If failure still occurs after switching to the Aliyun source, try executing `pip install -r requirements.txt `

7. `python sp.py` to open the software interface


[Detailed Deployment Scheme for Mac](https://BDvideoTrans.com/mac.html)

# Linux Source Code Deployment

0. For CentOS/RHEL series, execute the following commands in sequence to install python3.10

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

1. For Ubuntu/Debian series, execute the following commands to install python3.10

```

apt update && apt upgrade -y

apt install software-properties-common -y

add-apt-repository ppa:deadsnakes/ppa

apt update

sudo apt-get install libxcb-cursor0

apt install python3.10

curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

sudo update-alternatives --install /usr/bin/python python /usr/local/bin/python3.10  1

sudo update-alternatives --config python

apt-get install ffmpeg

```


**Open any terminal and execute `python3 -V`, if the output is "3.10.4", it means the installation was successful; otherwise, it was not successful.**


1. Create a folder without spaces or Chinese characters, then navigate to that folder from the terminal.
3. Extract or clone the BDvideoTrans source code
4. Continue with `cd BDvideoTrans`
5. Execute `python -m venv venv`
6. Continue with `source ./venv/bin/activate`, ensure the command line prompt has changed to start with `(venv)`, otherwise, it indicates an error.
7. Execute `pip install -r requirements.txt`, if failure occurs, execute the following 2 commands to switch the pip mirror to Alibaba.

    ```

    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com

    ```

    Then re-execute. If failure still occurs after switching to the Aliyun source, try executing `pip install -r requirements.txt `
8. To use CUDA acceleration, execute separately

    `pip uninstall -y torch torchaudio`


    `pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118`

    `pip install nvidia-cublas-cu11 nvidia-cudnn-cu11`

9. To enable CUDA acceleration on Linux, an Nvidia graphics card must be available, and the CUDA11.8+ environment must be properly set up. Please search "Linux CUDA Installation" for more information.


10. `python sp.py` to open the software interface


# Window10/11 Source Code Deployment

0. Open https://www.python.org/downloads/ to download Windows3.10, double-click to proceed with the installation, make sure to select "Add to PATH"

   **Open a cmd, execute `python -V`, if the output is not `3.10.4`, it indicates an installation error or "Add to PATH" was not selected, please reinstall**

1. Find a folder without spaces or Chinese characters, enter `cmd` in the address bar and press enter to open the terminal, all the following commands must be executed in this terminal.
2. Extract or clone the BDvideoTrans source code
3. Continue with `cd BDvideoTrans`
4. Execute `python -m venv venv`
5. Continue with `.\venv\scripts\activate`, after execution check and confirm that the command line has changed to start with `(venv)`, otherwise, it indicates an error.
6. Execute `pip install -r requirements.txt `, if failure occurs, execute the following 2 commands to switch the pip mirror to Alibaba

    ```

    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com

    ```

    Then re-execute. If failure still occurs after switching to the Aliyun source, try executing `pip install -r requirements.txt`
8.  To use CUDA acceleration, execute separately

    `pip uninstall -y torch torchaudio`

    `pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118`


9. For Windows, to enable CUDA acceleration, an Nvidia graphics card is required, and the CUDA11.8+ environment must be properly set up. See [CUDA Acceleration Support](https://BDvideoTrans.com/gpu.html) for installation details.

10. Unzip ffmpeg.zip to the current source code directory, prompt to overwrite if asked, make sure the ffmpeg folder under the source code directory contains ffmpeg.exe ffprobe.exe ytwin32.exe,

11. `python sp.py` to open the software interface



# Source Code Deployment Issue Explanation

1. By default, ctranslate2 version 4.x is used, only supporting CUDA12.x version. If your CUDA version is below 12 and you cannot upgrade to CUDA12.x, please execute the command to uninstall ctranslate2 and then reinstall

```

pip uninstall -y ctranslate2

pip install ctranslate2==3.24.0

```

2. You may encounter errors such as `xx module not found`. Open requirements.txt, search for the xx module, then remove the == and the version number after it.




# User Guide and Documentation

Please visit https://BDvideoTrans.com/guide.html


# Speech Recognition Models:

   Download link: https://BDvideoTrans.com/model.html

   Model descriptions and differences: https://BDvideoTrans.com/02.html



# Video Tutorials (Third-party)

[Mac Source Code Deployment/Bilibili](https://www.bilibili.com/video/BV1tK421y7rd/)

[Method of setting video translation with Gemini Api/Bilibili](https://b23.tv/fED1dS3)

[How to Download and Install](https://www.bilibili.com/video/BV1Gr421s7cN/)


# Software Preview Screenshot

## Acknowledgments

> This program mainly relies on several open-source projects

1. ffmpeg
2. PySide6
3. edge-tts
4. faster-whisper
5. openai-whisper
6. pydub



