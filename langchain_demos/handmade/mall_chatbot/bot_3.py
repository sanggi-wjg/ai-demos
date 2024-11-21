import os
from typing import List

from dotenv import load_dotenv
from langchain_community.document_loaders import ConfluenceLoader
from langchain_community.document_loaders.confluence import ContentFormat
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
# set_verbose(True)
# set_debug(False)

JIRA_SPACE_PO = os.getenv("JIRA_SPACE_PO")
JIRA_SPACE_DEV = os.getenv("JIRA_SPACE_DEV")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_URL = os.getenv("JIRA_API_URL")
JIRA_API_KEY = os.getenv("JIRA_API_KEY")
JIRA_CONFLUENCE_API_URL = f"{JIRA_API_URL}/wiki"

DOCUMENTS_CACHE_PATH = "./docs_bot_2.pkl"


def get_one_pager_documents_ids_in_confluence() -> List[str]:
    return [
        "241860609",
    ]


def load_documents() -> List[Document]:
    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n"],
    )
    # space_key, page_ids 는 둘중에 하나만 작동함
    confluence_loader = ConfluenceLoader(
        url=JIRA_CONFLUENCE_API_URL,
        api_key=JIRA_API_KEY,
        username=JIRA_USERNAME,
        content_format=ContentFormat.STORAGE,
        limit=10,
        max_pages=1000,
        keep_markdown_format=False,
        keep_newlines=False,
        # space_key=JIRA_SPACE_PO,
        page_ids=get_one_pager_documents_ids_in_confluence(),
    )
    # confluence_docs = recursive_text_splitter.split_documents(
    #     [doc for doc in confluence_loader.load() if doc.page_content != ""]
    # )
    return confluence_loader.load()


def main():
    llm = ChatOllama(model="llama3.1", temparature=0)
    # llm = ChatGroq(
    #     model="llama-3.1-70b-versatile",
    #     temperature=0,
    #     max_tokens=None,
    #     max_retries=2,
    #     timeout=None,
    # )

    prompt = ChatPromptTemplate.from_template(
        """
    # **Prompt Template: Clarifying Missing Information in PRD or Policies**

    ## **System Context**
    You are a backend developer analyzing a product requirement document (PRD) and policy documentation. Your goal is to identify unclear areas, missing details, or potential edge cases before starting development. Use the provided input to generate a list of clarifying questions.
    
    ---
    
    ## **Prompt Input Format**
    1. **Feature Description:**  
       A high-level description of the feature or functionality.
    
    2. **User Stories:**  
       Key user flows or stories provided in the PRD.
    
    3. **Policies:**  
       Specific rules or guidelines governing the functionality.
    
    4. **Known Constraints:**  
       Any technical or business constraints mentioned.
    
    ---
    
    ## **Expected Output Format**
    - Clarifying questions about **business goals**.  
    - Missing details about **functional requirements**.  
    - Potential **edge cases** or scenarios not covered in the documentation.  
    - **Dependencies** or integration details needing confirmation.
    
    ---
    
    ## **Prompt Example**
    > You are a backend engineer preparing to implement a feature described as:  
    > - **Feature Description:** A shopping cart notification system that alerts users when their cart contains items about to sell out or go on discount.  
    > - **User Stories:** "As a user, I want to receive real-time notifications when an item in my cart has a price drop."  
    > - **Policies:** Notifications should only be sent between 9 AM and 9 PM in the user’s timezone.  
    > - **Known Constraints:** The system must handle up to 100,000 concurrent notifications.
    
    Generate questions to ensure all functional and technical aspects are clear.
    
    ---
    
    ## **Sample Output**
    ### **1. Business Goals**  
    - What is the primary purpose of this feature: increasing conversion rates, reducing abandoned carts, or improving user experience?
    
    ### **2. Functional Requirements**  
    - Should notifications for price drops and stock levels be sent via email, push notifications, or both?  
    - How frequently should stock-level checks be performed (e.g., real-time, hourly)?
    
    ### **3. Edge Cases**  
    - What happens if a user's timezone cannot be determined?  
    - How should notifications behave for users who have disabled notifications in their settings?
    
    ### **4. Dependencies**  
    - Does the notification system need to integrate with an existing messaging service, or should it be built independently?  
    - Are there specific third-party APIs or data sources to use for stock and pricing information?
    
    ---

    # **Document_context** 
    {document_context}""".strip(),
    )
    translate_prompt = ChatPromptTemplate.from_template("Translate '{text_to_translate}' to Korean.")

    analyze_chain = prompt | llm | StrOutputParser()
    translate_chain = {"text_to_translate": analyze_chain} | translate_prompt | llm | StrOutputParser()

    for token in translate_chain.stream({"document_context": load_documents()[0].page_content}):
        print(token, end="", flush=True)

    # while True:
    #     for token in chain.stream({"document_context": load_documents()[0].page_content}):
    #         print(token, end="", flush=True)


if __name__ == "__main__":
    main()
