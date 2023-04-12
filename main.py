import os
import shutil

from flask import Flask, request, render_template, jsonify, Markup
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

from utils.assistant import run
from utils.arxiv_utils import download_arxiv_source, split_latex
from utils.db_utils import update_txt

app = Flask(__name__, template_folder="static")


@app.route("/")
def index():
    """Render page with existing arXiv IDs in database."""
    arxiv_ids = []
    file_path = "./data/db/arxiv_ids.txt"

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            arxiv_ids = [line.strip() for line in file.readlines()]

    return render_template("index.html", arxiv_ids=arxiv_ids)


@app.route("/ask", methods=["POST"])
def ask():
    """Route to handle queries from the frontend."""
    data = request.get_json()

    query = request.json.get("query", "").strip()
    if not query:
        return jsonify({"result": "Please provide a question."})

    data = request.get_json()
    model = data["modelStr"]
    dont_query_papers = data["queryBool"]
    selected_paper = data["selectedPaperId"]
    openai_api_key = data["openAIKey"]

    # Do error handling here
    result = run(query, model=model, query_papers=not dont_query_papers, api_key=openai_api_key)

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
    """Route to add arXiv IDs to the database."""
    arxiv_ids = request.json["arxiv_ids"]

    pdf_dir = "./data/papers/"
    db_dir = "./data/db/"
    faiss_db_dir = "./data/db/faiss_index"

    try:
        os.makedirs(pdf_dir)
    except FileExistsError:
        pass

    texts = [download_arxiv_source(arxiv_id, output_dir="./data/papers/") for arxiv_id in arxiv_ids]

    window_size = 512
    stride = 384

    texts_metadata = []
    for text, arxiv_id in zip(texts, arxiv_ids):
        text = text.replace("\n", " ").strip()
        texts_metadata_temp = split_latex(text, window_size, stride)
        for i in range(len(texts_metadata_temp)):
            texts_metadata_temp[i]["arxiv_id"] = arxiv_id
        texts_metadata += texts_metadata_temp

    texts = [txt["chunk"] for txt in texts_metadata]
    metadatas = [dict((key, d[key]) for key in ["section", "arxiv_id"]) for d in texts_metadata]
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1")

    # Check if FAISS db folder exists, in which case add to the db. Otherwise, create a new db.
    if os.path.exists(faiss_db_dir):
        db = FAISS.load_local(faiss_db_dir, embeddings)
        db.add_texts(texts, metadatas)

    else:
        db = FAISS.from_texts(texts, embeddings, metadatas)

    # Save the FAISS db
    db.save_local("./data/db/faiss_index")

    # Update list of arXiv IDs in db
    arxiv_ids = update_txt("{}/arxiv_ids.txt".format(db_dir), arxiv_ids)
    with open("{}/arxiv_ids.txt".format(db_dir), "w") as f:
        for line in arxiv_ids:
            f.write(line + "\n")

    return jsonify({"status": "success"})


@app.route("/reset_arxiv_ids", methods=["POST"])
def reset_arxiv_ids():
    """Route to clear entire database."""

    db_dir = "./data/"
    for filename in os.listdir(db_dir):
        file_path = os.path.join(db_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error deleting file: {file_path} - {e}")

    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
