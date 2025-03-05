from openai import OpenAI

client_1 = OpenAI(
    api_key = "api_key",
    base_url = "url"
)

def call_model(Prompt, the_model = "the_model", the_temperature = 0.2, the_max_tokens = 1024):
  response = client_1.chat.completions.create(
    model=the_model,
    messages=Prompt,
    temperature=the_temperature,
    max_tokens=the_max_tokens,
    top_p = 0.95,
  )

  content = response.choices[0].message.content
  input_tokens = response.usage.prompt_tokens
  output_tokens = response.usage.completion_tokens
  total_tokens = response.usage.total_tokens

  return [content,input_tokens,output_tokens,total_tokens]

