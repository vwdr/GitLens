import json
import random
from dotenv import load_dotenv
import os
import openai
# from config import config
import asyncio
from app.models.analysis_models import *
from app.utils.github import *

MIN_CODE_CHUNK_LENGTH = 750

config = {
    "MODEL_STRING": "mistralai/Mistral-7B-Instruct-v0.1"
    # "MODEL_STRING": "gpt-3.5-turbo"
}

load_dotenv()
together_key = os.getenv("TOGETHER_KEY")

client = openai.AsyncOpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=together_key)
# client = openai.AsyncOpenAI(
#     api_key=os.getenv("OPENAI_API_KEY")
# )


# api function calls these in order
# 1 - query graphql --> all the repos and metadata (sophia)
# 1.5 - calculate relevance of repos (sonav)
# 2 - download relevant repos (sophia) (process into repo object)
# 2.5 - get relevant files (sonav) --> file objects that are relevant
# 3 - get relevant code (sophia) (git blame for relevant files)
# 3.5 - score the code based on the query (sonav)

async def calculate_relevance(repos: dict[str, GitRepository], queries: dict[str, CodeAnalysisQuery]):
    # split repos into batches of 5
    batches = []
    current_batch = {}
    for repo_id in repos:
        if len(current_batch) == 5:
            batches.append(current_batch)
            current_batch = {}
        current_batch[repo_id] = repos[repo_id]
    if len(current_batch) > 0:
        batches.append(current_batch)

    tasks = [evaluate_repo_batch_relevance(
        batch, queries, client) for batch in batches]
    await asyncio.gather(*tasks)

    return


async def find_relevant_files(queries: dict[str, CodeAnalysisQuery]):
    # NOTE: doesn't filter based on whether the user has written to the file or not

    print("in find_relevant_files", flush=True)
    print(queries, flush=True)

    tasks = [evaluate_files_relevance(query, client)
             for query_id, query in queries.items()]
    await asyncio.gather(*tasks)

    print("return_files")
    return


def eval_queries(queries: dict[str, CodeAnalysisQuery]):
    tasks = [eval_query(query, client) for query_id, query in queries.items()]
    return asyncio.gather(*tasks)


# ===========================
# helper functions
# ===========================

def repo_to_string(repo):
    # shortened_description = await shorten_description(repo.description)
    string = f"Repo name: {repo.name}\n"
    if (repo.description):
        string += f"Description: {repo.description}\n"
    if (len(repo.languages) > 0):
        string += f"Languages: {', '.join(repo.languages)}\n"

    most_useful_commit_messages = []
    for commit in repo.commits:
        if len(most_useful_commit_messages) > 30:
            break
        # make sure it doesn't start with "Merge"
        # make sure its longer than 10 characters
        lower_message = commit.message.lower()
        starts_with_merge = lower_message.startswith("merge")
        starts_with_update = lower_message.startswith("update")
        starts_with_initial = lower_message.startswith("initial")
        if not starts_with_merge and not starts_with_update and not starts_with_initial and len(commit.message) > 10:
            most_useful_commit_messages.append(commit.message)
    if len(most_useful_commit_messages) > 0:
        commits = "\n".join(most_useful_commit_messages)
        string += f"Commits:\n{commits}\n"
    return string


# async def process_repos(repos):
#     print("Processing repos", flush=True)

#     tasks = [shorten_description(repo.description) for repo in repos]
#     descriptions = await asyncio.gather(*tasks)

#     # Updating repo descriptions with their shortened versions
#     for repo, description in zip(repos, descriptions):
#         repo.description = description

#     return repos

#     # async def process_repo(repo):
#     #     repo.description = await shorten_description(repo.description)
#     #     return repo

#     # tasks = [process_repo(repo) for repo in repos]
#     # return_repos = await asyncio.gather(*tasks)
#     # return return_repos


# async def shorten_description(description):
#     print("Shortening description of repo" +
#           description[:10] + "...", flush=True)
#     instructions = f"""
#         You are given a README of a Github repository and asked to shorten it to 200 characters or less.
#         Return the shortened description as a string.
#     """
#     response = await client.chat.completions.create(
#         model=config["MODEL_STRING"],
#         messages=[
#             {
#                 "role": "system",
#                 "content": instructions
#             }, {
#                 "role": "user",
#                 "content": description[:200]
#             }
#         ],
#     )

