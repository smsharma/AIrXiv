<h1 align="center">
AIrXiv<!-- omit from toc -->
</h1>

<h4 align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-red.svg)](https://opensource.org/licenses/MIT)
[![Pull requests welcome](https://img.shields.io/badge/Pull%20Requests-welcome-green.svg?logo=github)](https://github.com/smsharma/AIrXiv/pulls)
</h4>

AIrXiv is a prototype for an LLM-powered ArXiv research assistant. It is an Electron app with a Flask backend powered by the OpenAI API. AIrXiv relies on a user-facing [OpenAI API Key](https://platform.openai.com/account/api-keys).

![Screenshot.](static/screenshot.png)

## Contents<!-- omit from toc -->

- [Implementation Notes](#implementation-notes)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Implementation Notes

- AIrXiv attempts to extract the TeX source of the papers when they are added to the database. This was found to work better when it comes to transcribing equations and algorithms compared to extracting directly from the PDF. If this fails, PDF extraction is used.
- AIrXiv uses a simple top-k similarity search (k = 3 by default) from a FAISS vector store, relying on `langchain`. k can be set in config.yml, along with the chunk size and stride length of chunks (512 and 384 by default).
- Frontend elements are in `static`, and backend elements are in `util` and `main.py`.

## Installation

Please open an [Issue](https://github.com/smsharma/AIrXiv/issues) is you are having problems with installation. 

0. (Prerequisites) Make sure you have [Node.js](https://nodejs.org/en/download) (LTS version recommended) and Python >=3.7.
1. Clone and `cd` into the repo:
```
git clone https://github.com/smsharma/AIrXiv.git
cd AIrXiv
```
2. Install the required Python packages using the provided environment.yml file. You can use Conda or any other environment manager of your choice:
```
conda env create -f environment.yml
conda activate airxiv
```
3. Install the required Node.js packages by running the following command:
```
npm install
```

## Usage

Run the Electron app with 
```
npm run dev
```
which launches the Python/Flask backend (`python main.py` or `npm run start-flask`) as well as the frontend (`npm start`). If this fails, try running the two commands separately. Add an arXiv ID or two, enter your [OpenAI API Key](https://platform.openai.com/account/api-keys) in the text box towards the bottom, and start asking questions!

Usage notes:
- Either `gpt-3.5-turbo` or `gpt-4` can be selected in the app settings. `gpt-4` is significantly better in particular at implementing code, but is about an order of magnitude more expensive (~$0.02/1000 tokens) compared `gpt-3.5-turbo`, and additionally API access is subject to a [waitlist](https://openai.com/waitlist/gpt-4-api).
- Paper querying can be turned off by checking "Don't query papers" in the settings. This then simply relies on the general capabilities of the model.
- **The models can hallucinate, and all output should be verified for integrity.**

## License

AIrXiv is licensed under the [MIT License](LICENSE.md).
