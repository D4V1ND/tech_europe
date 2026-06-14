from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env from the same directory as this file
load_dotenv()

model_gemini = ChatGoogleGenerativeAI(
                            model="gemini-3.1-pro-preview",
                            thinking_level="high",
                            temperature=0.0, 
                            top_p=0.1,
                            media_resolution="MEDIA_RESOLUTION_HIGH")

model_openai = ChatOpenAI(
                            model="gpt-5.5", 
                            temperature=0.0
                        )