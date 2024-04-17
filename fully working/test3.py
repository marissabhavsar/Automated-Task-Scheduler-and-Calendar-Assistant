import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.meteor_score import meteor_score
from rouge import Rouge
from collections import defaultdict

def calculate_bertscore(references, candidates):
    # Compute BERTScore
    P, R, F1 = bert_score_function(candidates, references, lang="en", rescale_with_baseline=True)
    return F1.mean().item()

def separate_action_and_arguments(input_string):
    # function separates input string into Intent and Entities
    parts = input_string.split('(', 1)
    intent = parts[0].strip()
    entities = '(' + parts[1] if len(parts) > 1 else ''
    return intent, entities

def get_description(entity_string):
    # Extract descriptions from the entity string, which is the first substring in between "(" and "," or the end of the string if no comma is present
    start = entity_string.find('(') + 1  # Index after the opening parenthesis
    end = entity_string.find(',', start)  # Index of the first comma after the opening parenthesis
    end = end if end != -1 else entity_string.find(')', start)  # If no comma, find the closing parenthesis
    
    if start != -1 and end != -1 and end > start:
        return entity_string[start:end].strip()
    else:
        # Return the whole string inside the parentheses if no comma is found
        if start != -1 and entity_string.endswith(')'):
            return entity_string[start:-1].strip()
    return ""

# Remove Event ID from entities if necessary

def remove_event_id(entities, intent):
    intents_to_remove_event_id = {'deleteEvent', 'deleteRecurringEvent', 'updateEvent', 'updateRecurringEvent', 'moveEvent'}
    if intent in intents_to_remove_event_id:
        # Assuming the entities are contained inside brackets "()"
        if len(entities) > 0 and entities[0] == "(" and entities[-1] == ")":
            # Remove the parentheses and then split
            entities = entities[1:-1].split(',', 1)
            if len(entities) > 1:
                # Here, we join back the remaining entities after removing the first one
                entities = '(' + entities[1].strip() + ')'
            else:
                # If there's only one entity, we return an empty set of parentheses
                entities = "()"
    return entities

def test_intent(ground_truth_intent, predicted_intents):
    intent_accuracy = accuracy_score(ground_truth_intent, predicted_intents)
    intent_precision = precision_score(ground_truth_intent, predicted_intents, average='weighted')
    intent_recall = recall_score(ground_truth_intent, predicted_intents, average='weighted')
    intent_f1 = f1_score(ground_truth_intent, predicted_intents, average='weighted')
    
    print("\nIntent Metrics:")
    print("Accuracy:", intent_accuracy)
    print("Precision:", intent_precision)
    print("Recall:", intent_recall)
    print("F1 Score:", intent_f1)

def test_entities(ground_truth_entities, predicted_entities):
    # Preprocess entities to remove event_id if present
    processed_ground_truth = [remove_event_id(entity) for entity in ground_truth_entities]
    processed_predicted = [remove_event_id(entity) for entity in predicted_entities]

    entity_accuracy = accuracy_score(processed_ground_truth, processed_predicted)
    entity_precision = precision_score(processed_ground_truth, processed_predicted, average='weighted')
    entity_recall = recall_score(processed_ground_truth, processed_predicted, average='weighted')
    entity_f1 = f1_score(processed_ground_truth, processed_predicted, average='weighted')
    
    print("\nEntity Metrics:")
    print("Accuracy:", entity_accuracy)
    print("Precision:", entity_precision)
    print("Recall:", entity_recall)
    print("F1 Score:", entity_f1)
    
def test_descriptions(ground_truth_descriptions, predicted_descriptions):
    # Initialize scores
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
                            alpha=0.5,  # Default F1_score
                            weight_factor=1.2,
                            stemming=True)

    # Calculate scores
    for gt_desc, pred_desc in zip(ground_truth_descriptions, predicted_descriptions):
        gt_tokens = gt_desc.split()
        pred_tokens = pred_desc.split()
        
        # Calculate BLEU score
        bleu_scores.append(sentence_bleu([gt_tokens], pred_tokens))
        
        # Calculate METEOR score
        meteor_scores.append(meteor_score([" ".join(gt_tokens)], " ".join(pred_tokens)))
        
        # Calculate ROUGE score
        rouge_result = rouge_evaluator.get_scores(' '.join(pred_tokens), ' '.join(gt_tokens))
        rouge_scores.append(rouge_result)
        
    # Print evaluation metrics for descriptions
    bert_score = calculate_bertscore(ground_truth_descriptions, predicted_descriptions)
    print("Average BERTScore F1:", bert_score)
    print("\nDescriptions Metrics:")
    print("Average BLEU score:", sum(bleu_scores) / len(bleu_scores))
    print("Average METEOR score:", sum(meteor_scores) / len(meteor_scores))
    # Average the ROUGE scores
    average_rouge_scores = {key: sum(rouge_dict[key]['f'] for rouge_dict in rouge_scores) / len(rouge_scores)
                            for key in rouge_scores[0]}
    print("Average ROUGE scores:", average_rouge_scores)
    

