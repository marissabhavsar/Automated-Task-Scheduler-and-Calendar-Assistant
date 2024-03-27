import pandas as pd
import json
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.meteor_score import meteor_score
from rouge import Rouge
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
    queries = test_data['Query'].tolist()
    ground_truth_intent = test_data['Intent'].tolist()
    ground_truth_entities = test_data['Entities'].tolist()
    
    # Predict intents and entities using the model
    predicted_intents = []
    predicted_entities = []

    for query in queries:
        intent, entities = separate_action_and_arguments(model_function(query))
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


    
    bleu_scores = []
    meteor_scores = []
    rouge_scores = []

    # Initialize a rouge evaluator
    rouge_evaluator = Rouge(metrics=['rouge-n', 'rouge-l'],
                            max_n=2,
                            limit_length=True,
                            length_limit=100,
                            length_limit_type='words',
                            apply_avg=False,
                            apply_best=False,
                            alpha=0.5, # Default F1_score
                            weight_factor=1.2,
                            stemming=True)

    # Loop over the dataset for evaluating BLEU, METEOR, and ROUGE
    for gt, pred in zip(ground_truth_entities, predicted_entities):
        # Tokenizing the strings for the evaluation metrics
        reference = gt.split()  # Assuming the entities are space-separated
        candidate = pred.split()  # Assuming the entities are space-separated

        # Calculating BLEU score
        bleu_scores.append(sentence_bleu([reference], candidate))
        
        # Calculating METEOR score
        meteor_scores.append(meteor_score([' '.join(reference)], ' '.join(candidate)))
        
        # Calculating ROUGE score
        rouge_result = rouge_evaluator.get_scores(' '.join(candidate), ' '.join(reference))
        rouge_scores.append(rouge_result)

    # Calculate average of the scores
    average_bleu_score = sum(bleu_scores) / len(bleu_scores)
    average_meteor_score = sum(meteor_scores) / len(meteor_scores)
    # Averaging ROUGE scores across all samples
    average_rouge_scores = defaultdict(float)
    for score in rouge_scores:
        for key in score:
            average_rouge_scores[key] += score[key]['f']
    for key in average_rouge_scores:
        average_rouge_scores[key] /= len(rouge_scores)


    # Print evaluation metrics
    print("Intent Accuracy:", intent_accuracy)
    print("Intent Precision:", intent_precision)
    print("Intent Recall:", intent_recall)
    print("Intent F1 Score:", intent_f1)
    
    print("\nEntity Accuracy:", entity_accuracy)
    print("Entity Precision:", entity_precision)
    print("Entity Recall:", entity_recall)
    print("Entity F1 Score:", entity_f1)

    # Print out the text generation quality scores
    print("\nAverage BLEU score:", average_bleu_score)
    print("Average METEOR score:", average_meteor_score)
    print("Average ROUGE scores:", dict(average_rouge_scores))
