# Real-Time Notes Maker

An intelligent clinical note-making agent that listens to doctor-patient conversations in real-time and automatically generates comprehensive medical notes. This AI-powered system captures the entire consultation, processes it in the background, and produces structured SOAP notes at the end of the meeting.

## 🚀 Features

- **Real-time Conversation Processing**: Actively listens to and processes doctor-patient conversations during consultations
- **End-of-Meeting Note Generation**: Automatically generates comprehensive medical notes after the consultation
- **SOAP Notes Generation**: Creates structured SOAP (Subjective, Objective, Assessment, Plan) notes from the conversation
- **AI-Powered Summarization**: Utilizes Google's Gemini multimodal AI to intelligently summarize and structure the consultation
- **Customizable Templates**: Doctors can customize note templates and dropdown options through the backend
- **Background Processing**: Efficient handling of conversation chunks and note generation using Celery
- **Modern Web Interface**: Built with Streamlit for an intuitive user experience

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance web framework for building APIs
- **Celery**: Distributed task queue for background processing
- **Redis**: In-memory data store for task queue management
- **Google Gemini AI**: Multimodal AI model for note generation and summarization
- **LangChain**: Framework for building LLM-powered applications

### Frontend
- **Streamlit**: Modern web interface for real-time interaction
- **Python**: Core programming language


## 🏗️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd real-time-notes-maker
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Unix/MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with the following variables:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   REDIS_URL=your_redis_url
   ```

5. **Start Redis server**
   ```bash
   # Make sure Redis is running on your system
   ```

6. **Start Celery worker**
   ```bash
   celery -A app.worker worker --loglevel=info
   ```

7. **Run the application**

   # In a separate terminal, start the Streamlit frontend
   streamlit run streamlit_frontend.py
   ```

## 🔑 Key Features

### Conversation Processing
- Real-time audio capture of doctor-patient conversations
- Intelligent chunking and processing of conversation segments
- Background processing using Celery for efficient resource utilization
- Automatic speech-to-text conversion

### SOAP Notes Generation
- End-of-meeting comprehensive note generation
- Structured note generation following SOAP format
- Customizable templates and dropdown options
- Evidence-based note generation using AI
- Context-aware summarization of the entire consultation

