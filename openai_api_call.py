from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI()

val_system_content = """Every prompt will begin with the text \"Question:\" followed by the question \
enclosed in triple backticks. The text \"Output Format:\" explains how the Question \
must be answered. You are an AI that reads the Question enclosed in triple backticks \
and provides the answer in the mentioned Output Format."""

ann_system_content = """Every prompt will begin with the text \"Question:\" followed by the question \
enclosed in triple backticks. The \"Annotator Steps:\" mentions the steps that you should take \
for answering the question. The text \"Output Format:\" explains how the Question \
output must be formatted. You are an AI that reads the Question enclosed in triple backticks \
and follows the Annotator Steps and provides the answer in the mentioned Output Format."""

model = "gpt-4o"

def format_content(is_annotated: int, question: str, annotator_steps: str = None, 
    output_format: str = "Provide only the answer to the question.") -> str:
        
        """
        Formats the content based on whether it is annotated or not, and returns the formatted output.

        Args:
            is_annotated (int): Indicates whether the content is annotated (1 for yes, 0 for no).
            question (str): The question that requires an answer.
            annotator_steps (str, optional): The steps taken by the annotator. Default is an empty string.
            output_format (str, optional): The desired format of the output. Default is "Provide only the answer to the question.".

        Returns:
            str: The formatted content based on the input parameters.
        """
        if not is_annotated:
            return f"""Question: ```{question}```
            Output Format: {output_format}
            """
        else:
            return f"""Question: ```{question}```
            Annotator Steps: {annotator_steps}
            Output Format: {output_format}
            """

def validation_prompt(system_content: str, user_content: str, model: str = "gpt-4o") -> str:
    """
    Sends a validation prompt to the specified language model and returns the model's response.

    Args:
        system_content (str): The system message that sets the context or behavior for the model.
        validation_content (str): The user message that you want the model to validate or respond to.
        model (str): The model ID to be used for generating the completion (e.g. 'gpt-4o').

    Returns:
        str: The content of the model's response.
    """
    MODEL = model
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        max_tokens=75,
    )
    
    return response.choices[0].message.content

def image_validation_prompt(system_content: str, validation_content: str, imageurl: str, model: str = "gpt-4o") -> str:
    """
    Sends a validation prompt with an image to the specified language model and returns the model's response.

    Args:
        system_content (str): The system message that sets the context or behavior for the model.
        validation_content (str): The user message that you want the model to validate or respond to.
        imageurl (str): The url of the image that you want the model to validate or respond to.
        model (str): The model ID to be used for generating the completion (e.g. 'gpt-4o').

    Returns:
        str: The content of the model's response.
    """
    MODEL = model
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": validation_content},
                    {
                        "type": "image_url",
                        "image_url": imageurl,
                    },
                ],
            }
        ],
        max_tokens=75,
    )
    
    return response.choices[0].message.content