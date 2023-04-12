import os
import csv

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import openai
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from utils.embedding_utils import get_embedding
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings


def semantic_search(query_embedding, embeddings):
    """Load context prompt."""
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    ranked_indices = np.argsort(-similarities)
    return ranked_indices


def answer_question(context, query, model="gpt-3.5-turbo", max_tokens=None, temperature=0.02):
    system_prompt = "You are a truthful and accurate scientific research assistant. You can write equations in LaTeX. You can fix any unknown LaTeX syntax elements. Do not use the \enumerate. \itemize, \cite, \ref LaTex environments. You are an expert and helpful programmer and write correct code. If parts of the context are not relevant to the question, ignore them. Only answer if you are absolutely confident in the answer. Do not make up any facts. Do not make up what acronyms stand for."

    if context is not None and len(context) > 0:
        prompt = f"Use the following context to answer the question at the end. If parts of the context are not relevant to the question, ignore them. Context: {context}. Question: {query}"
    else:
        prompt = f"Question: {query}"

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            n=1,
            temperature=temperature,
        )
        return response["choices"][0]["message"]["content"]
    except (openai.error.AuthenticationError, openai.error.APIError) as e:
        return "Authentication error."
    except (openai.error.APIError, openai.error.Timeout, openai.error.ServiceUnavailableError) as e:
        return "There was an error with the OpenAI API, or the request timed out."
    except openai.error.APIConnectionError as e:
        return "Issue connecting to the OpenAI API."
    except Exception as e:
        return "An unknown error occurred."


def run(query, model="gpt-3.5-turbo", api_key=None, query_papers=True, k=2, max_len_query=300):
    if api_key is None:
        openai.api_key = os.getenv("OPENAI_API_KEY")
    else:
        openai.api_key = api_key

    db_path = "./data/db/faiss_index"

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1")

    files = [db_path]
    is_missing = False

    for file in files:
        if not os.path.exists(file):
            print(f"{file} does not exist")
            is_missing = True
        else:
            # Load FAISS index
            db = FAISS.load_local(db_path, embeddings)

    # If set, don't query papers; pretend they don't exist
    if not query_papers:
        is_missing = True

    if not query:
        return "Please enter your question above, and I'll do my best to help you."
    if len(query) > max_len_query:
        return "Please ask a shorter question!"
    else:
        # Do a similarity query, combine the most relevant chunks, and answer the question
        if not is_missing:
            similarity_results = db.similarity_search(query, k=k)
            most_relevant_chunk = ". ".join([results.page_content for results in similarity_results])
            answer = answer_question(context=most_relevant_chunk, query=query, model=model)
            answer.strip("\n")
            return answer
        else:
            answer = answer_question(context=None, query=query, model=model)
            answer.strip("\n")
            return answer
