import os
import shutil
import tarfile
import zipfile
import requests
import fnmatch
import subprocess
import re

import pandas as pd
from tqdm import tqdm
from langchain.document_loaders import PyPDFLoader


def split_latex(latex_source, chunk_size, stride):
    # Extract the content between \begin{document} and \end{document}
    document_pattern = re.compile(r"\\begin\{document\}(.*?)\\end\{document\}", re.DOTALL)
    match = document_pattern.search(latex_source)
    if not match:
        return []
    document_content = match.group(1)

    # Extract sections
    section_pattern = re.compile(r"\\section\{.*?\}", re.DOTALL)
    figure_caption_pattern = re.compile(r"\\begin\{figure\}.*?\\caption\{.*?\}.*?\\end\{figure\}", re.DOTALL)
    table_caption_pattern = re.compile(r"\\begin\{table\}.*?\\caption\{.*?\}.*?\\end\{table\}", re.DOTALL)

    sections = list(section_pattern.finditer(document_content))
    figure_captions = list(figure_caption_pattern.finditer(document_content))
    table_captions = list(table_caption_pattern.finditer(document_content))

    def is_inside_caption(pos):
        for fig_caption in figure_captions:
            if fig_caption.start() < pos < fig_caption.end():
                return True

        for table_caption in table_captions:
            if table_caption.start() < pos < table_caption.end():
                return True

        return False

    def get_section(pos):
        if is_inside_caption(pos):
            return None

        current_section = None
        for sec in reversed(sections):
            if sec.start() < pos:
                current_section = sec.group(0)
                break

        return current_section if current_section else None

    # Split the content into chunks
    chunks = []
    pos = 0
    while pos < len(document_content):
        end_pos = min(pos + chunk_size, len(document_content))
        current_section = get_section(pos)

        chunks.append({"chunk": document_content[pos:end_pos], "section": current_section})

        pos += stride

    return chunks


def remove_latex_preamble(latex_source):
    """Remove the LaTeX preamble from a string containing LaTeX source."""
    # Regular expression to match the preamble
    preamble_pattern = re.compile(r"\\documentclass.*?(?=\\begin\{document\})", re.DOTALL | re.MULTILINE)

    # Remove the preamble using the re.sub function
    cleaned_latex_source = preamble_pattern.sub("", latex_source)

    return cleaned_latex_source


def extract_arxiv_ids(papers):
    """Extract the arXiv IDs from the Inspire-HEP papers."""
    arxiv_ids = []
    for paper in papers:
        arxiv_eprints = paper["metadata"].get("arxiv_eprints", [])
        if arxiv_eprints:
            arxiv_id = arxiv_eprints[0]["value"]
            arxiv_ids.append(arxiv_id)
    return arxiv_ids


def download_arxiv_pdf(arxiv_id, output_dir="../data/papers"):
    """Download the PDF of a paper from arXiv."""
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    response = requests.get(pdf_url)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{arxiv_id}.pdf".replace("/", "_"))

    with open(output_path, "wb") as f:
        f.write(response.content)


def download_arxiv_source(arxiv_id, output_dir="../data/papers"):
    """Download the source code of a paper from arXiv; if failed, download the PDF instead."""
    # Try to download the source
    try:
        url = f"https://arxiv.org/e-print/{arxiv_id}"
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            content_type = response.headers["content-type"]
            extension = None

            if "application/x-eprint-tar" in content_type:
                extension = ".tar"
            elif "application/x-eprint-pdf" in content_type:
                extension = ".pdf"
            elif "application/x-eprint" in content_type:
                extension = ".gz"
            elif "application/zip" in content_type:
                extension = ".zip"
            else:
                raise ValueError(f"Unknown content type: {content_type}")

            # For papers with the older arXiv ID format, replace the slash with an underscore
            arxiv_id = arxiv_id.replace("/", "_")
            filename = f"{arxiv_id}{extension}"
            file_path = os.path.join(output_dir, filename)

            with open(file_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

            extracted_folder = os.path.join(output_dir, arxiv_id)
            os.makedirs(extracted_folder, exist_ok=True)

            if extension == ".tar":
                with tarfile.open(file_path, "r") as tar:
                    tar.extractall(extracted_folder)
                os.remove(file_path)
            elif extension == ".gz":
                with tarfile.open(file_path, "r:gz") as tar:
                    tar.extractall(extracted_folder)
                os.remove(file_path)
            elif extension == ".zip":
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(extracted_folder)
                os.remove(file_path)
            else:
                raise ValueError(f"Unknown extension: {extension}")

            all_tex_contents = []

            for root, _, filenames in os.walk(extracted_folder):
                for filename in fnmatch.filter(filenames, "*.tex"):
                    file = os.path.join(root, filename)
                    with open(file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        all_tex_contents.append(remove_latex_preamble(content))

            combined_tex_content = "\n".join(all_tex_contents)
            return combined_tex_content
        else:
            print(f"Error {response.status_code} while downloading {arxiv_id}")
    except:
        # If all else fails, download the PDF
        download_arxiv_pdf(arxiv_id, output_dir=output_dir)
        file = f"{arxiv_id}.pdf".replace("/", "_")
        loader = PyPDFLoader("{}/{}".format(output_dir, file))
        pages = loader.load_and_split()
        return "".join([page.page_content for page in pages])
