Overview
MPEdge is an AI-powered search and analysis tool for the Manual of Patent Examining Procedure (MPEP). The application helps patent professionals, attorneys, inventors, and examiners quickly find relevant information within the extensive USPTO documentation.
Features

Semantic Search: Ask questions in natural language and receive relevant answers from the MPEP
Intelligent Chapter Selection: Automatic suggestion of relevant MPEP chapters based on your query
Multiple LLM Support: Choose from various free AI models for generating responses
Source Citations: View the exact MPEP paragraphs that support each answer
User History: Keep track of your previous questions and answers
Export Options: Download responses in markdown or text format
Customizable Themes: Choose between Light, Dark, and Fun visual themes

How It Works

Ask a patent law question in natural language
MPEdge automatically suggests relevant MPEP chapters to search
The application retrieves and analyzes text from selected chapters
The AI model generates a concise answer based on the MPEP content
All source paragraphs are available for review with their match scores

Getting Started
Prerequisites
streamlit
requests
PyMuPDF==1.23.9
thefuzz
python-Levenshtein
sentence-transformers
torch
huggingface_hub
streamlit-lottie
Installation

Clone the repository:

bashgit clone https://github.com/Alonso-droid/mpedge-app
cd mpedge-app

Install the required packages:

bashpip install -r requirements.txt

Set up your API keys:
Create a .streamlit/secrets.toml file with your API keys:

tomlOPENROUTER_API_KEY = "your_openrouter_api_key"
HUGGINGFACE_API_KEY = "your_huggingface_api_key"

Run the application:

bashstreamlit run streamlit_app.py
Usage Examples

"What is a restriction requirement?"
"How do I respond to a final office action?"
"Explain the difference between a continuation and a CIP"
"What are the requirements for obviousness under 35 USC 103?"
"How does the duty of disclosure work?"

Supported Models
MPEdge uses free tier AI models from OpenRouter and Hugging Face, including:

LLaMA 4 Maverick/Scout
Gemini 2.5 Pro
DeepSeek models (R1, Chat V3, R1 Zero)
Mistral Small 3.1
NVIDIA Nemotron Nano
Qwen2.5 VL
DeepHermes 3
Various Hugging Face hosted models

Technical Implementation

Frontend: Built with Streamlit for a responsive and interactive user interface
PDF Processing: Uses PyMuPDF for extracting text from MPEP PDF documents
Semantic Search: Utilizes Sentence Transformers for embedding-based similarity matching
AI Integration: Connects to multiple LLM providers through their APIs
Hugging Face Integration:

Uses Hugging Face's inference API for model access
Leverages the Hugging Face Hub for model selection
Utilizes sentence-transformers from Hugging Face for embeddings
Implements fallback mechanisms between OpenRouter and Hugging Face models



Acknowledgements
This application was created with assistance from ChatGPT and utilizes the following resources:

USPTO's MPEP Documentation
Sentence Transformers
OpenRouter
Streamlit
Hugging Face - For model hosting, inference API, and pre-trained models
