from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Load a conversational model
model_name = "microsoft/DialoGPT-medium"  # Using DialoGPT for better conversational responses
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Create a conversational pipeline
conversation_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Function to get a response from the model
def get_response(prompt, max_length=100):
    responses = conversation_pipeline(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=tokenizer.eos_token_id, truncation=True)
    return responses[0]['generated_text']

# Interactive loop for asking questions
def interactive_conversation():
    print("Welcome to the interactive chat! Type 'exit' to end the conversation.")
    context = ""

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # Combine context with user input, ensuring clear separation
        prompt = context + f"User: {user_input}\nAI:"

        # Get model response
        response = get_response(prompt)

        # Extract the response part after "AI:"
        response_text = response.split("AI:")[-1].strip()

        # Display the model's response
        print(f"AI: {response_text}")

        # Update context, keeping only relevant part to avoid growing too large
        context += f"User: {user_input}\nAI: {response_text}\n"

# Start the interactive conversation
interactive_conversation()
