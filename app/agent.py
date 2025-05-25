from google import genai
from pydantic import BaseModel, ValidationError
from log_exp_wrapper import log_exceptions
import os
from typing import Optional

# Pydantic schemas
class Format(BaseModel):
    parameter: str
    evidence: list[str]

class SOAPNote(BaseModel):
    Subjective: Format
    Objective: Format
    Assessment: Format
    Plan: Format

class Report(BaseModel):
    detailed_summary: str
    SOAP_note_so_far: SOAPNote

# Initialize the Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@log_exceptions
def generate_clinical_report(
    visit_type: str,
    audio_file_path: str,
    previous_report: Optional[Report] = None,
) -> Report:
    """
    Generate a detailed summary and SOAP report based on audio input.

    Args:
        visit_type: The type of clinical visit (e.g., "Initial Consultation", "Follow-up", "Telemedicine").
        audio_file_path: Path to the audio file containing the clinical notes.
        previous_report: Optional previous Report object to update or append new findings.

    Returns:
        Report: Parsed Pydantic Report object with detailed summary and SOAP note.
    """
    # Upload audio file
    uploaded_file = client.files.upload(file=audio_file_path)


    # Build prompt with optional previous report
    prompt_parts = [
        f"Type of Visit: {visit_type}",
        "You are given an audio transcript chunk from a clinical scenario."
    ]
    if previous_report:
        prompt_parts.append(
            "Here is the previous report to update with new information (include exact evidences):"
        )
        prompt_parts.append(str(previous_report))
    prompt_parts.append(
        "Your tasks:\n"
        "1. Provide a detailed summary of the new information.\n"
        "2. Update or draft the SOAP note so far, including evidence (exact transcription words) for each section."
    )
    prompt = "\n\n".join(prompt_parts)

    # Call the model
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt, uploaded_file],
        config={
            "response_mime_type": "application/json",
            "response_schema": Report,
        }
    )

    # Parse and return
    try:
        report = Report.parse_raw(response.text)
    except ValidationError as e:
        raise RuntimeError(f"Failed to parse model response: {e}\nResponse was: {response.text}")
    return report

