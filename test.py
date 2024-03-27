import pandas as pd
import openai
import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def separate_action_and_arguments(input_string):
    # function separates input string into Intent and Entities
    # Split the input string by the first "(" occurrence
    parts = input_string.split('(', 1)
    
    # Extract the action and arguments
    intent = parts[0].strip()
    entities = '(' + parts[1] if len(parts) > 1 else ''
    
    return intent, entities

def evaluate_model(model_function):
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
        intent, entities = model_function(query)
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


