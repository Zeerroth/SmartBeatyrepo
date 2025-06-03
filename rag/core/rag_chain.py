from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

def get_rag_chain(llm, retriever):
    """
    Create a RAG chain using the given language model and retriever.
    
    Args:
        llm: The language model to use for generating responses.
        retriever: The retriever for finding relevant documents.
        
    Returns:
        A RetrievalQA chain that can be used to answer questions.
    """
    # Define the prompt template for the skincare advisor
    prompt_template_str = """You are a helpful and knowledgeable skincare advisor.
    Your goal is to recommend suitable products based on the user's skin concern and the provided product information.
    When making recommendations, please:
    1. List 1 to 3 products that best match the user's needs based on the context.
    2. For each recommended product, clearly explain *why* it is suitable, referencing specific features, ingredients, or benefits mentioned in the product's context.
    3. If the context for a retrieved product is insufficient to make a strong recommendation for the user's specific query, acknowledge that.
    4. If no suitable products are found in the context for the query, state that you couldn't find specific recommendations from the provided information.
    5. Be concise and focus on actionable advice.

    Context (Retrieved Product Information):
    {context}

    User's Question/Concern: {question}

    Helpful Answer:"""

    PROMPT = PromptTemplate(
        template=prompt_template_str, 
        input_variables=["context", "question"]
    )

    # Create the QA chain with the prompt
    chain_type_kwargs = {"prompt": PROMPT}
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs=chain_type_kwargs,
        return_source_documents=True
    )
    
    return qa_chain
