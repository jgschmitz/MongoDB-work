import boto3
import json
import os

# Load the transcript
with open("transcript.txt", "r") as f:
    transcript = f.read()

# Load reference documents
reference_texts = []
for fname in os.listdir("references"):
    if fname.endswith(".txt"):
        with open(os.path.join("references", fname), "r") as f:
            reference_texts.append(f.read())

# Create the Claude prompt
prompt = f"""
You are a coaching assistant for Solutions Architects.

Use the following reference documents:
{''.join(reference_texts)}

Here is the transcript of a sales call:

{transcript}

Please provide coaching feedback that includes:
1. A brief summary of the call.
2. Strengths demonstrated by the SA.
3. Areas for improvement.
4. Actionable coaching suggestions.
"""

# Call Claude via Bedrock
client = boto3.client("bedrock-runtime")

response = client.invoke_model(
    modelId="anthropic.claude-v2:1",
    body=json.dumps({
        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
        "max_tokens_to_sample": 2048,
        "temperature": 0.5
    }),
    contentType="application/json",
    accept="application/json"
)

# Decode and print output
output = response['body'].read().decode()
print("\n🧠 Coaching Feedback:\n")
print(output)
