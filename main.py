from flask import Flask, request, render_template, jsonify, Markup
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from assistant import run
from utils.arxiv_utils import download_arxiv_source
from utils.db_utils import update_dataframe, update_ndarray, update_txt
from utils.embedding_utils import get_embedding, sliding_window
from langchain.document_loaders import PyPDFLoader
import pandas as pd
import os
import numpy as np

app = Flask(__name__)


@app.route("/")
def index():
    arxiv_ids = []
    file_path = "./data/db/arxiv_ids.txt"

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            arxiv_ids = [line.strip() for line in file.readlines()]

    return render_template("index.html", arxiv_ids=arxiv_ids)


@app.route("/ask", methods=["POST"])
def ask():
    query = request.json.get("query", "").strip()
    if not query:
        return jsonify({"result": "Please provide a question."})

    # # Update the context with the current session's arXiv IDs
    # assistant.context = {"arxiv_ids": session.get("arxiv_ids", [])}

    result = run(query)

    sections = result.split("```")
    formatted_result = []
    is_code_block = False
    default_language = "python"
    formatter = HtmlFormatter(style="lovelace")

    for section in sections:
        if is_code_block:
            lines = section.split("\n", 1)
            code_language = lines[0].strip() or default_language
            code = lines[1].strip()
            lexer = get_lexer_by_name(code_language)
            highlighted_code = highlight(code, lexer, formatter)
            formatted_result.append(Markup(highlighted_code))
        else:
            formatted_result.append(Markup.escape(section.strip()))

        is_code_block = not is_code_block

    formatted_result = Markup("\n".join(formatted_result))
    css_classes = Markup(formatter.get_style_defs(".highlight"))

    # Return the formatted result as JSON, including the Pygments CSS classes
    return jsonify({"result": formatted_result, "css_classes": css_classes})


@app.route("/add_arxiv_ids", methods=["POST"])
def add_arxiv_ids():

    arxiv_ids = request.json["arxiv_ids"]

    pdf_dir = "./data/papers/"
    db_dir = "./data/db/"

    try:
        os.makedirs(pdf_dir)
    except FileExistsError:
        pass

    # TODO: Check for success
    texts = [download_arxiv_source(arxiv_id, output_dir="./data/papers/") for arxiv_id in arxiv_ids]

    window_size = 512
    stride = 384

    text_chunks = []
    embeddings = []

    for text in texts:
        text = text.replace("\n", " ").strip()
        text_chunks_i = list(sliding_window(text, window_size, stride))
        embeddings_i = [get_embedding(text) for text in text_chunks_i]

        text_chunks += text_chunks_i
        embeddings += embeddings_i

    embeddings = np.array(embeddings)

    data = [text_chunks]
    transposed_data = list(map(list, zip(*data)))

    columns = ["text"]
    df = pd.DataFrame(transposed_data, columns=columns)

    # Update db (text, embeddings, ids) if already exists; save

    df = update_dataframe("{}/df_text.csv".format(db_dir), df)
    df.to_csv("{}/df_text.csv".format(db_dir), index=False)

    embeddings = update_ndarray("{}/embeddings.npy".format(db_dir), embeddings)
    np.save("{}/embeddings.npy".format(db_dir), embeddings)

    arxiv_ids = update_txt("{}/arxiv_ids.txt".format(db_dir), arxiv_ids)
    with open("{}/arxiv_ids.txt".format(db_dir), "w") as f:
        for line in arxiv_ids:
            f.write(line + "\n")

    return jsonify({"status": "success"})


@app.route("/reset_arxiv_ids", methods=["POST"])
def reset_arxiv_ids():
    # Perform your actions to reset the arXiv IDs here, e.g., clear them from a database or a session variable

    db_dir = "./data/db/"
    for filename in os.listdir(db_dir):
        file_path = os.path.join(db_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {file_path} - {e}")

    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
