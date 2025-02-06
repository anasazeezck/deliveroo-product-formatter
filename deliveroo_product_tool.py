import streamlit as st
from PIL import Image, ImageOps
import openai
import os
import io
import requests
from io import BytesIO

# Load OpenAI API Key securely
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to generate Deliveroo-optimized SEO title and description
def generate_seo_content(product_name):
    try:
        prompt = f"""
        Generate a Deliveroo-optimized product title (max 120 characters) and description (max 500 characters) for the product: {product_name}.

        - **Title:** Use high-intent customer search keywords and make it conversion-focused.
        - **Description:** Highlight key benefits, use engaging language, and naturally insert keywords.
        - **Ensure:** The title and description comply with Deliveroo’s ranking algorithm.
        - **Format Output Strictly as:**
          Title: [Generated Title]
          Description: [Generated Description]
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in e-commerce product optimization."},
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = response["choices"][0]["message"]["content"]
        
        # Extract title and description correctly
        title, description = "Error extracting response", "Error extracting response"
        if "Title:" in response_text and "Description:" in response_text:
            title = response_text.split("Title:")[1].split("Description:")[0].strip()[:120]
            description = response_text.split("Description:")[1].strip()[:500]
        
        return title, description
    
    except Exception as e:
        return "Error: OpenAI API request failed.", str(e)

# Function to process an image from a URL
def process_product_image(image_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(image_url, headers=headers, stream=True)
        
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            
            # Convert unsupported AVIF format by fetching as JPG if necessary
            if img.format not in ["WEBP", "PNG", "JPEG", "JPG"]:
                return None, "Error: Unsupported image format. Please use WEBP, JPG, JPEG, or PNG."
            
            img = img.convert("RGBA")
            
            # Check minimum resolution
            if img.width < 500 or img.height < 500:
                return None, "Error: Image resolution is too low. Minimum required: 500x500 pixels."
            
            base_width, base_height = 1200, 800
            img.thumbnail((base_width - 100, base_height - 100), Image.LANCZOS)
            
            white_canvas = Image.new("RGBA", (base_width, base_height), (255, 255, 255, 255))
            img_w, img_h = img.size
            x_offset = (base_width - img_w) // 2
            y_offset = (base_height - img_h) // 2
            
            white_canvas.paste(img, (x_offset, y_offset), img)
            processed_img = white_canvas.convert("RGB")
            
            return processed_img, None
        else:
            return None, f"Error: Unable to fetch the image from the provided URL. Status Code: {response.status_code}"
    
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

# Streamlit UI
def main():
    st.title("Deliveroo Product Content & Image Formatter")
    st.write("Paste a product image URL and enter the product name. This tool will generate Deliveroo-optimized titles & descriptions and format the image.")
    
    product_name = st.text_input("Enter Product Name:")
    image_url = st.text_input("Paste Image URL:")
    
    if st.button("Process Product"):
        if product_name and image_url:
            title, description = generate_seo_content(product_name)
            processed_img, error_msg = process_product_image(image_url)
            
            if error_msg:
                st.error(error_msg)
            else:
                st.subheader("Generated SEO Title (Max 120 characters):")
                st.write(title)
                
                st.subheader("Generated SEO Description (Max 500 characters):")
                st.write(description)
                
                st.subheader("Processed Product Image:")
                st.image(processed_img, caption="Formatted Image", use_column_width=True)
                
                img_byte_arr = io.BytesIO()
                processed_img.save(img_byte_arr, format='JPEG', quality=100)
                img_byte_arr = img_byte_arr.getvalue()
                
                st.download_button(
                    label="Download Processed Image",
                    data=img_byte_arr,
                    file_name="formatted_product.jpg",
                    mime="image/jpeg"
                )
        else:
            st.error("Please enter a product name and paste a valid image URL.")

if __name__ == "__main__":
    main()
