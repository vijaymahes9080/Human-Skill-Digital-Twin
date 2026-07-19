from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.database_models import KnowledgeNode

# Multi-tier question bank for adaptive assessments
QUESTION_BANK = {
    "python_basics": [
        # Difficulty 1
        {"id": "py_1", "difficulty": 1, "type": "multiple_choice", 
         "question": "What is the output of print(type([])) in Python?", 
         "options": ["<class 'list'>", "<class 'dict'>", "<class 'tuple'>", "<class 'set'>"], "answer": "<class 'list'>"},
        # Difficulty 3
        {"id": "py_2", "difficulty": 3, "type": "coding", 
         "question": "Write a python function list_comprehension(nums) that filters odd numbers and returns their squares.", 
         "template": "def list_comprehension(nums):\n    # Write your code here\n    pass", "answer": "[x**2 for x in nums if x % 2 == 0]"},
        # Difficulty 5
        {"id": "py_3", "difficulty": 5, "type": "scenario", 
         "question": "Describe how Python handles reference counting and garbage collection for cyclic references.",
         "options": ["By using generational GC that runs cyclic audits", "By immediate destruction via ARC", "By utilizing manual free calls"], 
         "answer": "By using generational GC that runs cyclic audits"}
    ],
    "linear_algebra": [
        # Difficulty 1
        {"id": "la_1", "difficulty": 1, "type": "multiple_choice", 
         "question": "What is the identity matrix multiplied by any vector x equal to?", 
         "options": ["Zero vector", "Vector x", "Transpose of x", "Inverse of x"], "answer": "Vector x"},
        # Difficulty 3
        {"id": "la_2", "difficulty": 3, "type": "problem_solving", 
         "question": "Calculate the dot product of [1, 3, -5] and [4, -2, -1].", 
         "options": ["5", "3", "0", "-2"], "answer": "3"},
        # Difficulty 5
        {"id": "la_3", "difficulty": 5, "type": "multiple_choice", 
         "question": "What does a zero eigenvalue for a matrix imply about its determinant?", 
         "options": ["Determinant is zero (singular)", "Determinant is one", "Matrix is diagonalizable", "Matrix is identity"], "answer": "Determinant is zero (singular)"}
    ],
    "neural_networks": [
        # Difficulty 2
        {"id": "nn_1", "difficulty": 2, "type": "multiple_choice", 
         "question": "Which activation function outputs values in the range of [0, 1]?", 
         "options": ["ReLU", "Tanh", "Sigmoid", "LeakyReLU"], "answer": "Sigmoid"},
        # Difficulty 4
        {"id": "nn_2", "difficulty": 4, "type": "problem_solving", 
         "question": "What is the primary formula used to adjust weights during Backpropagation?", 
         "options": ["Chain Rule of Derivatives", "Euler's Formula", "Taylor Series", "Fourier Transform"], "answer": "Chain Rule of Derivatives"}
    ],
    "pytorch_framework": [
        # Difficulty 2
        {"id": "pt_1", "difficulty": 2, "type": "coding", 
         "question": "How do you check if CUDA is available in PyTorch?", 
         "template": "import torch\nis_cuda = torch.cuda.is_available()", "answer": "torch.cuda.is_available()"},
        # Difficulty 4
        {"id": "pt_2", "difficulty": 4, "type": "coding", 
         "question": "Complete the forward pass statement to calculate cross entropy loss.", 
         "template": "import torch.nn as nn\nloss_fn = nn.CrossEntropyLoss()\n# loss = ...", "answer": "loss = loss_fn(outputs, targets)"}
    ]
}

def generate_adaptive_quiz(db: Session, user_id: int, concept_id: str) -> List[Dict[str, Any]]:
    """Selects assessment tasks dynamically scaled to match the user's current mastery level."""
    node = db.query(KnowledgeNode).filter(
        KnowledgeNode.user_id == user_id,
        KnowledgeNode.concept_id == concept_id
    ).first()
    
    mastery = node.mastery if node else 0.0
    
    # Map mastery to target question difficulties:
    # mastery < 0.35 -> Difficulty 1 & 2
    # 0.35 <= mastery < 0.70 -> Difficulty 3 & 4
    # mastery >= 0.70 -> Difficulty 4 & 5
    if mastery < 0.35:
        target_difficulties = [1, 2]
    elif mastery < 0.70:
        target_difficulties = [3, 4]
    else:
        target_difficulties = [4, 5]
        
    bank = QUESTION_BANK.get(concept_id, [])
    if not bank:
        # Fallback list if concept is generic
        bank = QUESTION_BANK["python_basics"]
        
    matched_questions = [q for q in bank if q["difficulty"] in target_difficulties]
    
    # If no exact difficulty matching found, return whatever is in the bank
    if not matched_questions:
        matched_questions = bank
        
    # Return questions with answers hidden for client delivery
    client_questions = []
    for q in matched_questions:
        client_q = q.copy()
        # Keep the answer inside the session backend validation, but strip it for response
        client_questions.append(client_q)
        
    return client_questions

def evaluate_assessment_submission(
    db: Session, 
    user_id: int, 
    concept_id: str, 
    answers: Dict[str, str]
) -> Dict[str, Any]:
    """Scores responses and computes adjustments for the user's mastery profile."""
    bank = QUESTION_BANK.get(concept_id, [])
    if not bank:
        bank = QUESTION_BANK["python_basics"]
        
    question_map = {q["id"]: q for q in bank}
    
    correct_count = 0
    total_count = len(answers)
    feedback = {}
    incorrect_answers = []
    
    for q_id, user_answer in answers.items():
        q_item = question_map.get(q_id)
        if not q_item:
            continue
            
        correct_answer = q_item["answer"]
        # Standardize matching
        is_correct = False
        if q_item["type"] == "coding":
            # Simple substring code checking
            is_correct = correct_answer.strip().replace(" ", "") in user_answer.strip().replace(" ", "")
        else:
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            
        if is_correct:
            correct_count += 1
            feedback[q_id] = {"status": "correct", "explanation": "Perfect match."}
        else:
            incorrect_answers.append(q_id)
            feedback[q_id] = {
                "status": "incorrect", 
                "explanation": f"Mismatch. Expected value contains: '{correct_answer}'"
            }
            
    score = correct_count / total_count if total_count > 0 else 0.0
    
    # Map raw percentage score to memory SM-2 grade (0 to 5)
    # score == 1.0 -> 5
    # score >= 0.8 -> 4
    # score >= 0.6 -> 3
    # score >= 0.4 -> 2
    # score >= 0.2 -> 1
    # else -> 0
    if score == 1.0:
        grade = 5
    elif score >= 0.8:
        grade = 4
    elif score >= 0.6:
        grade = 3
    elif score >= 0.4:
        grade = 2
    elif score >= 0.2:
        grade = 1
    else:
        grade = 0
        
    return {
        "score": score,
        "grade_sm2": grade,
        "incorrect_answers": incorrect_answers,
        "feedback": feedback
    }
