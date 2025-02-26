from fastapi import Body
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from backend.modules.query_controllers.base import BaseQueryController
from backend.modules.query_controllers.example.payload import (
    QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
    QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
    QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD,
)
from backend.modules.query_controllers.example.types import ExampleQueryInput
from backend.server.decorators import post, query_controller

EXAMPLES = {
    "vector-store-similarity": QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD,
    "contextual-compression-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
    "contextual-compression-multi-query-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
}


@query_controller("/basic-rag")
class BasicRAGQueryController(BaseQueryController):
    @post("/answer")
    async def answer(
        self,
        request: ExampleQueryInput = Body(
            openapi_examples=EXAMPLES,
        ),
    ):
        """
        Sample answer method to answer the question using the context from the collection
        """
        # Get the vector store
        vector_store = await self._get_vector_store(request.collection_name)

        # Create the QA prompt templates
        QA_PROMPT = PromptTemplate(
            input_variables=["context", "question"],
            template=request.prompt_template,
        )

        # Get the LLM
        llm = self._get_llm(request.model_configuration, request.stream)

        # get retriever
        retriever = await self._get_retriever(
            vector_store=vector_store,
            retriever_name=request.retriever_name,
            retriever_config=request.retriever_config,
        )

        # Using LCEL
        rag_chain_from_docs = (
            RunnablePassthrough.assign(
                # add internet search results to context
                context=(
                    lambda x: self._format_docs(
                        x["context"],
                    )
                )
            )
            | QA_PROMPT
            | llm
            | StrOutputParser()
        )

        rag_chain_with_source = RunnableParallel(
            {"context": retriever, "question": RunnablePassthrough()}
        )

        if request.internet_search_enabled:
            rag_chain_with_source = (
                rag_chain_with_source | self._internet_search
            ).assign(answer=rag_chain_from_docs)
        else:
            rag_chain_with_source = rag_chain_with_source.assign(
                answer=rag_chain_from_docs
            )

        if request.stream:
            return StreamingResponse(
                self._sse_wrap(
                    self._stream_answer(rag_chain_with_source, request.query),
                ),
                media_type="text/event-stream",
            )

        else:
            outputs = await rag_chain_with_source.ainvoke(request.query)

            # Intermediate testing
            # Just the retriever
            # setup_and_retrieval = RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
            # outputs = await setup_and_retrieval.ainvoke(request.query)
            # print(outputs)

            # Retriever, internet search
            # outputs = await (setup_and_retrieval | self.internet_search).ainvoke(request.query)
            # print(outputs)

            # Retriever and QA
            # outputs = await (setup_and_retrieval | QA_PROMPT).ainvoke(request.query)
            # print(outputs)

            # Retriever, QA and LLM
            # outputs = await (setup_and_retrieval | QA_PROMPT | llm).ainvoke(request.query)
            # print(outputs)

            return {
                "answer": outputs["answer"],
                "docs": self._enrich_context_for_non_stream_response(outputs),
            }


#######
# Streaming Client

# import httpx
# from httpx import Timeout

# from backend.modules.query_controllers.example.types import ExampleQueryInput

# payload = {
#   "collection_name": "pstest",
#   "query": "What are the features of Diners club black metal edition?",
#   "model_configuration": {
#     "name": "openai-devtest/gpt-3-5-turbo",
#     "parameters": {
#       "temperature": 0.1
#     },
#     "provider": "truefoundry"
#   },
#   "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
#   "retriever_name": "vectorstore",
#   "retriever_config": {
#     "search_type": "similarity",
#     "search_kwargs": {
#       "k": 20
#     },
#     "filter": {}
#   },
#   "stream": True
# }

# data = ExampleQueryInput(**payload).model_dump()
# ENDPOINT_URL = 'http://localhost:8000/retrievers/example-app/answer'


# with httpx.stream('POST', ENDPOINT_URL, json=data, timeout=Timeout(5.0*60)) as r:
#     for chunk in r.iter_text():
#         print(chunk)
#######
