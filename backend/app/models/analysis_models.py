

from typing import List
from pydantic import BaseModel


CODE_ANALYSIS_TYPES = ["structure", "complexity",
                       "performance", "implementation", "data", "problem_solving"]

# structure: how well the code is organized
# complexity: how complex the code is
# performance: how well the code performs (speed and memory)
# implementation: how well the code implements the requirements
# data: how well the code handles and manipulates data
# problem_solving: how well the code solves problems


class CodeAnalysisQuery:
    def __init__(self, query_id, original_query):
        self.query_id = query_id
        self.original_query = original_query

        self.query = ""
        self.extensions = []
        self.languages: list[CodeAttribute] = []
        self.tools: list[CodeAttribute] = []
        self.skills: list[CodeAttribute] = []

        self.relevant_repos = {}
        self.relevant_files = []
        self.eval_files = []

        self.rubric = None

        # self.repos = []
        # self.files = []
        # self.best_repos = []
        # self.best_files = []


class QueryRubric:
    def __init__(self):
        self.attributes = []


class RubricAttribute:
    def __init__(self):
        self.attribute_id = ""
        self.name = ""
        self.criterion = ""
        self.weight = 1
        self.score = -1

    def copy(self):
        new = RubricAttribute()
        new.attribute_id = self.attribute_id
        new.name = self.name
        new.criterion = self.criterion
        new.weight = self.weight
        new.score = self.score
        return new


class CodeSnippet():
    def __init__(self):
        self.file_path = ""
        self.code = ""
        self.score = -1

        self.repo_name = ""
        self.repo_url = ""
        self.repo_description = ""

        self.rubric_attributes = []


class QueryResponse():
    def __init__(self):
        self.query_id = ""
        self.query = ""
        self.score = -1
        self.code_snippets = []


class AnalyzeAccountResponse():
    def __init__(self):
        self.username = ""
        self.queries: dict[str, QueryResponse] = {}


# ===========================
# tools are things like libraries, frameworks, and languages
# ===========================


class ToolAnalysisQuery:
    def __init__(self, query):
        self.query = query
        self.query_type = ""
        self.tools = []
        self.best_tools = []


class CodeAttribute:
    def __init__(self, name):
        self.name = name
        self.score = -1

    def __repr__(self):
        if self.score == -1:
            return self.name
        return f"{self.name}({self.score})"
