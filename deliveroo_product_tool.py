import streamlit as st
from PIL import Image
import io
import requests
import os
from io import BytesIO
import openai  # Keep this in case you want to switch back easily

# Load API key securely from environment variable
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Set this in your local/system environment

# Function to generate Deliveroo-optimized SEO title and description using DeepSeek API
def generate_seo_content(product_name):
    if not DEEPSEEK_API_KEY:
        return None, "Error: DeepSeek API key is missing. Please set it in your environment variables."

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an expert in e-commerce SEO, specializing in Deliveroo product listings."},
            {"role": "user", "content": f"""
                Generate a Deliveroo-optimized product title (max 120 characters) and description (max 500 characters) for the product: {product_name}.

                - **Title:** Use high-intent customer search keywords and make it conversion-focused.
                - **Description:** Highlight key benefits, use engaging language, and naturally insert keywords.
                - **Ensure:** The title and description comply with Deliveroo’s ranking algorithm.
                - **Format Output Strictly as:**
                  Title: [Generated Title]
                  Description: [Generated Description]
            """}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"].split("\n")
        title = content[0].replace("Title:", "").strip()[:120]
        description = content[1].replace("Description:", "").strip()[:500]
        return title, description
    else:
        return None, f"Error: {response.json()}"

# Function to process product image to 1200x800 with a white background
def process_product_image(image_url):
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content)).convert("RGBA")

        # Check image resolution
        if img.size[0] < 500 or img.size[1] < 500:
            return None, "Error: Image resolution is too low. Minimum required: 500x500 pixels."

        # Prepare canvas
        base_width, base_height = 1200, 800
        img.thumbnail((base_width - 100, base_height - 100))  # Resize while maintaining aspect ratio
        white_canvas = Image.new("RGBA", (base_width, base_height), (255, 255, 255, 255))

        # Center the image
        x_offset = (base_width - img.size[0]) // 2
        y_offset = (base_height - img.size[1]) // 2
        white_canvas.paste(img, (x_offset, y_offset), img)

        return white_canvas.convert("RGB"), None
    else:
        return None, "Error: Unable to fetch the image from the provided URL."

# Streamlit Web App UI
def main():
    st.title("Deliveroo Product Processor (DeepSeek AI Edition)")
    st.write("Enter a product name and paste an image URL to generate Deliveroo-optimized content and process the image.")

    product_name = st.text_input("Enter Product Name:")
    image_url = st.text_input("Paste Image URL:")

    if st.button("Process Product"):
        if product_name and image_url:
            title, description = generate_seo_content(product_name)
            
            if not title:
                st.error(description)  # If there's an API error, show the message
                return

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
            st.error("Please enter a product name and a valid image URL.")

if __name__ == "__main__":
    main()
