import streamlit as st
import pyaudio
import wave
import threading
import time
import os
from datetime import datetime
import queue
from app.service import create_visit,upload_chunk,get_report
# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100



def get_visit_id(soap_type: str) -> str:
    # In a real app, replace this with a call to your backend/service
    return create_visit(soap_type)

class AudioRecorder:
    def __init__(self,visit_id, chunk_duration=10, output_folder="audio_chunks" ):
        self.chunk_duration = chunk_duration
        self.output_folder = output_folder
        self.visit_id = visit_id
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.frames = []
        
        # Create output folder if it doesn't exist
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
    
    def start_recording(self):
        self.is_recording = True
        self.frames = []
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
            
            st.success("Recording started...")
            
            chunk_start_time = time.time()
            chunk_frames = []
            chunk_number = 1
            
            while self.is_recording:
                data = stream.read(CHUNK)
                chunk_frames.append(data)
                
                # Check if chunk duration has elapsed
                if time.time() - chunk_start_time >= self.chunk_duration:
                    # Save current chunk
                    self.save_chunk(chunk_frames, chunk_number)
                    
                    # Reset for next chunk
                    chunk_frames = []
                    chunk_start_time = time.time()
                    chunk_number += 1
            
            # Save any remaining frames when recording stops
            if chunk_frames:
                self.save_chunk(chunk_frames, chunk_number,is_final=True)
                
        except Exception as e:
            st.error(f"Error during recording: {str(e)}")
        finally:
            # Clean up
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    def save_chunk(self, frames, chunk_number , is_final=False):
        filename = f"chunk_{chunk_number:03d}_{self.visit_id}.wav"
        filepath = os.path.join(self.output_folder, filename)
        
        # Save the chunk as a WAV file
        p = pyaudio.PyAudio()
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        p.terminate()
        upload_chunk(self.visit_id,chunk_number,filepath,is_final)
        st.info(f"Saved chunk: {filename}")
    
    def stop_recording(self):
        self.is_recording = False

