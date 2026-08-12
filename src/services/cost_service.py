class CostService:
    """
    Tracks tokens and calculates estimated costs based on provider pricing.
    """
    
    # Example rates per 1k tokens
    PRICING = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    }

    def __init__(self):
        pass

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(model)
        if not pricing:
            return 0.0
            
        input_cost = (input_tokens / 1000.0) * pricing["input"]
        output_cost = (output_tokens / 1000.0) * pricing["output"]
        return input_cost + output_cost\n