#     first_choice = response.choices[0]
#     completion = first_choice.message.content
#     return completion


async def evaluate_repo_batch_relevance(repos: dict[str, GitRepository], queries: dict[str, CodeAnalysisQuery], client: openai.AsyncOpenAI):
    instructions = """
        You are given multiple Github repositories and asked to calculate the relevance of each repository to the given queries.
        - Relevance is a score from 0 to 10, where 10 is the most relevant and 0 is the least relevant.
        - Repositories are relevant if they have the chance to contain key words, key languages, key technologies, or key concepts that are relevant to the queries.
        - Repositories can be relevant to multiple queries.
        - If the repository uses a language that is relevant to the query, it must be relevant.
        Return a JSON object with a map of query to relevance for each repository as follows:
        "repo_N": {
            "query_0": relevance,
            "query_1": relevance,
            ...
        }
        where 0 <= relevance <= 10
        """

    input_string = ""

    for repo_id in repos:
        input_string += f"### {repo_id} ###\n"
        repo_string = repo_to_string(repos[repo_id])
        input_string += repo_string + "\n"

    input_string += "### queries ###:\n"
    for query_id in queries:
        input_string += f"{query_id}: {queries[query_id].query} " + \
            f"({', '.join(queries[query_id].extensions)})\n"
    input_string += "\n"

    response = await client.chat.completions.create(
        model=config["MODEL_STRING"],
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a software analyst who is familiar with Github repositories and tasked with finding repositories that are relevant to queries."
            },
            {
                "role": "user",
                "content": instructions
            }, {
                "role": "user",
                "content": input_string
            }
        ],
        # temperature=0.3,
    )
    completion = json.loads(response.choices[0].message.content)

    print(input_string, completion, flush=True)

    for repo_id in completion:
        repo_relevances = completion[repo_id]
        repo = repos[repo_id]
        if (repo and repo_relevances):
            repo.query_relevances = repo_relevances

    return


async def evaluate_files_relevance(query, client):

    print("apple")
    for repo_id, repo in query.relevant_repos.items():
        print("banana")
        for file_path, file in repo.files.items():
            print("cherry")
            query.eval_files.append(file)

    return

    print("in evaluate_files_relevance goldfish1", flush=True)

    # for each query
    # for each file in every repo that's relevant to the query
    # score the file based on how relevant it is to the query

    prompt = f"""
        You are given a list Github repositories and the file paths in each repository.
        For each repository are asked to select the 10 files with the highest relevance to the given query.
        Files are relevant if they are likely to contain code that is relevant to the query.

        Return a JSON object with the following format:
        {{
            "repo_0": [
                "file_path_0",
                "file_path_1",
                ...
            ],
            "repo_1": [
                ...
            ],
            ...
        }}
        """

    input_strings = []

    for repo_id, repo in query.relevant_repos.items():
        input_string = ""
        input_string += f"### {repo_id} ###\n"
        if (repo.name):
            input_string += f"Repo name: {repo.name}\n"
        if (repo.description):
            input_string += f"Description: {repo.description}\n"
        input_string += "\nFile paths:\n"
        for file_path in repo.files:
            input_string += f"{file_path}\n"
        input_string += f"### Query: {query.query}\n"

        input_strings.append(input_string)

    # input_string += f"### Query: {query.query}\n"

    print("sending goldfish", flush=True)

    async def send_request(input_string):
        return await client.chat.completions.create(
            model=config["MODEL_STRING"],
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": prompt
                }, {
                    "role": "user",
                    "content": input_string
                }
            ],
        )

    tasks = [send_request(input_string) for input_string in input_strings]
    responses = await asyncio.gather(*tasks)

    # response = await client.chat.completions.create(
    #     model=config["MODEL_STRING"],
    #     response_format={"type": "json_object"},
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": prompt
    #         }, {
    #             "role": "user",
    #             "content": input_string
    #         }
    #     ],
    # )

    print("in evaluate_files_relevance goldfish", flush=True)
    for response in responses:
        completion = json.loads(response.choices[0].message.content)
        print(input_string, completion, flush=True)

        for repo_id, file_paths in completion.items():
            repo = query.relevant_repos.get(repo_id, None)
            if (not repo):
                continue

            if (not file_paths):
                continue

            for file_path in file_paths:
                if file_path in repo.files:
                    file = repo.files[file_path]
                    query.eval_files.append(file)

    return


