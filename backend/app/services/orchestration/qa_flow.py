from app.pipeline.rag_qa_ver2 import ask_policy_question


def run_policy_qa(question: str):
    answer = ask_policy_question(question)
    return {
        "answer": answer
<<<<<<< HEAD
    }
=======
    }
>>>>>>> e31dd98 (edit)
