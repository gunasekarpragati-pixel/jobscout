from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()
r = client.responses.create(model="gpt-5.4-mini", input="Say: setup works!")
print(r.output_text)