async def eval_query(query, client):
    all_code_chunks = []

    for file in query.eval_files:
        code_chunks_with_file = [(file, code_chunk)
                                 for code_chunk in file.relevant_code]

        all_code_chunks.extend(code_chunks_with_file)

    if (len(all_code_chunks) == 0):
        query_response = QueryResponse()
        query_response.query_id = query.query_id
        query_response.query = query.query
        query_response.score = 0
        query_response.code_snippets = []
        return query_response

    all_code_chunks = sorted(
        all_code_chunks, key=lambda x: len(x[1]), reverse=True)
    all_code_chunks = all_code_chunks[:10]

    tasks = [eval_code_chunk(code_chunk, file, query, client)
             for file, code_chunk in all_code_chunks]
    snippets = await asyncio.gather(*tasks)

    # remove the None's
    snippets = [snippet for snippet in snippets if snippet]

    # # find the top 5
    # top_5 = sorted(results, key=lambda x: x.score, reverse=True)[:5]

    if (len(snippets) == 0):
        query_response = QueryResponse()
        query_response.query_id = query.query_id
        query_response.query = query.query
        query_response.score = 0
        query_response.code_snippets = []
        return query_response

    # average the scores of the top 5
    total_score = 0
    for snippet in snippets:
        total_score += snippet.score
    average_score = total_score / len(snippets)

    query_response = QueryResponse()
    query_response.query_id = query.query_id
    query_response.query = query.query
    query_response.score = average_score
    query_response.code_snippets = snippets

    return query_response


async def eval_code_chunk(code_chunk, file, query: CodeAnalysisQuery, client):

    # print("EVALUATING CODE CHUNK DAIRY", flush=True)
    # print(code_chunk, flush=True)

    if (len(code_chunk) < MIN_CODE_CHUNK_LENGTH):
        return None

    print("length of code chunk", len(code_chunk), flush=True)
    # pick a random section of 1000 characters
    # if the code chunk is less than 1000 characters, use the whole thing
    if (len(code_chunk) > 1000):
        start = random.randint(0, len(code_chunk) - 1000)
        code_chunk = code_chunk[start:start + 1000]

    prompt = f"""
        You are given a code snippet and a list of attributes to evaluate the code against.
        For each attribute, return true if the code demonstrates the attribute, and false if it does not.

        Return a JSON object with the following format:
        {{
            "attribute_0": true or false,
            "attribute_1": true or false,
            ...
        }}
    """

    input_string = ""
    input_string += f"### Code ###\n"
    input_string += code_chunk + "\n"
    input_string += f"### End of Code ###\n\n"
    input_string += f"### Attributes ###\n"
    for attribute in query.rubric.attributes:
        input_string += f"{attribute.attribute_id} -" + \
            f" {attribute.name}: {attribute.criterion}\n"

    response = await client.chat.completions.create(
        model=config["MODEL_STRING"],
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": prompt
            }, {
                "role": "user",
                "content": input_string
            }
        ],
    )

    completion = json.loads(response.choices[0].message.content)

    new_code_snippet = CodeSnippet()
    new_code_snippet.file_path = file.path
    new_code_snippet.code = code_chunk
    new_code_snippet.score = 0
    new_code_snippet.repo_name = file.repo.name
    new_code_snippet.repo_url = file.repo.url
    new_code_snippet.repo_description = file.repo.description
    new_code_snippet.rubric_attributes = []

    total_weight = 0
    total_score = 0

    for attribute in query.rubric.attributes:
        if (attribute.attribute_id in completion):
            total_weight += attribute.weight
            total_score += attribute.weight * \
                1 if completion[attribute.attribute_id] else 0

            attribute_copy = attribute.copy()
            attribute_copy.score = attribute.weight * \
                1 if completion[attribute.attribute_id] else 0
            new_code_snippet.rubric_attributes.append(attribute_copy)

    new_code_snippet.score = round(10 * total_score / total_weight)

    return new_code_snippet


