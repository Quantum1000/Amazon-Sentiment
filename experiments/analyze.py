from _context import former
from former import util

from util import d, here

import torch
from torch import nn
from torch.autograd import Variable
import torch.nn.functional as F

from torchtext import data, datasets, vocab
from torchtext.data import Example

import numpy as np

import pickle

import requests

import time

import spacy
from spacy.lang.en import English
from spacy.lang.de import German
from spacy.lang.tr import Turkish
from spacy.lang.ja import Japanese

from argparse import ArgumentParser
from torch.utils.tensorboard import SummaryWriter

import random, tqdm, sys, math, gzip
from google.cloud import translate
import pickle

def metatokenize(x,  nlp):
    doc = nlp(x)
    out = []
    for t in doc:
        out.append(t.text)
    return out
tokenizer = {'EN':English, 'JA':Japanese, 'DE':German, 'TR':Turkish}
LANGS = ['EN', 'DE', 'JA']#
nlp = English()
def tok(x):
    return metatokenize(x, nlp)


RvPL = 16000

project_id = 'translationtest-1575630305182'
client = translate.TranslationServiceClient()
parent = client.location_path(project_id, "global")
for fromlang in LANGS:
    fp = open("reviews" + fromlang + ".pkl", "rb")
    arr = pickle.load(fp)
    fp.close()
    reviewbyrating = [[],[]]
    ratinghist = [0, 0]
    for content in arr:
        r = content[2] > 3
        ratinghist[r] += 1
        content[2] = int(r)
        reviewbyrating[r].append(content)
    keep = min(ratinghist)
    arr = []
    if keep * 2 >= RvPL:
        for i in range(0, len(ratinghist)):
            arr.extend(random.sample(reviewbyrating[i], int(RvPL / 2)))
    else:
        for i in range(0, len(ratinghist)):
            if ratinghist[i] < RvPL / 2:
                arr.extend(reviewbyrating[i])
            else:
                arr.extend(random.sample(reviewbyrating[i], int(RvPL - keep)))
    transarr = []
    print("Data from lang " + fromlang + " processed, ready to be translated.")
    # Review Content format = [category, name, rating, title, text]
    natarr = arr.copy()
    for content in arr:
        transarr.append(content[3].lower()[:512])
        transarr.append(content[4].lower()[:2048])
    for tolang in LANGS:
        if tolang != fromlang:
            print("Translation commencing.")
            translations = []
            payloadsize = 10000
            processed = 0
            while processed < len(transarr):
                charc = 0
                payload = []
                mask = []
                while processed < len(transarr):
                    newstr = transarr[processed]

                    if(len(newstr) + charc > payloadsize):
                        break
                    elif len(newstr) == 0:
                        mask.append(False)
                        processed += 1
                    else:
                        charc += len(newstr)
                        mask.append(True)
                        payload.append(newstr)
                        processed += 1
                for j in range(0, 2):
                    try:
                        translation = client.translate_text(
                            parent = parent, 
                            contents = payload, 
                            mime_type = 'text/plain', 
                            source_language_code = fromlang, 
                            target_language_code = tolang)
                    except:
                        print("Translate threw error, sleeping and hoping it goes away lol. Managed to get to " + str(len(translations)) + " things translated.")
                        time.sleep(100)
                    else:
                        break
                t = translation.translations
                k = 0
                for j in range(0, len(mask)):
                    if mask[j]:
                        translations.append(t[k].translated_text)
                        k+=1
                    else:
                        translations.append('')
                        
            
            for i in range(0, len(arr)):
                try:
                    arr[i][3] = translations[int(i * 2)]
                    arr[i][4] = translations[int(i * 2) + 1]
                except:
                    print(i)
                    print(len(translations))
                    break
            print("Translations from lang " + fromlang + " to " + tolang + " complete, ready to be analyzed.")
        else:
            arr = natarr.copy()
        fp = open("model" + tolang + ".pkl", "rb")
        modelarr = pickle.load(fp)
        fp.close()
        model = modelarr[0]
        nlp = tokenizer[tolang]()
        TEXT = data.Field(lower=True, include_lengths=True, batch_first=True, tokenize=lambda x: metatokenize(x, nlp))
        TEXT.vocab = modelarr[2]
        LABEL = data.Field(False)
        # Formatting, same as from preprocess.py
        newarr = []
        for content in arr:
            newarr.append(Example.fromdict({"rating": content[2], "review": (content[3] + '<body>\n' + content[4])},{"rating": ("label", LABEL), "review": ("text", TEXT)}))
        analyze = data.Dataset(newarr,{"label": LABEL, "text": TEXT})
        LABEL.build_vocab(analyze)
        batches = data.BucketIterator(analyze, batch_size=8, device=util.d(), sort_key=lambda x: len(x.text), sort_within_batch=False)
        if torch.cuda.is_available():
            model.cuda()
        cor = 0.0
        tot = 0.0
        mx = 512 # Magic number, supposed to be the same as in amazonclassify.py
        print("All data in the correct format, beginning analysis.")
        with torch.no_grad():

            model.train(False)
            tot, cor= 0.0, 0.0

            for batch in batches:

                input = batch.text[0]
                label = batch.label - 1

                if input.size(1) > mx:
                    input = input[:, :mx]
                out = model(input).argmax(dim=1)

                tot += float(input.size(0))
                cor += float((label == out).sum().item())

            acc = cor / tot
            if acc < 0.5:
                acc = 1 - acc # Since the result is binary, this acc can be achieved simply by inverting the output
            if fromlang == tolang:
                print(f'Native accuracy is {acc:.3}')
            else:
                print(f'{fromlang} to {tolang} accuracy is {acc:.3}')  