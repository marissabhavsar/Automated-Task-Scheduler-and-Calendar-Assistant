import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import openai
import json

def model(query):
    # Define the prompt
    prompt = "Extract intent from the following query meant for a virtual calendar assistant - " + query + ". Your response should be a single word that describes the intent of the query, and should be one of the following: create_event, delete_event, move_event, update_event, add_task, list_events,create_recurring_event, delete_recurring_event, move_recurring_event"
    
    # Initialize OpenAI client
    client = openai.ChatCompletion.create()
    
    # Get intent from GPT-3.5
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    intent = ''
    for chunk in stream:
        intent += chunk.choices[0].delta.content or ""
    
    # Execute action based on intent
    if intent == 'create_event':
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': query}],
            functions=create_event_format,
            function_call='auto',
        )
        json_response = json.loads(response.choices[0].message.function_call.arguments)
        entities = dict(json_response)
        create_event(entities)
    # Add conditions for other intents and corresponding actions here
    else:
        print("Intent not recognized.")

def evaluate_model():
    # Load test data
    test_data = pd.read_csv("test.csv")
    
    # Extract queries and ground truth from test data
    queries = test_data['Query']
    ground_truth_intent = test_data['Intent']
    ground_truth_entities = test_data['Entities']
    
    # Predict intents and entities using the model
    predicted_intents = []
    predicted_entities = []

    for query in queries:
        intent, entities = model(query)  # Assuming model has a predict method
        predicted_intents.append(intent)
        predicted_entities.append(entities)
    
    # Calculate evaluation metrics
    intent_accuracy = accuracy_score(ground_truth_intent, predicted_intents)
    intent_precision = precision_score(ground_truth_intent, predicted_intents, average='weighted')
    intent_recall = recall_score(ground_truth_intent, predicted_intents, average='weighted')
    intent_f1 = f1_score(ground_truth_intent, predicted_intents, average='weighted')
    
    # Assuming entities are evaluated separately
    entity_accuracy = accuracy_score(ground_truth_entities, predicted_entities)
    entity_precision = precision_score(ground_truth_entities, predicted_entities, average='weighted')
    entity_recall = recall_score(ground_truth_entities, predicted_entities, average='weighted')
    entity_f1 = f1_score(ground_truth_entities, predicted_entities, average='weighted')
    
    # Print evaluation metrics
    print("Intent Accuracy:", intent_accuracy)
    print("Intent Precision:", intent_precision)
    print("Intent Recall:", intent_recall)
    print("Intent F1 Score:", intent_f1)
    
    print("\nEntity Accuracy:", entity_accuracy)
    print("Entity Precision:", entity_precision)
    print("Entity Recall:", entity_recall)
    print("Entity F1 Score:", entity_f1)
