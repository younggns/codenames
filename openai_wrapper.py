import openai
import os

class OpenAIWrapper:
    def __init__(self):
        self.api_key = os.environ['OPENAI_API_KEY']
        self.client = openai.OpenAI()
        openai.api_key = self.api_key

    def infer(self, prompts, engine='gpt-3.5-turbo-instruct', max_tokens=150):
        responses = []
        for prompt in prompts:
            try:
                response = self.client.completions.create(
                    model=engine,
                    prompt=prompt,
                    max_tokens=max_tokens
                )
                responses.append(response.choices[0].text.strip())
            except Exception as e:
                responses.append('Error: ' + str(e))
        return responses


def wrapper_test():
    model = OpenAIWrapper()
    prompts = ["The sky is", "My haircut looks really"]
    return model.infer(prompts)