import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
import utils

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="🧾 Receipt Extractor",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Universal Dark/Light Mode Compatible Colors */
    .stApp {
        background-color: var(--background-color);
    }
    
    /* High contrast text that works on both themes */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: var(--text-color) !important;
    }
    
    .element-container p, .element-container span {
        color: var(--text-color) !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .metric-card {
        background: rgba(79, 70, 229, 0.05);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid rgba(79, 70, 229, 0.2);
        margin-bottom: 1rem;
        color: #4f46e5;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .receipt-info {
        background: rgba(16, 185, 129, 0.05);
        padding: 2rem;
        border-radius: 12px;
        border: 2px solid rgba(16, 185, 129, 0.3);
        color: #059669;
        font-weight: 500;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .receipt-info h4 {
        color: #047857 !important;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    
    .receipt-info p {
        color: #065f46 !important;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .success-message {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: none;
        margin: 1rem 0;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }
    
    .error-message {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: none;
        margin: 1rem 0;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
        color: white;
        border: 2px solid rgba(255, 255, 255, 0.2);
        padding: 0.75rem 2.5rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.4s ease;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.3);
        backdrop-filter: blur(10px);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
        background: linear-gradient(135deg, #5b21b6 0%, #9333ea 50%, #f43f5e 100%);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(79, 70, 229, 0.05);
        border-right: 2px solid rgba(79, 70, 229, 0.2);
    }
    
    /* Metric containers */
    .css-1r6slb0 {
        background: rgba(16, 185, 129, 0.05);
        border: 2px solid rgba(16, 185, 129, 0.2);
        border-radius: 12px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_gemini():
    """Initialize Gemini API client"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("🔑 GEMINI_API_KEY not found in environment variables!")
            st.stop()
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"❌ Failed to initialize Gemini: {str(e)}")
        st.stop()

def analyze_receipt(uploaded_file, model):
    """
    Analyze uploaded receipt image using the existing workflow
    """
    try:
        # Process start time
        process_start_time = time.time()
        
        # Create temporary file from uploaded image
        temp_path = f"temp_{uploaded_file.name}"
        
        # Save uploaded file temporarily
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Preprocess image using existing utils function
        with st.spinner("🔧 Preprocessing image..."):
            processed_img = utils.preprocess_image(temp_path)
        
        # Detect receipt type
        with st.spinner("🏷️ Detecting receipt type..."):
            type_contents = [processed_img, utils.TYPE_DETERMINATION_PROMPT]
            type_response = model.generate_content(type_contents)
            receipt_type = type_response.text.strip().upper()
        
        # Extract information based on detected type
        with st.spinner(f"🧠 Extracting {receipt_type.lower()} receipt information..."):
            contents = [
                processed_img,
                f"""Extract the receipt information based on the determined type ({receipt_type}) 
                and return ONLY a valid JSON object with the following structure:
                {utils.PROMPTS[receipt_type]}
                Return ONLY the JSON object with no additional text or formatting.""",
            ]
            
            response = model.generate_content(contents)
            
            if not response.text:
                raise ValueError("Empty API response!")
            
            # Clean and parse JSON response
            json_string = response.text
            cleaned_json = utils.clean_json_string(json_string)
            receipt_data = json.loads(cleaned_json)
        
        # Calculate processing time
        process_end_time = time.time()
        process_duration = process_end_time - process_start_time
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "success": True,
            "data": receipt_data,
            "processing_time": process_duration,
            "processed_image": processed_img
        }
        
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parsing error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Analysis error: {str(e)}"}
    finally:
        # Ensure cleanup
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

def display_receipt_results(result_data, container):
    """Display analysis results in the specified container"""
    
    with container:
        data = result_data["data"]
        receipt_type = data.get("type", "UNKNOWN")
        processing_time = result_data.get("processing_time", 0)
        
        st.markdown("### 📊 Analysis Results")
        
        # Processing time metric
        st.metric(
            label="⚡ Processing Time",
            value=f"{processing_time:.2f}s",
            delta=f"{'Fast' if processing_time < 3 else 'Normal'}"
        )
        
        # Combined receipt information card
        receipt_info_content = f"""
        <div class="receipt-info">
            <h4>🧾 Receipt Information</h4>
            <p><strong>Receipt Type:</strong> {receipt_type}</p>
            <p><strong>Business Name:</strong> {data.get('business_name', 'N/A')}</p>
            <p><strong>Date:</strong> {data.get('date', 'N/A')}</p>
            <p><strong>Total Amount:</strong> {data.get('total_amount', 'N/A')} TL</p>
            <p><strong>VAT Percentage:</strong> {data.get('vat_percentage', 'N/A')}</p>"""
        
        # Add license plate for fuel receipts
        if receipt_type == "FUEL" and 'license_plate' in data:
            receipt_info_content += f"""
            <p><strong>License Plate:</strong> {data.get('license_plate', 'N/A')}</p>"""
        
        receipt_info_content += """
        </div>
        """
        
        st.markdown(receipt_info_content, unsafe_allow_html=True)
        
        # Market items section
        if receipt_type == "MARKET" and 'items' in data:
            st.markdown("#### 🛍️ Purchased Items")
            
            if isinstance(data['items'], list) and data['items']:
                # Display items in an expandable section
                with st.expander(f"📋 View All Items ({len(data['items'])} items)", expanded=True):
                    for i, item in enumerate(data['items'], 1):
                        st.markdown(f"""
                        <div class="metric-card">
                            <strong style="color: #4f46e5; font-size: 1.1rem;">{i}. {item.get('name', 'N/A')}</strong><br>
                            <span style="color: #059669; font-weight: bold; font-size: 1.2rem;">💰 {item.get('price', 'N/A')} TL</span>
                        </div>
                        """, unsafe_allow_html=True)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧾 Receipt Extractor</h1>
        <p>Upload receipt images and extract information using AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Gemini
    model = initialize_gemini()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔧 Settings")
        
        st.markdown("""
        **Supported Receipt Types:**
        - 🏪 Market/Grocery receipts  
        - ⛽ Fuel station receipts
        - 🍽️ Restaurant receipts
        """)
        
        st.markdown("---")
        
        st.markdown("""
        **Supported Formats:**
        - JPG, JPEG, PNG
        - Max size: 10MB
        """)
        
        st.markdown("---")
        
        st.markdown("### 🎯 How it Works")
        
        st.markdown("""
        1. **📤 Upload** your receipt image
        2. **🔧 Preprocessing** enhances image quality  
        3. **🏷️ Type Detection** identifies receipt category
        4. **🧠 AI Analysis** extracts structured information
        5. **📊 Results** displayed in beautiful format
        """)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📤 Upload Receipt Image")
        
        uploaded_file = st.file_uploader(
            "Choose a receipt image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of your receipt for analysis"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            image = PIL.Image.open(uploaded_file)
            st.image(image, caption="Uploaded Receipt", use_column_width=True)
            
            # Analysis button
            if st.button("🚀 Analyze Receipt", key="analyze_btn"):
                with st.container():
                    # Analysis progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Update progress
                    for i in range(100):
                        progress_bar.progress(i + 1)
                        time.sleep(0.01)
                    
                    status_text.text("✅ Analysis complete!")
                    
                    # Perform analysis
                    result = analyze_receipt(uploaded_file, model)
                    
                    if result["success"]:
                        st.markdown("""
                        <div class="success-message">
                            ✅ <strong>Analysis Successful!</strong> Receipt information extracted successfully.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display results in the right column
                        display_receipt_results(result, col2)
                        
                        # Download results as JSON
                        json_string = json.dumps(result["data"], indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download Results (JSON)",
                            data=json_string,
                            file_name=f"receipt_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        
                    else:
                        st.markdown(f"""
                        <div class="error-message">
                            ❌ <strong>Analysis Failed:</strong> {result.get('error', 'Unknown error')}
                        </div>
                        """, unsafe_allow_html=True)
    
    # Col2 is now used for displaying results when analysis is performed

if __name__ == "__main__":
    main()
