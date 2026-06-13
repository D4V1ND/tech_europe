from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env from the same directory as this file
load_dotenv(Path(__file__).parent / ".env")

model_gemini = ChatGoogleGenerativeAI(
                            model="gemini-3.1-pro-preview",
                            temperature=0.0)

model_openai = ChatOpenAI(
                            model="gpt-5.5", 
                            temperature=0.0
                        )