def main():
    st.set_page_config(layout="wide", page_title="SOAP Report Viewer")
    st.title("🎤 Audio Recorder with Chunking")
    st.write("Records continuous audio and saves chunks at regular intervals")
    
    # Initialize session state
    if 'recorder' not in st.session_state:
        st.session_state.recorder = None
    if 'recording_thread' not in st.session_state:
        st.session_state.recording_thread = None
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'visit_id' not in st.session_state:
        st.session_state.visit_id = None

    visit_type = st.selectbox("Select the type of medical visit:", [
        "General Checkup", "followup"
    ])

    # Button to get visit ID
    if st.button("Get Visit ID"):
        visit_id = get_visit_id(visit_type)
        if visit_id != -1:
            st.session_state.visit_id = visit_id  # <-- Store it in session_state
            st.success(f"Visit ID for '{visit_type}' is {visit_id}")
        else:
            st.error("Invalid visit type selected.")
    
    # Configuration
    col1, col2  = st.columns(2)
    with col1:
        chunk_duration = st.number_input("Chunk Duration (seconds)", 
                                       min_value=1, max_value=300, value=10)
    with col2:
        output_folder = st.text_input("Output Folder", value="audio_chunks")
        
    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start Recording", disabled=st.session_state.is_recording):
            if st.session_state.visit_id is None:
                st.error("Please get a Visit ID before starting recording.")
            else:
                st.session_state.recorder = AudioRecorder(st.session_state.visit_id,chunk_duration, output_folder )
                st.session_state.recording_thread = threading.Thread(
                    target=st.session_state.recorder.start_recording
                )
                st.session_state.recording_thread.start()
                st.session_state.is_recording = True
                st.rerun()
    
    with col2:

        if st.button("⏹️ Stop Recording", disabled=not st.session_state.is_recording):
            if st.session_state.recorder:
                st.session_state.recorder.stop_recording()
                st.session_state.recording_thread.join()
                st.session_state.is_recording = False
                st.success("Recording stopped!")
                st.rerun()
    

    if "recording_start_time" not in st.session_state:
        st.session_state.recording_start_time = None
    if "last_chunk_time" not in st.session_state:
        st.session_state.last_chunk_time = None

    if st.session_state.get("is_recording", False):
        if st.session_state.recording_start_time is None:
            st.session_state.recording_start_time = time.time()
            st.session_state.last_chunk_time = time.time()

        # Live updating timer UI using a placeholder
        timer_placeholder = st.empty()

        while True:
            now = time.time()
            elapsed = int(now - st.session_state.recording_start_time)
            time_since_last_chunk = now - st.session_state.last_chunk_time
            time_remaining = max(0, int(chunk_duration - time_since_last_chunk))

            # Update display
            with timer_placeholder.container():
                st.info("🔴 Recording in progress...")
                st.write(f"⏱️ Recording time elapsed: `{elapsed} seconds`")
                st.write(f"⏳ Next chunk in: `{time_remaining} seconds`")
                st.write(f"Saving chunks every {chunk_duration} seconds to: `{output_folder}/`")

            # Simulate chunk save
            if time_remaining == 0:
                st.session_state.last_chunk_time = now
                # Optional: actual chunk-saving logic here

            time.sleep(1)

    if st.button("Fetch Follow-Up SOAP Report"):
        report = get_report(st.session_state.visit_id)
        
        # Display detailed summary if available
        if hasattr(report, 'detailed_summary') or 'detailed_summary' in report:
            detailed_summary = getattr(report, 'detailed_summary', report.get('detailed_summary', ''))
            if detailed_summary:
                st.info(f"**Visit Summary:** {detailed_summary}")
                st.divider()
        
        st.subheader("🏥 SOAP Clinical Report - Follow-Up Visit")
        
        # Handle structured SOAP data
        if hasattr(report, 'SOAP_note_so_far') or 'SOAP_note_so_far' in report:
            soap_data = getattr(report, 'SOAP_note_so_far', report.get('SOAP_note_so_far'))
            
            # Create columns for better layout
            col1, col2 = st.columns([1, 3])
            
            # Subjective Section
            with col1:
                st.markdown("### 📝 **Subjective**")
            with col2:
                if hasattr(soap_data, 'Subjective') and soap_data.Subjective:
                    subj = soap_data.Subjective
                    if hasattr(subj, 'parameter') and subj.parameter != 'N/A':
                        st.markdown(f"**Chief Concern:** {subj.parameter}")
                    
                    if hasattr(subj, 'evidence') and subj.evidence:
                        st.markdown("**Patient Reports:**")
                        for evidence in subj.evidence:
                            st.markdown(f"• *\"{evidence}\"*")
                else:
                    st.markdown("*No subjective data recorded*")
            
            st.divider()
            
            # Objective Section
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### 🔍 **Objective**")
            with col2:
                if hasattr(soap_data, 'Objective') and soap_data.Objective:
                    obj = soap_data.Objective
                    if hasattr(obj, 'parameter') and obj.parameter != 'N/A':
                        st.markdown(f"**Findings:** {obj.parameter}")
                    
                    if hasattr(obj, 'evidence') and obj.evidence:
                        st.markdown("**Clinical Observations:**")
                        for evidence in obj.evidence:
                            st.markdown(f"• {evidence}")
                    else:
                        st.markdown("*Physical examination pending*")
                else:
                    st.markdown("*No objective data recorded*")
            
            st.divider()
            
            # Assessment Section
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### 🎯 **Assessment**")
            with col2:
                if hasattr(soap_data, 'Assessment') and soap_data.Assessment:
                    assess = soap_data.Assessment
                    if hasattr(assess, 'parameter') and assess.parameter != 'N/A':
                        st.markdown(f"**Diagnosis:** {assess.parameter}")
                    
                    if hasattr(assess, 'evidence') and assess.evidence:
                        st.markdown("**Clinical Reasoning:**")
                        for evidence in assess.evidence:
                            st.markdown(f"• {evidence}")
                    else:
                        st.warning("⚠️ Assessment pending clinical evaluation")
                else:
                    st.warning("⚠️ Assessment pending clinical evaluation")
            
            st.divider()
            
            # Plan Section
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### 📋 **Plan**")
            with col2:
                if hasattr(soap_data, 'Plan') and soap_data.Plan:
                    plan = soap_data.Plan
                    if hasattr(plan, 'parameter') and plan.parameter != 'N/A':
                        st.markdown(f"**Treatment Plan:** {plan.parameter}")
                    
                    if hasattr(plan, 'evidence') and plan.evidence:
                        st.markdown("**Interventions:**")
                        for evidence in plan.evidence:
                            st.markdown(f"• {evidence}")
                    else:
                        st.warning("⚠️ Treatment plan to be determined")
                else:
                    st.warning("⚠️ Treatment plan to be determined")
        
        # Fallback for simple dictionary format
        elif isinstance(report, dict):
            for section, content in report.items():
                if section not in ['detailed_summary', 'SOAP_note_so_far']:
                    st.markdown(f"**{section.title()}:**")
                    st.markdown(content)
                    st.divider()
        
        # Add action buttons at the bottom
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 Export Report", use_container_width=True):
                st.success("Report export functionality would be implemented here")
        with col2:
            if st.button("✏️ Edit Notes", use_container_width=True):
                st.info("Edit functionality would be implemented here")
        with col3:
            if st.button("📧 Share Report", use_container_width=True):
                st.info("Share functionality would be implemented here")

    # Display saved files
    # if os.path.exists(output_folder):
    #     files = [f for f in os.listdir(output_folder) if f.endswith('.wav')]
    #     if files:
    #         st.subheader("📁 Saved Audio Chunks")
    #         files.sort(reverse=True)  # Show newest first
            
    #         for file in files[:10]:  # Show last 10 files
    #             file_path = os.path.join(output_folder, file)
    #             file_size = os.path.getsize(file_path)
    #             st.write(f"📄 {file} ({file_size:,} bytes)")
                
    #             # Add audio player for each file
    #             with open(file_path, 'rb') as audio_file:
    #                 st.audio(audio_file.read(), format='audio/wav')
            
    #         if len(files) > 10:
    #             st.write(f"... and {len(files) - 10} more files")

if __name__ == "__main__":
    main()