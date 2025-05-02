from prompts.question_rewriter_prompt import question_rewriter_prompt

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser



def question_rewriter_creator(llm):
    #print(question_rewriter_prompt)
    system = question_rewriter_prompt
    re_write_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human","Here is the initial question: \n\n {question} \n Formulate an improved question.",
            ),
        ]
    )

    question_rewriter = re_write_prompt | llm | StrOutputParser()
    return question_rewriter

#uncomment the below line of code when you want test the question re-writer
#question_rewriter.invoke({"question": question})