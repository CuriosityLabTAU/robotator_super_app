#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

url = "https://ttsapi.almagu.com/Api/Synth?key=544980f8fe8b48d7ad&sampling=16000&encoding=mp3&rate=0&voice=elik_2100"


def tts_heb(text, filename="example.mp3"):
    data = requests.get(url + '&text=' + text)
    f = open(filename, 'wb')
    f.write(data.content)
    f.close()