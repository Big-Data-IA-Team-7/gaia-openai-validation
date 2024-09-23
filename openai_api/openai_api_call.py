from openai import OpenAI

class OpenAIClient:
    def __init__(self):
        """
        Initializes the OpenAIClient with a specified model.

        Args:
            model (str): The model ID to be used for generating completions (default: "gpt-4o").
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

        self.output_format = "Provide only text in the answer to the question. Do not provide any attachments or code."

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
        
    def validation_prompt(self, system_content: str, user_content: str, model: str = "gpt-4o", imageurl: str = None) -> str:
        """
        Sends a validation prompt to the model and returns the model's response.

        Args:
            system_content (str): The system message that sets the context for the model.
            user_content (str): The user message to validate or respond to.

        Returns:
            str: The model's response.
        """
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
                max_tokens=1000,
            )
        else:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=75,
            )
        return response.choices[0].message.content
    
    def file_validation_prompt(self, file_path: str, system_content: str, validation_content: str, model: str = "gpt-4o") -> str:
        """
        Sends a validation prompt with a file to the model and returns the response.

        Args:
            file_path (str): The path to the file to be validated.
            validation_content (str): The user message to validate.

        Returns:
            str: The model's response or the run status if not completed.
        """
        file_assistant = self.client.beta.assistants.create(
            instructions=self.assistant_instruction + system_content,
            model=model,
            tools=[{"type": "file_search"}],
        )

        query_file = self.client.files.create(file=open(file_path, "rb"), purpose="assistants")
        empty_thread = self.client.beta.threads.create()

        self.client.beta.threads.messages.create(
            empty_thread.id,
            role="user",
            content=validation_content,
            attachments=[{"file_id": query_file.id, "tools": [{"type": "file_search"}]}]
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=empty_thread.id,
            assistant_id=file_assistant.id,
            max_completion_tokens=75
        )

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=run.thread_id
            )

            self.cleanup_resources(file_assistant.id, query_file.id, empty_thread.id)

            return messages.data[0].content[0].text.value
        else:
            
            self.cleanup_resources(file_assistant.id, query_file.id, empty_thread.id)
            
            return run.status
        
    def ci_file_validation_prompt(self, file_path: str, system_content: str, validation_content: str, model: str = "gpt-4o") -> str:
        """
        Sends a validation prompt with an XLSX file to the model and returns the response.

        Args:
            file_path (str): The path to the XLSX file to validate.
            validation_content (str): The user message to validate.

        Returns:
            str: The model's response or the run status if not completed.
        """
        file_assistant = self.client.beta.assistants.create(
            instructions=self.assistant_instruction + system_content,
            model=model,
            tools=[{"type": "code_interpreter"}],
        )

        query_file = self.client.files.create(file=open(file_path, "rb"), purpose="assistants")
        empty_thread = self.client.beta.threads.create()

        self.client.beta.threads.messages.create(
            empty_thread.id,
            role="user",
            content=validation_content,
            attachments=[{"file_id": query_file.id, "tools": [{"type": "code_interpreter"}]}]
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=empty_thread.id,
            assistant_id=file_assistant.id,
            max_completion_tokens=75
        )

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=empty_thread.id
            )

            self.cleanup_resources(file_assistant.id, query_file.id, empty_thread.id)

            return messages.data[0].content[0].text.value
        else:

            self.cleanup_resources(file_assistant.id, query_file.id, empty_thread.id)

            return run.status
    
    def stt_validation_prompt(self, file_path: str) -> str:
        messages = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=open(file_path, "rb"),
            response_format="text"
        )

        return messages
    
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
            print(f"Assistant {assistant_id} deleted successfully.")

            # Delete the file
            self.client.files.delete(file_id)
            print(f"File {file_id} deleted successfully.")

            # Delete the thread
            self.client.beta.threads.delete(thread_id)
            print(f"Thread {thread_id} deleted successfully.")
        except Exception as e:
            print(f"Error during resource cleanup: {e}")