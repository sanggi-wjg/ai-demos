from ollama_ocr import OCRProcessor

ocr = OCRProcessor(
    model_name="gemma3:12b",
    base_url="http://localhost:11434/api/generate",
    max_workers=1,
)
result = ocr.process_image(
    image_path="m_1459501106_1459500949539_274.jpg",  # path to your pdf files "path/to/your/file.pdf"
    format_type="json",  # Options: markdown, text, json, structured, key_value
    # custom_prompt="Extract all text, focusing on dates and names.",  # Optional custom prompt
    custom_prompt="""
Analyze a mobile voucher image to extract 'voucher name', 'valid until date', 'store name', and 'barcode number', and return the data as  JSON.
Ensure the JSON response includes the additional field "accuracy score" to indicate the confidence level of recognition.

<!IMPORTANT>
Ensure accuracy and pay particular attention to 'barcode number' and 'valid until date'.
<!IMPORTANT>

<Requirements>
When you analyze the image, pay attention to the following:
- Since 'barcode number' and 'valid until date' are very important, double-check their accuracy. Think slowly, and do not answer if unsure.
- Do not guess. Only include values in the JSON if they are recognized with high confidence. If unknown, return a blank field.
- "accuracy score" should be an integer ranging from 0 to 100.
- 'valid until date' must be in the format 'yyyyy/mm/dd'
</Requirements>

<Output Format>
{{
    "voucher name": "...",
    "valid until date": "...",
    "store name": "...",
    "barcode number": "...",
    "accuracy score": ranging from 0 to 100, as an integer.
}} 
</Output Format>
""".strip(),
    language="Korean",  # Specify the language of the text (New! 🆕)
)
print(result)