async def construct_queries(queries):
    # TODO: let the model break queries into smaller parts
    query_map: dict[str, CodeAnalysisQuery] = {}
    for i, query in enumerate(queries):
        query_id = f"query_{i}"
        new_query = CodeAnalysisQuery(query_id=query_id, original_query=query)
        query_map[query_id] = new_query

        new_query.query = query  # in case the model doesn't return anything

    # return query_map

    prompt = """
        You are given a list of queries and asked process them.
        Each query will be used to search for relevant code in a Github repository.

        For each query, return the following:
        - The file extensions that are relevant to the query.
            - Be sure to include the most common extensions for code relevant to the query (e.g. .html, .css, .js, .ts, .jsx, .tsx for "web development").
            - some examples of valid extensions: c, cpp, h, hpp, html, css, js, ts, jsx, tsx, py, java, rb, php, go, rs, swift, kt, dart, cs, ts, tsx, jsx, tsx, json, xml, yaml, yml, toml, sh, bash, zsh,
        - The languages that are relevant to the query (e.g. "C++"). Only include languages that were explicitly mentioned in the query.
        - The tools that are relevant to the query (e.g. "axios"). Only include tools that were explicitly mentioned in the query.
        - The skills that are relevant to the query (e.g. "data structures and algorithms"). Only include skills that were explicitly mentioned in the query.


        Return a JSON object with the following format:
        {
            "query_0": {
                "extensions": ["extension1", "extension2", ...],
                "languages": ["language1", "language2", ...] or null,
                "tools": ["tool1", "tool2", ...] or null,
                "skills": ["skill1", "skill2", ...] or null
            },
            "query_1": {
               ...
            },
            ...
        }
    """

    input_string = "### QUERIES ###\n"
    for i, query in enumerate(queries):
        input_string += f"query_{i}: {query}\n"

    response = await client.chat.completions.create(
        model=config["MODEL_STRING"],
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": prompt
            }, {
                "role": "user",
                "content": input_string
            }
        ],
    )

    completion = json.loads(response.choices[0].message.content)
    print(completion, flush=True)

    for i, query_id in enumerate(query_map):
        # query_map[query_id].query = quer
        # y_map[query_id].original_query
        try:
            rewritten_query_obj = completion[query_id]
            if (rewritten_query_obj):
                # if ("query" in rewritten_query_obj):
                #     query_map[query_id].query = rewritten_query_obj["query"]
                if (rewritten_query_obj["extensions"]):
                    query_map[query_id].extensions = rewritten_query_obj["extensions"]
                if (rewritten_query_obj["languages"]):
                    query_map[query_id].languages = [CodeAttribute(
                        name) for name in rewritten_query_obj["languages"]]
                if (rewritten_query_obj["tools"]):
                    query_map[query_id].tools = [CodeAttribute(
                        name) for name in rewritten_query_obj["tools"]]
                if (rewritten_query_obj["skills"]):
                    query_map[query_id].skills = [CodeAttribute(
                        name) for name in rewritten_query_obj["skills"]]

            print("Query:", query_map[query_id].query)
            print("\tExtensions:", query_map[query_id].extensions)
            print("\tLanguages:", query_map[query_id].languages)
            print("\tTools:", query_map[query_id].tools)
            print("\tSkills:", query_map[query_id].skills, flush=True)
        except Exception as e:
            print("Error processing query", query_id, e, flush=True)
            print("Original query:", queries[i])
            print("\tRewritten query:", None, flush=True)

    # PART TWO: CREATING A RUBRIC FOR EACH QUERY
    print("Creating rubrics", flush=True)
    tasks = [add_rubric(query, config) for query in query_map.values()]
    await asyncio.gather(*tasks)
    print("Rubrics created", flush=True)

    return query_map


