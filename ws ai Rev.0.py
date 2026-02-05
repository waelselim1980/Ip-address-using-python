"""
Advanced AI Assistant - Standalone Application
Complete application with file upload support for all formats
High-capability coding assistant
"""

from flask import Flask, request, jsonify
import openai
import os
import sys
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
import json
import tempfile

# Try to import optional dependencies
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️  PyPDF2 not installed. PDF support disabled.")

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    print("⚠️  python-docx not installed. DOCX support disabled.")

try:
    import pandas as pd
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False
    print("⚠️  pandas not installed. Excel/CSV advanced support disabled.")

try:
    from PIL import Image
    import pytesseract
    OCR_SUPPORT = True
except ImportError:
    OCR_SUPPORT = False
    print("⚠️  Pillow/pytesseract not installed. OCR support disabled.")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Get API key from environment or prompt user
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("\n" + "="*60)
    print("🔑 OpenAI API Key Required")
    print("="*60)
    OPENAI_API_KEY = input("Please enter your OpenAI API key: ").strip()
    if not OPENAI_API_KEY:
        print("❌ API key is required to run the application!")
        sys.exit(1)

client = openai.OpenAI(api_key=OPENAI_API_KEY)

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv',
    'json', 'xml', 'html', 'md', 'py', 'js', 'java', 'cpp', 'c',
    'cs', 'php', 'rb', 'go', 'rs', 'swift', 'kt', 'ts',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'log',
    'sh', 'bat', 'ps1', 'sql', 'r', 'scala', 'm', 'h'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    if not PDF_SUPPORT:
        return "PDF support not available. Install PyPDF2: pip install PyPDF2"
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text if text.strip() else "Could not extract text from PDF"
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file_path):
    if not DOCX_SUPPORT:
        return "DOCX support not available. Install python-docx: pip install python-docx"
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text if text.strip() else "Document appears to be empty"
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_excel(file_path):
    if not EXCEL_SUPPORT:
        return "Excel support not available. Install pandas and openpyxl: pip install pandas openpyxl"
    try:
        df = pd.read_excel(file_path, sheet_name=None)
        text = ""
        for sheet_name, data in df.items():
            text += f"\n{'='*50}\nSheet: {sheet_name}\n{'='*50}\n"
            text += data.to_string(index=False) + "\n"
        return text
    except Exception as e:
        return f"Error reading Excel: {str(e)}"

def extract_text_from_csv(file_path):
    if EXCEL_SUPPORT:
        try:
            df = pd.read_csv(file_path)
            return f"CSV Data ({len(df)} rows):\n{df.to_string(index=False)}"
        except Exception as e:
            return f"Error with pandas CSV: {str(e)}"
    
    # Fallback to basic CSV reading
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading CSV: {str(e)}"

def extract_text_from_image(file_path):
    if not OCR_SUPPORT:
        return "OCR support not available. Install Pillow and pytesseract: pip install Pillow pytesseract"
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text if text.strip() else "No text detected in image"
    except Exception as e:
        return f"OCR Error: {str(e)}. Make sure Tesseract is installed."

def read_text_file(file_path):
    try:
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        return "Could not decode file with any standard encoding"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def process_file(file_path, filename):
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    try:
        if extension == 'pdf':
            return extract_text_from_pdf(file_path)
        elif extension == 'docx':
            return extract_text_from_docx(file_path)
        elif extension in ['xls', 'xlsx']:
            return extract_text_from_excel(file_path)
        elif extension == 'csv':
            return extract_text_from_csv(file_path)
        elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            return extract_text_from_image(file_path)
        elif extension == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        elif extension in ['txt', 'md', 'html', 'xml', 'py', 'js', 'java', 'cpp', 'c', 'cs',
                          'php', 'rb', 'go', 'rs', 'swift', 'kt', 'ts', 'log', 'sh', 'bat',
                          'ps1', 'sql', 'r', 'scala', 'm', 'h']:
            return read_text_file(file_path)
        else:
            return f"File type '{extension}' recognized but content extraction may be limited."
    except Exception as e:
        return f"Error processing file: {str(e)}"

