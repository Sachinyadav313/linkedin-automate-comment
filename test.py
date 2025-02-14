import os
import time
import random
import csv
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from fpdf import FPDF  # Import FPDF for PDF generation

# Load environment variables from .env
load_dotenv()

# Get credentials
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
COMMENT_TEXT = "This is an automated comment. 🚀"

def filter_bmp_characters(text):
    """Filter out non-BMP characters to prevent Selenium errors."""
    return ''.join(char for char in text if ord(char) <= 0xFFFF)

def generate_pdf_report(results):
    """Generate a PDF report with results of LinkedIn comments."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Set title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, txt="LinkedIn Comment Automation Report", ln=True, align='C')
    pdf.ln(10)

    # Set table headers
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 10, "Post Index", border=1, align='C')
    pdf.cell(100, 10, "Post Content", border=1, align='C')
    pdf.cell(50, 10, "Comment Status", border=1, align='C')
    pdf.ln()

    # Add results to PDF
    pdf.set_font('Arial', '', 12)
    for result in results:
        pdf.cell(40, 10, str(result['Post Index']), border=1, align='C')
        pdf.cell(100, 10, result['Post Content'], border=1, align='C')
        pdf.cell(50, 10, result['Comment Status'], border=1, align='C')
        pdf.ln()

    # Save the PDF
    pdf_output_path = "linkedin_comments_report.pdf"
    pdf.output(pdf_output_path)
    print(f"PDF report generated: {pdf_output_path}")

def automate_linkedin_comments(email, password, comment_text):
    options = Options()
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)

    # Prepare a list to store results for the PDF report
    results = []

    try:
        # Step 1: Login to LinkedIn
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)

        driver.find_element(By.ID, "username").send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        time.sleep(5)

        # Step 2: Navigate to LinkedIn feed
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)

        # Scroll to load more posts
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        # Step 3: Find posts
        posts = driver.find_elements(By.CLASS_NAME, "feed-shared-update-v2")
        if not posts:
            print("No posts found.")
            return

        for idx, post in enumerate(posts[:5]):  # Limit to 5 posts
            try:
                # Get post content for reference
                post_content = post.text[:200]  # Extract first 200 characters for the CSV

                # Click "See more" if it exists
                try:
                    see_more_button = post.find_element(By.XPATH, './/button[contains(text(), "See more")]')
                    driver.execute_script("arguments[0].click();", see_more_button)
                    time.sleep(2)
                except:
                    pass  # No "See more" button

                # Locate and click the "Comment" button
                try:
                    comment_button = post.find_element(By.XPATH, './/button[contains(@aria-label, "Comment")]')
                    driver.execute_script("arguments[0].click();", comment_button)
                    time.sleep(2)
                except:
                    print(f"Post {idx + 1}: No comment button found. Skipping...")
                    results.append({"Post Index": idx + 1, "Post Content": post_content, "Comment Status": "No Comment Button"})
                    continue

                # Find the comment text area
                comment_box = post.find_element(By.XPATH, './/div[contains(@role, "textbox")]')

                # Filter BMP characters and inject comment using JavaScript
                filtered_comment_text = filter_bmp_characters(comment_text)
                driver.execute_script("arguments[0].innerText = arguments[1];", comment_box, filtered_comment_text)
                driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", comment_box
                )
                time.sleep(2)

                # Find and click the "Post comment" button
                try:
                    post_button = WebDriverWait(post, 10).until(
                        EC.element_to_be_clickable((By.XPATH, './/button[contains(@class, "comments-comment-box__submit-button--cr") and contains(@class, "artdeco-button--primary")]'))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({ block: 'center', inline: 'nearest' });", post_button)
                    driver.execute_script("arguments[0].click();", post_button)
                    time.sleep(random.uniform(2, 4))  # Wait before moving to the next post
                    print(f"Commented on Post {idx + 1}")
                    results.append({"Post Index": idx + 1, "Post Content": post_content, "Comment Status": "Commented"})
                except Exception as e:
                    print(f"Post {idx + 1}: Unable to click the 'Post comment' button. {e}")
                    results.append({"Post Index": idx + 1, "Post Content": post_content, "Comment Status": "Failed to Comment"})
                    continue

            except Exception as e:
                print(f"Error processing Post {idx + 1}: {e}")
                continue

    finally:
        driver.quit()
        print(f"Automation complete. Generating PDF report.")
        generate_pdf_report(results)

if __name__ == "__main__":
    print("Starting LinkedIn automation...")
    automate_linkedin_comments(EMAIL, PASSWORD, COMMENT_TEXT)
