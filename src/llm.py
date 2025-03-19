from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_groq import ChatGroq

# Configuration du rate limiter (6000 tokens / bucket pour GROQ)
rate_limiter = InMemoryRateLimiter(
    max_bucket_size=6000,
)

# Setup LLM
llm = ChatGroq(
    # groq_api_key=groq_api_key,
    model="qwen-2.5-coder-32b",
    streaming=True,
    temperature=0,
    rate_limiter=rate_limiter,
    max_tokens=6000
)