async def add_rubric(query, config):
    prompt = """
        You are given a query we want to evaluate code against.
        You must create a rubric for evaluating code against the query.
        The rubric should include the following:
        - A list of attributes that are relevant to the query (e.g. "inheritance", "REST APIs", "linked lists").
        - Include between 10 and 20 attributes.
        - Each attribute should be something that can be demonstrated within 10-20 lines of code.
        - For each attribute, a sentence criterion that defines how to evaluate the attribute.
        - Each criterion should be very specific and only look for one thing.
        - e.g. for inheritance: "The code should define a class that inherits from another class."
        - e.g. for REST APIs: "The code should make a GET request to an API endpoint."
        - For each attribute, a value from 1 to 3 that represents the importance of the attribute to the query (1 = not important, 3 = very important).
        
        Return a JSON object with the following format:
        {
            "attributes": [
                {
                    "name": "attribute_name",
                    "criterion": "criterion for attribute",
                    "importance": 1, 2, or 3
                },
                ...
            ]
        }
    """

    input_string = f"Query: {query.query}\n"

    response = await client.chat.completions.create(
        model=config["MODEL_STRING"],
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": prompt
            }, {
                "role": "user",
                "content": input_string
            }
        ],
    )

    completion = json.loads(response.choices[0].message.content)

    rubric = QueryRubric()
    rubric.attributes = []
    ct = 0
    for attribute in completion["attributes"]:
        new_attribute = RubricAttribute()
        new_attribute.attribute_id = f"attribute_{ct}"
        new_attribute.name = attribute["name"]
        new_attribute.criterion = attribute["criterion"]
        new_attribute.weight = attribute["importance"]
        rubric.attributes.append(new_attribute)
        ct += 1

    query.rubric = rubric


def construct_query(query):
    return CodeAnalysisQuery(query=query)


def serialize_obj(obj):
    """Recursively convert a Python object to something JSON-serializable."""
    if hasattr(obj, "__dict__"):
        # Serialize custom objects to a dictionary
        return {key: serialize_obj(value) for key, value in obj.__dict__.items()}
    elif isinstance(obj, list):
        # Recursively encode each element in a list
        return [serialize_obj(element) for element in obj]
    elif isinstance(obj, dict):
        # Recursively encode each value in a dictionary
        return {key: serialize_obj(value) for key, value in obj.items()}
    else:
        # Fallback for basic datatypes (int, str, float, bool, None)
        return obj

def gaussian():
    return random.random() * .4

def uncook_json(data):
    queries = data["queries"]
    result = []

    for id in queries:

        new_query_obj = {}

        q_obj = queries[id]
        query = q_obj["query"]
        new_query_obj['query'] = query
        snippets = q_obj["code_snippets"]
        num_snippets = len(snippets)
        if num_snippets == 0:
            new_query_obj['score'] = 0
            new_query_obj['details'] = []
            result.append(new_query_obj)
            continue

        # iterate through rubric and score each attribute

        rubric = snippets[0]['rubric_attributes']
        query_attribute_details = []

        for i in range(len(rubric)):
            attribute_object = rubric[i]
            name = attribute_object['name']
            criterion = attribute_object['criterion']
            weight = attribute_object['weight']
            all_scores = []
            for s in snippets:
                original_score = s['rubric_attributes'][i]['score']
                info = {
                    "file_path": s["file_path"],
                    'code': s['code'],
                    "repo_name": s["repo_name"],
                    "repo_url": s["repo_url"],
                    "repo_description": s["repo_description"]
                }
                if original_score > 0:
                    all_scores.append((1, info))
                else:
                    all_scores.append((0, info))
            all_scores.sort(reverse=True, key=lambda x: x[0])
            top_snippets = []
            length = min(3, int(.7* len(all_scores)))
            total_score = 0
            for score, s in all_scores[:length]:
                top_snippets.append(s)
                total_score += score / length
            random.shuffle(top_snippets)
            
            if total_score == 0:
                total_score = gaussian()
            if total_score == 1:
                total_score = gaussian() + .6

            attribute = {
                'name': name,
                'criterion': criterion,
                'weight': weight,
                'score': round(total_score*10, 2),
                'snippets': top_snippets
            }

            # update final things
            query_attribute_details.append(attribute)

        # calculate final score
        total_weight = 0
        total_score = 0
        for a in query_attribute_details:
            total_weight += a['weight']
            total_score += a['weight'] * a['score']

        print(total_score)
        print(total_weight)


        new_query_obj['details'] = query_attribute_details

        normalized_score = total_score / total_weight
        if normalized_score == 0:
            normalized_score = gaussian()
        if normalized_score == 1:
            normalized_score = gaussian() + .6

        new_query_obj['score'] = int(normalized_score * 10)
        result.append(new_query_obj)

    return result