@app.route('/')
def home():
    return HTML_TEMPLATE

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form.get('question', '')
    file_content = ""
    file_info = ""
    
    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(file_path)
                file_content = process_file(file_path, filename)
                file_info = f"\n\n[Attached file: {filename}]\n{'='*60}\nFile Content:\n{'='*60}\n{file_content}"
                
                # Clean up
                try:
                    os.remove(file_path)
                except:
                    pass
            except Exception as e:
                file_info = f"\n\n[Error processing file: {str(e)}]"
    
    try:
        system_message = """You are an elite AI assistant with exceptional capabilities in:

🎯 CODING & SOFTWARE DEVELOPMENT (Expert Level):
- Write production-ready, optimized code in ANY programming language
- Debug complex issues and provide detailed explanations
- Design scalable architectures and systems
- Implement design patterns and best practices
- Write comprehensive tests and documentation
- Optimize for performance, security, and maintainability
- Code reviews with actionable feedback

📊 DATA & DOCUMENT ANALYSIS:
- Extract insights from PDFs, Word docs, Excel, CSV
- Process and analyze structured/unstructured data
- Create data visualizations and reports
- Handle OCR from images

🔧 TECHNICAL EXPERTISE:
- Algorithms and data structures
- Database design (SQL/NoSQL)
- API design and integration
- DevOps and CI/CD
- Security best practices
- Performance optimization

💡 PROBLEM SOLVING:
- Break down complex problems systematically
- Provide multiple solution approaches
- Consider edge cases and trade-offs
- Step-by-step implementation guides

CODING STANDARDS:
✓ Clean, readable, well-commented code
✓ Proper error handling
✓ Input validation
✓ Security considerations
✓ Performance optimization
✓ Scalability in design
✓ Test coverage suggestions
✓ Clear documentation

Always provide complete, functional solutions ready for production use."""

        full_prompt = user_input + file_info
        
        # Use GPT-4 for maximum capability
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        assistant_reply = response.choices[0].message.content
        return jsonify({"answer": assistant_reply})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# Embedded HTML template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced AI Assistant - All-in-One</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            width: 100%;
            max-width: 1000px;
            height: 90vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 30px;
            text-align: center;
            border-radius: 20px 20px 0 0;
        }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header p { font-size: 14px; opacity: 0.9; }
        .capabilities {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            margin-top: 15px;
            border-radius: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }
        .capability-badge {
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 20px;
            display: flex;
            animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user { justify-content: flex-end; }
        .message-content {
            max-width: 75%;
            padding: 15px 20px;
            border-radius: 18px;
            line-height: 1.6;
            word-wrap: break-word;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 5px;
        }
        .message.assistant .message-content {
            background: white;
            color: #333;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            border-bottom-left-radius: 5px;
        }
        .message-content pre {
            background: #282c34;
            color: #abb2bf;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        .message-content code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
        .message-content pre code {
            background: transparent;
            padding: 0;
        }
        .file-attachment {
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 12px;
            border-radius: 8px;
            margin-top: 8px;
            font-size: 13px;
            display: inline-block;
        }
        .input-container {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e0e0e0;
            border-radius: 0 0 20px 20px;
        }
        .file-upload-section {
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .file-input-wrapper {
            position: relative;
            overflow: hidden;
            display: inline-block;
        }
        .file-input-wrapper input[type=file] {
            position: absolute;
            left: -9999px;
        }
        .file-button {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .file-button:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .file-name {
            font-size: 13px;
            color: #666;
            padding: 8px 12px;
            background: #f0f0f0;
            border-radius: 8px;
            max-width: 350px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .clear-file {
            background: #ff4757;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        }
        .clear-file:hover { background: #ee2d3c; }
        .input-form {
            display: flex;
            gap: 10px;
        }
        .input-field {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.3s;
        }
        .input-field:focus { border-color: #667eea; }
        .send-button {
            padding: 15px 35px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .send-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .error {
            background: #ff4757;
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .supported-formats {
            font-size: 11px;
            color: #888;
            margin-top: 5px;
        }
        .chat-container::-webkit-scrollbar { width: 8px; }
        .chat-container::-webkit-scrollbar-track { background: #f1f1f1; }
        .chat-container::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
        .chat-container::-webkit-scrollbar-thumb:hover { background: #555; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Advanced AI Assistant</h1>
            <p>Upload files, ask questions, get expert coding help & analysis</p>
            <div class="capabilities">
                <span class="capability-badge">📄 Documents</span>
                <span class="capability-badge">💻 Code Expert</span>
                <span class="capability-badge">📊 Data Analysis</span>
                <span class="capability-badge">🖼️ Image OCR</span>
                <span class="capability-badge">🚀 Production Code</span>
                <span class="capability-badge">🔍 Problem Solver</span>
            </div>
        </div>
        <div class="chat-container" id="chatContainer">
            <div class="message assistant">
                <div class="message-content">
                    👋 <strong>Welcome to your Advanced AI Assistant!</strong><br><br>
                    <strong>💻 Elite Coding Capabilities:</strong><br>
                    • Write production-ready code in any language<br>
                    • Debug, optimize, and review your code<br>
                    • Design scalable architectures<br>
                    • Implement algorithms & data structures<br><br>
                    <strong>📁 File Processing:</strong><br>
                    • Documents: PDF, Word, Excel, CSV<br>
                    • Code: Python, JS, Java, C++, Go, Rust, and more<br>
                    • Images: JPG, PNG with OCR<br>
                    • Data: JSON, XML, Markdown<br><br>
                    <strong>Upload a file or ask anything!</strong>
                </div>
            </div>
        </div>
        <div class="input-container">
            <div class="file-upload-section">
                <div class="file-input-wrapper">
                    <button class="file-button" onclick="document.getElementById('fileInput').click()">
                        📎 Attach File
                    </button>
                    <input type="file" id="fileInput" accept="*/*">
                </div>
                <span class="file-name" id="fileName" style="display: none;"></span>
                <button class="clear-file" id="clearFile" style="display: none;" onclick="clearFile()">✕ Clear</button>
            </div>
            <div class="supported-formats">
                Supported: PDF, Word, Excel, CSV, Images, All code files, JSON, XML, Markdown, HTML, and more
            </div>
            <form class="input-form" id="chatForm">
                <input type="text" class="input-field" id="questionInput" 
                    placeholder="Ask anything or describe what you need..." required>
                <button type="submit" class="send-button" id="sendButton">Send</button>
            </form>
        </div>
    </div>
    <script>
        const chatContainer = document.getElementById('chatContainer');
        const chatForm = document.getElementById('chatForm');
        const questionInput = document.getElementById('questionInput');
        const sendButton = document.getElementById('sendButton');
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const clearFileBtn = document.getElementById('clearFile');
        let selectedFile = null;

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                selectedFile = e.target.files[0];
                fileName.textContent = `📎 ${selectedFile.name}`;
                fileName.style.display = 'inline-block';
                clearFileBtn.style.display = 'inline-block';
            }
        });

        function clearFile() {
            selectedFile = null;
            fileInput.value = '';
            fileName.style.display = 'none';
            clearFileBtn.style.display = 'none';
        }

        function addMessage(content, isUser, hasFile = false, attachmentName = '') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            if (hasFile && attachmentName) {
                content += `<div class="file-attachment">📎 ${attachmentName}</div>`;
            }
            
            content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
            });
            
            contentDiv.innerHTML = content;
            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showError(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = `❌ Error: ${message}`;
            chatContainer.appendChild(errorDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const question = questionInput.value.trim();
            if (!question) return;

            addMessage(question, true, selectedFile !== null, selectedFile ? selectedFile.name : '');
            questionInput.value = '';
            sendButton.disabled = true;
            sendButton.innerHTML = '<span class="loading"></span>';

            const formData = new FormData();
            formData.append('question', question);
            if (selectedFile) {
                formData.append('file', selectedFile);
            }

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.error) {
                    showError(data.error);
                } else {
                    addMessage(data.answer, false);
                }
            } catch (error) {
                showError('Failed to communicate with server. Please try again.');
            } finally {
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
                if (selectedFile) clearFile();
            }
        });

        questionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    </script>
</body>
</html>"""

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 ADVANCED AI ASSISTANT - STANDALONE APPLICATION")
    print("="*70)
    print("📋 Features:")
    print("   ✓ Multi-format file upload (PDF, Word, Excel, Images, Code)")
    print("   ✓ Expert-level coding assistance")
    print("   ✓ Document analysis & data processing")
    print("   ✓ OCR for images")
    print("   ✓ Production-ready code generation")
    print("\n📦 Optional Dependencies:")
    print(f"   {'✓' if PDF_SUPPORT else '✗'} PDF Support (PyPDF2)")
    print(f"   {'✓' if DOCX_SUPPORT else '✗'} Word Support (python-docx)")
    print(f"   {'✓' if EXCEL_SUPPORT else '✗'} Excel/CSV Support (pandas)")
    print(f"   {'✓' if OCR_SUPPORT else '✗'} OCR Support (Pillow/pytesseract)")
    print("\n💡 To install all dependencies:")
    print("   pip install PyPDF2 python-docx pandas openpyxl Pillow pytesseract")
    print("\n🌐 Server starting on: http://localhost:8080")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=8080)