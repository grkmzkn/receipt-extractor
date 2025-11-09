import google.generativeai as genai
import PIL.Image
import json
import time
import os
from dotenv import load_dotenv
import utils

load_dotenv()
####################################################################
# Gemini API Configuration
####################################################################
genai.configure(api_key = os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

####################################################################
# Image preprocessing
####################################################################
process_start_time = time.time()
image_path = "./data/fuel-2.jpeg"
img = utils.preprocess_image(image_path)

####################################################################
# Detects receipt type
####################################################################
type_contents = [
    img,
    utils.TYPE_DETERMINATION_PROMPT
]

type_response = model.generate_content(type_contents)
receipt_type = type_response.text.strip().upper()

####################################################################
# Extract informations from the receipt
####################################################################
contents = [
    img,
    f"""Extract the receipt information based on the determined type ({receipt_type}) 
    and return ONLY a valid JSON object with the following structure:
    {utils.PROMPTS[receipt_type]}
    Return ONLY the JSON object with no additional text or formatting.""",
]

response = model.generate_content(contents)

try:
    if not response.text:
        raise ValueError("API response error!")
    
    json_string = response.text
    cleaned_json = utils.clean_json_string(json_string)
    receipt_data = json.loads(cleaned_json)

    print(f"Fiş Türü: {receipt_data.get('type', 'N/A')}")
    print(f"İşletme Adı: {receipt_data.get('business_name', 'N/A')}")
    print(f"Tarih: {receipt_data.get('date', 'N/A')}")
    
    if receipt_data.get('type') == "FUEL":
        if 'license_plate' in receipt_data:
            print(f"Plaka: {receipt_data.get('license_plate', 'N/A')}")
    
    if receipt_data.get('type') == "MARKET":
        if 'items' in receipt_data and isinstance(receipt_data['items'], list):
            print("\nAlınan Ürünler:")
            for item in receipt_data['items']:
                print(f"{item.get('name', 'N/A')}")
                print(f"Fiyat: {item.get('price', 'N/A')}")
                print("-------------------")

    print(f"Toplam Tutar: {receipt_data.get('total_amount', 'N/A')}")

except:
    print(f"Hata oluştu:")
    
process_end_time = time.time()
process_duration = process_end_time - process_start_time
print(f"Processing time: {process_duration:.2f} seconds")