import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

###################################################################
# Image Preprocessing Functions
###################################################################

def preprocess_image(image_path):
    """
    Preprocess the image to get more accurate results from llm models.

    Args:
        image_path (str): image path

    Returns:
        image: preprocessed image
    """
    # Open image with PIL and preserve orientation
    img = Image.open(image_path)
    
    # Store original orientation to apply at the end
    original_img = img.copy()
    
    # Convert to OpenCV format for advanced processing
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding to better separate text from background
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 21, 10)
    
    # Noise removal with morphological operations
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # Skip deskewing as it might be causing orientation issues
    # Convert back to PIL format - ensure it's in the right mode for web display
    enhanced_img = Image.fromarray(opening).convert('RGB')
    
    # Apply additional PIL enhancements
    enhancer = ImageEnhance.Contrast(enhanced_img)
    enhanced_img = enhancer.enhance(2.0)  # Increased contrast
    
    sharpener = ImageEnhance.Sharpness(enhanced_img)
    enhanced_img = sharpener.enhance(2.0)  # Increased sharpness
    
    # Ensure the enhanced image has the same size as the original
    enhanced_img = enhanced_img.resize(original_img.size)
    
    return enhanced_img

###################################################################
# Output Cleaning Functions
###################################################################

def clean_json_string(text):
    """
    clean the json string to get more accurate results from llm models.

    Args:
        text (str): response from llm models

    Returns:
        text: cleaned text to be used in json.loads()
    """
    
    try:
        if '```json' in text:
            text = text.split('```json')[1]
        elif '```' in text:
            text = text.split('```')[1]
        if '```' in text:
            text = text.rsplit('```', 1)[0]
        
        text = text.strip()
        text = text.replace('\n', '').replace('\r', '')
        
        return text
    
    except Exception as e:
        print(f"Error in cleaning process: {e}")
        return text

def normalize_monetary_value(value_str):
    """
    Normalize monetary values by removing currency symbols and standardizing decimal separators.
    
    Args:
        value_str (str): The monetary value as a string
        
    Returns:
        str: Normalized monetary value
    """
    if value_str.lower() == "n/a":
        return value_str.lower()
    
    # Remove currency symbols and text
    cleaned = value_str.lower().replace("tl", "").replace("₺", "").replace("lira", "").strip()
    
    try:
        # Convert to float by first standardizing format
        # Replace comma with dot for decimal point
        numeric_str = cleaned.replace(",", ".")
        
        # Convert to float and format with 2 decimal places
        float_value = float(numeric_str)
        return f"{float_value:.2f}"
    except ValueError:
        # If conversion fails, return the original cleaned string
        return cleaned
    
###################################################################
# Prompt Configuration
###################################################################

TYPE_DETERMINATION_PROMPT = """Determine the type of receipt from the image. Return ONLY one of these values: 
"FUEL" for fuel/gas station receipts, 
"MARKET" for grocery/market receipts, 
"RESTAURANT" for food/restaurant receipts.
Return ONLY the type with no additional text."""

PROMPTS = {
    "FUEL": """
    {
        "type": "FUEL",
        "business_name": "Name of the gas station",
        "date": "Date of purchase (DD.MM.YYYY)",
        "license_plate": "Vehicle license plate number which locates under the date and above the VAT percentage",
        "total_amount": "Total amount paid",
        "vat_percentage": "VAT percentage"
    }
    """,
    "RESTAURANT": """
    {
        "type": "RESTAURANT",
        "business_name": "Name of the restaurant",
        "date": "Date of purchase (DD.MM.YYYY)",
        "total_amount": "Total amount paid",
        "vat_percentage": "VAT percentage"
    }
    """,
    "MARKET": """
    {
        "type": "MARKET",
        "business_name": "Name of the market/store",
        "date": "Date of purchase (DD.MM.YYYY)",
        "total_amount": "Total amount paid",
        "items": [
            {
                "name": "Item name (item name can not be contains only kg information. It should be concat with next line. It should be like this: 2,078 KG X 24,99 TL MV. Sogan KURU.)",
                "price": "Item price"
            },
            ...
        ]
    }
    """
}