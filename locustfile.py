from locust import HttpUser, task, between
import random

# A fixed list of questions so we can test a WARM cache on the second run
QUESTIONS = [
    "What causes heart disease?",
    "Is there a link between smoking and lung cancer?",
    "What is the effect of statins on cholesterol levels?",
    "Does exercise reduce the risk of cardiovascular disease?",
    "What are the symptoms of COVID-19?",
    "How does insulin regulate blood sugar?",
    "What is the role of the BRCA1 gene?",
    "Can vitamin C cure the common cold?",
    "What is the efficacy of mRNA vaccines?",
    "How does alcohol affect liver function?"
]

class RAGUser(HttpUser):
    # Wait between 0.5 and 1.5 seconds to simulate human typing
    # 30 users roughly translates to ~30 RPS
    wait_time = between(0.5, 1.5)

    @task
    def query_rag(self):
        self.client.post("/query", json={"question": random.choice(QUESTIONS)})