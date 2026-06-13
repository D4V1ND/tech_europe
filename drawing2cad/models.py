from dotenv import load_dotenv
from langchain_openai import ChatOpenAI 
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

model_gemini = ChatGoogleGenerativeAI(
                            model="gemini-3.1-pro-preview",
                            temperature=0.0)

model_openai = ChatOpenAI(
                            model="gpt-5.5", 
                            temperature=0.0
                        )