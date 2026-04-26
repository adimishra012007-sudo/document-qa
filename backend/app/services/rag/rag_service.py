import os
from typing import List, Dict, Any
from pinecone import Pinecone as PineconeClient
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from app.core.config import settings

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL
        )
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.MODEL_NAME,
            temperature=0
        )
        
        # Initialize Pinecone
        self.pc = PineconeClient(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        
        # Check if index exists, if not, it should be created manually in Pinecone console
        # or via self.pc.create_index(...) if using Serverless
        self.index = self.pc.Index(self.index_name)

    def index_documents(self, chunks: List[Any], user_id: str, document_id: str):
        """
        Uploads chunks to Pinecone with user_id as namespace.
        """
        # Add metadata to chunks before indexing
        for chunk in chunks:
            chunk.metadata["user_id"] = str(user_id)
            chunk.metadata["document_id"] = document_id

        # Pinecone uses namespaces for multi-tenancy isolation
        # This ensures a query with namespace X never sees data from namespace Y
        vector_store = PineconeVectorStore.from_documents(
            chunks,
            self.embeddings,
            index_name=self.index_name,
            namespace=str(user_id)
        )
        return f"pinecone://{self.index_name}/{user_id}/{document_id}"

    async def condense_question(self, chat_history: List[Dict[str, str]], question: str) -> str:
        """
        Uses LLM to rewrite a conversational question into a standalone query.
        """
        if not chat_history:
            return question

        history_str = ""
        for msg in chat_history[-5:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_str += f"{role}: {msg['content']}\n"

        condense_template = """Given the following conversation and a follow up question, 
        rephrase the follow up question to be a standalone question, in its original language.
        
        Chat History:
        {chat_history}
        Follow Up Input: {question}
        Standalone question:"""

        prompt = PromptTemplate.from_template(condense_template)
        chain = prompt | self.llm
        
        result = await chain.ainvoke({"chat_history": history_str, "question": question})
        return result.content

    async def get_answer(self, query: str, user_id: str, document_id: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieves relevant chunks from Pinecone and generates an answer.
        """
        # 1. Condense question if history exists
        standalone_query = await self.condense_question(chat_history or [], query)
        
        # 2. Connect to user's isolated namespace
        vector_db = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=str(user_id)
        )

        template = """
        You are an expert technical assistant. Your goal is to provide accurate, grounded answers based ONLY on the provided context.
        
        CONTEXT:
        {context}
        
        USER QUESTION:
        {question}
        
        INSTRUCTIONS:
        1. Answer the question using ONLY the information from the CONTEXT above.
        2. If the answer is not contained within the context, state clearly: "I'm sorry, but the provided document does not contain information to answer this question."
        3. Do NOT use outside knowledge or hallucinate details.
        4. Citations: Mention page numbers (e.g., [Page 1]) found in metadata.
        
        FINAL ANSWER:"""
        
        QA_PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])
        k = settings.TOP_K

        # Filter by document_id within the namespace for double isolation
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vector_db.as_retriever(
                search_kwargs={
                    "k": k,
                    "filter": {"document_id": document_id}
                }
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": QA_PROMPT}
        )

        result = qa_chain.invoke({"query": standalone_query})
        
        sources = [{
            "page": doc.metadata.get("page", "N/A"),
            "content": doc.page_content[:200] + "..."
        } for doc in result["source_documents"]]

        return {
            "answer": result["result"],
            "sources": sources
        }
