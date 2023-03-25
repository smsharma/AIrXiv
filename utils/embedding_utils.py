import pandas as pd
import numpy as np
from tqdm import tqdm
import os

import openai
from sentence_transformers import SentenceTransformer

# from sentence_transformers import SentenceTransformer


def sliding_window(text, window_size, stride):
    tokens = text.split()
    window_start = 0
    while window_start < len(tokens):
        window_end = min(window_start + window_size, len(tokens))
        yield " ".join(tokens[window_start:window_end])
        window_start += stride


def get_embedding(text, model="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model, device="cpu")
    return model.encode(text)