def test_complete_entities(ground_truth_entities, predicted_entities):
    # Initialize scores
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
                            alpha=0.5,  # Default F1_score
                            weight_factor=1.2,
                            stemming=True)

    # Calculate scores
    for gt_entity, pred_entity in zip(ground_truth_entities, predicted_entities):
        gt_tokens = gt_entity.split()
        pred_tokens = pred_entity.split()
        
        # Calculate BLEU score
        bleu_scores.append(sentence_bleu([gt_tokens], pred_tokens))
        
        # Calculate METEOR score
        meteor_scores.append(meteor_score([" ".join(gt_tokens)], " ".join(pred_tokens)))
        
        # Calculate ROUGE score
        rouge_result = rouge_evaluator.get_scores(' '.join(pred_tokens), ' '.join(gt_tokens))
        rouge_scores.append(rouge_result)
    
    
    bert_score = calculate_bertscore(ground_truth_entities, predicted_entities)
    print("Average BERTScore F1:", bert_score)
    # Print evaluation metrics for complete entities
    print("\nComplete Entities Metrics:")
    print("Average BLEU score:", sum(bleu_scores) / len(bleu_scores))
    print("Average METEOR score:", sum(meteor_scores) / len(meteor_scores))
    # Average the ROUGE scores
    average_rouge_scores = {key: sum(rouge_dict[key]['f'] for rouge_dict in rouge_scores) / len(rouge_scores)
                            for key in rouge_scores[0]}
    print("Average ROUGE scores:", average_rouge_scores)

def evaluate_model():
    # Load test data
    test_data = pd.read_csv('test2.csv')
    queries = test_data['Query'].tolist()
    ground_truth_intents = test_data['Intent'].tolist()
    ground_truth_entities = test_data['Entities'].tolist()
    
    # Load predicted data
    predicted_data = pd.read_csv("predictions.csv")
    predicted_queries = predicted_data['Query'].tolist()
    predicted_output = predicted_data['Output'].tolist()

    # Predicted intents and entities
    predicted_intents = []
    predicted_entities = []
    
    # Predict using the model and separate intents and entities
    for query in queries:
        output = predicted_output
        intent, entities = separate_action_and_arguments(output)
        predicted_intents.append(intent)
        predicted_entities.append(entities)

    # Remove event_id where necessary in ground truth data and predicted data
    ground_truth_descriptions = []
    predicted_descriptions = []
    for i, intent in enumerate(ground_truth_intents):
        if intent in ['deleteEvent', 'deleteRecurringEvent', 'updateEvent', 'updateRecurringEvent', 'moveEvent']:
            ground_truth_entities[i] = remove_event_id(ground_truth_entities[i], intent)
        ground_truth_descriptions.append(get_description(ground_truth_entities[i]))
    
    for i, intent in enumerate(predicted_intents):
        if intent in ['deleteEvent', 'deleteRecurringEvent', 'updateEvent', 'updateRecurringEvent', 'moveEvent']:
            predicted_entities[i] = remove_event_id(predicted_entities[i], intent)
        predicted_descriptions.append(get_description(predicted_entities[i]))
    
    # Assuming `test_intent`, `test_entities`, `test_descriptions`, `test_complete_entities` functions are defined correctly
    
    # Evaluate model
    test_intent(ground_truth_intent, predicted_intents)
    test_entities(ground_truth_entities, predicted_entities)
    test_complete_entities(ground_truth_entities, predicted_entities)
    test_descriptions(ground_truth_descriptions, predicted_descriptions)
    
    
#input_string = 'createEvent("598 Project and Study", "2024-04-18", "15:30", 2)'
#input_string = 'updateEvent("33pmlrcvmobnp4oc9t4d64ib2o_20240415T200000Z", "545 Project Meeting and Study for 598", 2, "")'
#intent, entities = separate_action_and_arguments(input_string)
#print("Intent:", intent)
#print("Entities:", entities)
#result_from_remove_event_id = remove_event_id(entities,intent)
#print(result_from_remove_event_id)
#result_from_get_description = get_description(result_from_remove_event_id)
#print(result_from_get_description)

evaluate_model()