# core/rag_chain.py
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory # A common memory type
# from langchain.llms import OpenAI # If not using ChatOpenAI directly in the chain
from langchain_openai import ChatOpenAI


def get_rag_chain(llm: ChatOpenAI, retriever):
    """
    Creates a simple RetrievalQA chain for single queries (no memory).
    """
    # Simple prompt for single-turn Q&A
    qa_prompt_template = """You are SmartBeauty, an expert and friendly skincare advisor.
Use the following pieces of context (retrieved product information) to answer the question at the end.
If you don't know the answer from the context, just say that you don't know, don't try to make up an answer.
When making recommendations, clearly explain *why* a product is suitable based on the product information provided.

Context:
{context}

Question: {question}
Helpful Answer:"""
    
    QA_PROMPT = PromptTemplate(
        template=qa_prompt_template, 
        input_variables=["context", "question"]
    )
    
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_PROMPT}
    )


# Your existing get_rag_chain for RetrievalQA can remain if you want both options.
# Let's create a new function for the conversational chain.

# You might need a separate prompt for condensing the question
CONDENSE_QUESTION_PROMPT_TEMPLATE = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}

Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(CONDENSE_QUESTION_PROMPT_TEMPLATE)


def get_conversational_rag_chain(llm: ChatOpenAI, retriever, memory, condense_question_prompt=CONDENSE_QUESTION_PROMPT):
    """
    Creates a ConversationalRetrievalChain.
    """
    # The qa_prompt is for the final answer generation step, using retrieved docs
    qa_prompt_template_str = """You are SmartBeauty, an expert and friendly skincare advisor.
    Use the following pieces of context (retrieved product information) and the chat history to answer the question at the end.
    If you don't know the answer from the context or history, just say that you don't know, don't try to make up an answer.
    If the question is about a specific product mentioned earlier, use the context provided for that product.
    If the question is a new concern, try to recommend suitable products from the context.
    When making recommendations, clearly explain *why* a product is suitable.

    Chat History:
    {chat_history}

    Retrieved Product Context:
    {context}

    Question: {question}
    Helpful Answer:"""
    QA_PROMPT = PromptTemplate(
        template=qa_prompt_template_str, input_variables=["chat_history", "context", "question"]
    )

    # ConversationalRetrievalChain can use an LLM to condense the question
    # It can also take a question_generator chain.
    # For the combine_docs_chain, we use an LLMChain with our QA_PROMPT.
    
    # This is the chain that will take the (condensed) question and retrieved documents to generate the final answer.
    from langchain.chains.llm import LLMChain
    from langchain.chains.combine_documents.stuff import StuffDocumentsChain

    doc_chain = StuffDocumentsChain(
        llm_chain=LLMChain(llm=llm, prompt=QA_PROMPT),
        document_variable_name="context" # Ensure this matches QA_PROMPT
    )
    
    # This is the chain that rephrases the question
    question_generator_chain = LLMChain(llm=llm, prompt=condense_question_prompt)

    conversational_chain = ConversationalRetrievalChain(
        retriever=retriever,
        question_generator=question_generator_chain, # Chain to generate standalone question
        combine_docs_chain=doc_chain,          # Chain to answer based on docs and question
        memory=memory,
        return_source_documents=True,
        # verbose=True # For debugging
    )
    return conversational_chain