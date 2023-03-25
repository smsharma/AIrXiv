import os
import csv

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import openai
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from utils.embedding_utils import get_embedding

n_relevant_chunks = 4

openai.api_key = os.environ.get("OPENAI_API_KEY")


def semantic_search(query_embedding, embeddings):
    """Load context prompt."""
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    ranked_indices = np.argsort(-similarities)
    return ranked_indices


def answer_question(context, query, model="gpt-4", max_tokens=None, temperature=0.3):
    system_prompt = "You are a helpful scientific research assistant. You can write equations in LaTeX. You are an expert and helpful programmer and write correct code."
    prompt = f"Use this context to answer the question at the end. {context}. Fix any unknown LaTeX syntax elements. Do not use the \enumerate or \itemize LaTex environments -- write text bullet points. Question: {query}"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        n=1,
        temperature=temperature,
    )
    return response["choices"][0]["message"]["content"]


def get_embedding(text, model="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model, device="cpu")
    return model.encode(text)


def run(query):

    text_file = "./data/db/df_text.csv"
    embeddings_file = "./data/db/embeddings.npy"

    files = [text_file, embeddings_file]
    is_missing = False

    for file in files:
        if not os.path.exists(file):
            print(f"{file} does not exist")
            is_missing = True

    if not query:
        return "Please enter your question above, and I'll do my best to help you."
    if len(query) > 250:
        return "Please ask a shorter question!"
    else:

        if not is_missing:
            with open("./data/db/df_text.csv") as csv_file:
                csv_reader = csv.reader(csv_file)
                embeddings = np.load("./data/db/embeddings.npy")

                query_embedding = get_embedding(query)
                ranked_indices = semantic_search(np.array(query_embedding), embeddings)
                most_relevant_chunk = ""
                for i, row in enumerate(csv_reader):
                    if i in ranked_indices[:n_relevant_chunks]:
                        most_relevant_chunk += " ".join(row)
                answer = answer_question(most_relevant_chunk, query)
                # print(most_relevant_chunk)
                answer.strip("\n")
                return answer
        else:
            answer = answer_question("", query)
            answer.strip("\n")
            return answer
