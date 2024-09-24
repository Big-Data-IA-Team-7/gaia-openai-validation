import openai
from openai import OpenAI
import time
from project_logging import logging_module

class OpenAIClient:
    def __init__(self):
        """
        Initializes the OpenAIClient with all system prompts.
        """
        self.client = OpenAI()  # Initialize OpenAI client

        # System content strings
        self.val_system_content = """Every prompt will begin with the text \"Question:\" followed by the question \
enclosed in triple backticks. The text \"Output Format:\" explains how the Question \
must be answered. You are an AI that reads the Question enclosed in triple backticks \
and provides the answer in the mentioned Output Format."""

        self.ann_system_content = """Every prompt will begin with the text \"Question:\" followed by the question \
enclosed in triple backticks. The \"Annotator Steps:\" mentions the steps that you should take \
for answering the question. The text \"Output Format:\" explains how the Question \
output must be formatted. You are an AI that reads the Question enclosed in triple backticks \
and follows the Annotator Steps and provides the answer in the mentioned Output Format."""

        self.audio_system_content = """Every prompt will begin with the text \"Question:\" followed by the question \
enclosed in triple backticks. The question will mention that there is an .mp3 file attached however the .mp3 file has \
already been transcribed and the transcribed text is attached after the text: \"Transcription:\". The text \"Output Format:\" \
explains how the Question must be answered. You are an AI that reads the Question enclosed in triple backticks and \
the Transcript and provides the answer in the mentioned Output Format."""

        self.ann_audio_system_content = """Every prompt will begin with the text \"Question:\" followed by the question \
enclosed in triple backticks. The question will mention that there is an .mp3 file attached however the .mp3 file has \
already been transcribed and the transcribed text is attached after the text: \"Transcription:\". The \"Annotator Steps:\" \
mentions the steps that you should take for answering the question. The text \"Output Format:\" \
explains how the Question must be answered. You are an AI that reads the Question enclosed in triple backticks and \
the Transcript and follows the Annotator Steps and provides the answer in the mentioned Output Format."""

        self.output_format = "Provide a clear and conclusive answer to the Question being asked. Do not provide any \
reasoning or references for your answer."

        self.assistant_instruction = """You are an assistant that answers any questions relevant to the \
file that is uploaded in the thread. """
    
    def format_content(self, format_type: int, question: str, transcription: str = None, annotator_steps: str = None) -> str:
        """
        Formats the content based on whether it is annotated or not.

        Args:
            is_annotated (int): Indicates whether the content is annotated (1 for yes, 0 for no).
            question (str): The question that requires an answer.
            annotator_steps (str, optional): The steps taken by the annotator.
            output_format (str, optional): The desired format of the output.

        Returns:
            str: The formatted content.
        """
        if format_type == 0:
            return f"Question: ```{question}```\nOutput Format: {self.output_format}\n"
        elif format_type == 1:
            return f"Question: ```{question}```\nTranscription: {transcription}\nOutput Format: {self.output_format}\n"
        elif format_type == 2:
            return f"Question: ```{question}```\nTranscription: {transcription}\nAnnotator Steps: {annotator_steps}\nOutput Format: {self.output_format}\n"
        else:
            return f"Question: ```{question}```\nAnnotator Steps: {annotator_steps}\nOutput Format: {self.output_format}\n"
        
    def validation_prompt(self, system_content: str, user_content: str, model: str, imageurl: str = None) -> str:
        """
        Sends a validation prompt to the model and returns the model's response.

        Args:
            system_content (str): The system message that sets the context for the model.
            user_content (str): The user message to validate or respond to.

        Returns:
            str: The model's response.
        """

        try:

            logging_module.log_success(f"System Content: {system_content}")
            logging_module.log_success(f"User Content: {user_content}")

            if imageurl:     
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_content},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_content},
                                {"type": "image_url", 
                                "image_url": {
                                    "url": imageurl,
                                    "detail": "low"
                                    }
                                },
                            ],
                        }
                    ],
                    max_completion_tokens=200,
                )
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content}
                    ],
                    max_completion_tokens=200,
                )

            logging_module.log_success(f"Response: {response.choices[0].message.content}")

            return response.choices[0].message.content
        
        except openai.BadRequestError as e:
            logging_module.log_error(f"Error: {e}")
            return f"Error-BDIA: {e}"
        except openai.APIError as e:
            if e.http_status == 429:
                logging_module.log_error(f"Error: {e}")
                return f"Error-BDIA: {e}"
        except Exception as e:
            logging_module.log_error(f"An unexpected error occurred: {str(e)}")
            return f"Error-BDIA: {e}"
    
    def file_validation_prompt(self, file_path: str, system_content: str, validation_content: str, model: str) -> str:
        """
        Sends a validation prompt with a file to the model and returns the response.

        Args:
            file_path (str): The path to the file to be validated.
            validation_content (str): The user message to validate.

        Returns:
            str: The model's response or the run status if not completed.
        """
        
        try:

            logging_module.log_success(f"System Content: {system_content}")
            logging_module.log_success(f"User Content: {validation_content}")

            file_assistant = self.client.beta.assistants.create(
                instructions=self.assistant_instruction + system_content,
                model=model,
                tools=[{"type": "file_search"}],
            )

            logging_module.log_success(f"Assistant created with ID: {file_assistant.id}")

            query_file = self.client.files.create(file=open(file_path, "rb"), purpose="assistants")

            logging_module.log_success(f"File stored with ID: {query_file.id}")

            empty_thread = self.client.beta.threads.create()

            logging_module.log_success(f"Thread created with ID: {query_file.id}")

            self.client.beta.threads.messages.create(
                empty_thread.id,
                role="user",
                content=validation_content,
                attachments=[{"file_id": query_file.id, "tools": [{"type": "file_search"}]}]
            )

            logging_module.log_success(f"Messages created with ID: {messages.id}")

            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=empty_thread.id,
                assistant_id=file_assistant.id,
                max_completion_tokens=200,
            )

            logging_module.log_success(f"Run executed with ID: {run.id}")

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=run.thread_id
                )

                logging_module.log_success(f"Response: {messages.data[0].content[0].text.value}")

                self.cleanup_resources(file_assistant.id, query_file.id, empty_thread.id)

                return messages.data[0].content[0].text.value
            else:
                logging_module.log_error(f"Run Status: {run.status}")
            
        except openai.BadRequestError as e:
            logging_module.log_error(f"Error: {e}")
            return f"Error-BDIA: {e}"
        except openai.APIError as e:
            if e.http_status == 429:
                logging_module.log_error(f"Error: {e}")
                return f"Error-BDIA: {e}"
        except Exception as e:
            logging_module.log_error(f"An unexpected error occurred: {str(e)}")
            return f"Error-BDIA: {e}"
        
    def ci_file_validation_prompt(self, file_path: str, system_content: str, validation_content: str, model: str) -> str:
        """
        Sends a validation prompt with an XLSX file to the model and returns the response.

        Args:
            file_path (str): The path to the XLSX file to validate.
            validation_content (str): The user message to validate.

        Returns:
            str: The model's response or the run status if not completed.
        """

        try:

            logging_module.log_success(f" System Content: {system_content}")
            logging_module.log_success(f" User Content: {validation_content}")

            file_assistant = self.client.beta.assistants.create(
                instructions=self.assistant_instruction + system_content,
                model=model,
                tools=[{"type": "code_interpreter"}],
            )

            logging_module.log_success(f"Assistant created with ID: {file_assistant.id}")

            query_file = self.client.files.create(file=open(file_path, "rb"), purpose="assistants")

            logging_module.log_success(f"File stored with ID: {query_file.id}")

            empty_thread = self.client.beta.threads.create()

            logging_module.log_success(f"Thread created with ID: {query_file.id}")

            self.client.beta.threads.messages.create(
                empty_thread.id,
                role="user",
                content=validation_content,
                attachments=[{"file_id": query_file.id, "tools": [{"type": "code_interpreter"}]}]
            )

            logging_module.log_success(f"Messages created with ID: {messages.id}")

            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=empty_thread.id,
                assistant_id=file_assistant.id,
                max_completion_tokens=200,
            )

            logging_module.log_success(f"Run executed with ID: {run.id}")

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=empty_thread.id
                )

                logging_module.log_success(f"Response: {messages.data[0].content[0].text.value}")

                self.cleanup_resources(file_assistant.id, query_file.id, empty_thread.id)

                return messages.data[0].content[0].text.value
            else:
                logging_module.log_error(f"Run Status: {run.status}")
            
        except openai.BadRequestError as e:
            logging_module.log_error(f"Error: {e}")
            return f"Error-BDIA: {e}"
        except openai.APIError as e:
            if e.http_status == 429:
                logging_module.log_error(f"Error: {e}")
                return f"Error-BDIA: {e}"
        except Exception as e:
            logging_module.log_error(f"An unexpected error occurred: {str(e)}")
            return f"Error-BDIA: {e}"
    
    def stt_validation_prompt(self, file_path: str) -> str:
        try:
            messages = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=open(file_path, "rb"),
                response_format="text"
            )

            logging_module.log_success(f"Transcript Generated: {messages}")

            return messages
        except openai.BadRequestError as e:
            logging_module.log_error(f"Error: {e}")
            return f"Error-BDIA: {e}"
        except openai.APIError as e:
            if e.http_status == 429:
                logging_module.log_error(f"Error: {e}")
                return f"Error-BDIA: {e}"
        except Exception as e:
            logging_module.log_error(f"An unexpected error occurred: {str(e)}")
            return f"Error-BDIA: {e}"
    
    def cleanup_resources(self, assistant_id: str, file_id: str, thread_id: str) -> None:
        """
        Cleans up the resources by deleting the assistant, file, and thread after the validation is complete.

        Args:
            assistant_id (str): The ID of the assistant to be deleted.
            file_id (str): The ID of the file to be deleted.
            thread_id (str): The ID of the thread to be deleted.

        Returns:
            None
        """
        try:
            # Delete the assistant
            self.client.beta.assistants.delete(assistant_id)
            logging_module.log_success(f"Assistant with {assistant_id} deleted successfully")

            # Delete the file
            self.client.files.delete(file_id)
            logging_module.log_success(f"Assistant with {file_id} deleted successfully")

            # Delete the thread
            self.client.beta.threads.delete(thread_id)
            logging_module.log_success(f"Assistant with {thread_id} deleted successfully")
        except Exception as e:
            logging_module.log_error(f"Error occurred while cleaning up resources!")