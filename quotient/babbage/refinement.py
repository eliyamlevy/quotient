from typing import List, Dict

class RefinementPipeline:
    """
    Multi-layer LLM-powered refinement pipeline for inventory extraction.
    Each layer incrementally refines the input for the next.
    """
    def __init__(self, llm_prompt_func):
        """
        Args:
            llm_prompt_func: function that takes a prompt string and returns LLM output string
        """
        self.llm_prompt_func = llm_prompt_func

    def layer1_lowercase(self, text: str) -> str:
        """
        First refinement: Convert all letters in the text to lowercase.
        """
        return ''.join([c.lower() if c.isalpha() else c for c in text])

    def layer2_label_clarification(self, text: str) -> str:
        """
        Second refinement: Word replacements and label clarification.
        Uses the LLM to replace all words/phrases related to quantity and item ID with canonical labels.
        
        LLM Prompt Example (exhaustive):
        """
        prompt = (
            """
            You are a data normalization assistant. In the following text, replace all words or phrases that mean quantity with the label 'quantity'.
            These include: amount, number of items, quantity, units, count, requested amount, qty, total units, total quantity, pieces, pcs, no. of items, item count, total count, total pcs, total pieces.
            
            Also, replace all words or phrases that mean item id with the label 'item_id'.
            These include: SKU, item code, product number, stock number, product code, part number, item id, id, item number, product id, code, catalog number, ref, reference number, ref no., item ref, item #, product #, part #.
            
            Return the modified text, preserving all other information.
            
            Text:
            {text}
            """
        )
        return self.llm_prompt_func(prompt.format(text=text))

    def layer3_item_recognition(self, text: str) -> str:
        """
        Third refinement: Item recognition and separation.
        Uses the LLM to split the text into distinct items, preserving all relevant info per item.
        
        LLM Prompt Example (exhaustive):
        """
        prompt = (
            """
            Split the following text into separate items, keeping all info for each item together.
            Text:
            {text}
            Result:
            """
        )
        return self.llm_prompt_func(prompt.format(text=text))

    def run_pipeline(self, text: str) -> Dict[str, str]:
        """
        Runs all refinement layers in sequence, returning intermediate outputs for debugging.
        Returns a dict with keys: 'layer1', 'layer2', 'layer3'.
        """
        out1 = self.layer1_lowercase(text)
        out2 = self.layer2_label_clarification(out1)
        out3 = self.layer3_item_recognition(out2)
        return {'layer1': out1, 'layer2': out2, 'layer3': out3} 