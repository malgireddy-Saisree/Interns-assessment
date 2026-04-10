"""
FAQ agent — retrieves information using faq_search_tool and
formats a grounded answer. In the current architecture the planner
handles this directly via tool calling, but this module provides
a reusable helper.
"""
import json
from tools.faq_search_tool import faq_search_tool


def get_faq_answer(question: str) -> str:
    """
    Call the FAQ search tool and return the raw result string.
    The planner's GPT-4o will format a natural-language answer from this.
    """
    return faq_search_tool.invoke({"question": question})
