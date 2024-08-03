from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.utils.analysis import *
from app.utils.github import *
from app.models.analysis_models import *
from asyncio import gather
from operator import attrgetter

import firebase_admin
from firebase_admin import credentials, firestore
from app.utils.fsa import *

# print the cwd
print("CWD", os.getcwd(), flush=True)
cred = credentials.Certificate(firebaseCreds)
firebaseapp = firebase_admin.initialize_app(cred)
firestore_client = firestore.client()


router = APIRouter()


class AnalyzeAccountRequest(BaseModel):
    username: str
    queries: List[str] = []
    criteria: List[str] = []


@router.post("/analyze_account")
async def analyze_account(background_tasks: BackgroundTasks, body: AnalyzeAccountRequest):
    username = body.username
    queries = body.queries
    criteria = body.criteria

    # create a document in firestore at /analysis-jobs/autoid
    # with an empty array called "updates"
    # field status: "pending"

    doc_ref = firestore_client.collection("analysis-jobs").document()
    doc_ref.set({
        "status": "pending",
        "updates": [],
    })

    # start the analysis in the background
    background_tasks.add_task(run_analysis, username,
                              queries, criteria, doc_ref)

    doc_id = doc_ref.id
    return doc_id


async def run_analysis_wrapper(username: str, queries: List[str], criteria: List[str], doc_ref: firebase_admin.firestore.DocumentReference):
    try:
        await run_analysis(username, queries, criteria, doc_ref)
    except Exception as e:
        print("Error in run_analysis_wrapper", e, flush=True)
        doc_ref.update({
            "status": "error",
            "updates": firebase_admin.firestore.ArrayUnion([f"Error: {e}", "Something went wrong"]),
        })


async def run_analysis(username: str, queries: List[str], criteria: List[str], doc_ref: firebase_admin.firestore.DocumentReference):

    print("Analyzing account", username, flush=True)

    add_update(doc_ref, f"Fetching repos for {username}")

    # Schedule both tasks to run in parallel
    queries_task = construct_queries(queries)
    repos_task = fetch_repos(username)
    completed_tasks = await gather(queries_task, repos_task)

    add_update(doc_ref, "Analyzing queries")

    # Unpack the results
    queries: dict[str, CodeAnalysisQuery] = completed_tasks[0]
    repos_list: list[GitRepository] = completed_tasks[1]
    for i, repo in enumerate(repos_list):
        repo.repo_id = f"repo_{i}"
    repos: dict[str, GitRepository] = {
        repo.repo_id: repo for repo in repos_list}

    # print the queries
    print("FOUND THESE QUERIES", flush=True)
    for query_id, query in queries.items():
        print("===========", flush=True)
        print(query_id, query.query, flush=True)
        for criterion in query.rubric.attributes:
            print(criterion.name, criterion.criterion,
                  criterion.weight, flush=True)

    print("Fetched repos and queries", flush=True)

    print("FOUND THIS MANY REPOS", len(repos_list), flush=True)

    for repo in repos_list:
        print("===========", flush=True)
        print(repo.name, repo.description, flush=True)

    add_update(doc_ref, "Finding most relevant repos")

    await calculate_relevance(repos, queries)

    print("Calculated relevance", flush=True)

    # TODO: PICK MORE RELEVANT REPOS BASED ON HOW MUCH YOU'VE CONTRIBUTED, ETC
    # TODO: CUT REPOS WITH VERY LITTLE CODE
    # TODO: CUT REPOS WITH NO RECENT COMMITS
    # TODO: DO THESE EARLIER
    # TODO: LOOK FOR PINNED REPOS

    MAX_REPOS_PER_QUERY = 5
    MIN_RELEVANCE = 7

    repos_to_download = set()

    add_update(doc_ref, "Downloading most relevant repos")

    for query_id, query in queries.items():
        print("===========", flush=True)
        print(query_id, query.query, flush=True)

        sorted_repos = repos_list

        # remove repos that haven't been updated in the last 3 years
        sorted_repos = [repo for repo in sorted_repos if repo.last_modified >
                        datetime.now() - timedelta(days=(365 * 3))]

        print("After removing old repos", len(sorted_repos), flush=True)
        for repo in sorted_repos:
            print(repo.name, repo.query_relevances[query_id], flush=True)
        print("\n\n", flush=True)

        sorted_repos = [
            repo for repo in sorted_repos if repo.query_relevances[query_id] > MIN_RELEVANCE]

        sorted_repos = sorted(
            sorted_repos, key=lambda r: r.query_relevances[query_id], reverse=True)

        sorted_repos = sorted_repos[:MAX_REPOS_PER_QUERY]

        for repo in sorted_repos:
            print(repo.name, repo.query_relevances[query_id], flush=True)
            query.relevant_repos[repo.repo_id] = repo

        repos_to_download.update(sorted_repos)

    repos = list(repos_to_download)
    temp = [repo.name for repo in repos_to_download]
    print("REPOS TO DOWNLOAD\n\n", temp, flush=True)

    successfully_cloned = download_repos(repos, queries, username, doc_ref)

    print("Successfully cloned", flush=True)

    # now we have all the repos and the files that may potentially be relevant

    # now, of those files, we want to find the most relevant ones
    # we will first keep only the ones that the user has contributed a lot to

    print("Fetching files", flush=True)
    fetch_files(successfully_cloned, username, doc_ref)
    print("Fetched files", flush=True)
    for repo in successfully_cloned:
        for file_path, file in repo.files.items():
            print(file_path, file.num_commits, flush=True)

    # we will send the file paths to LLM, and it will return the most relevant ones

    print("finding relevant file paths", flush=True)
    print("we have this many queries", len(queries), flush=True)
    add_update(doc_ref, "Filtering relevant files")
    await find_relevant_files(queries)
    print("found relevant file paths", flush=True)
    for query_id, query in queries.items():
        print("===========", flush=True)
        print(query_id, query.query, flush=True)
        print(query.eval_files, flush=True)

    # now we have a list of relevant files for each query
    # we will look through the chunks of code in those files and send them to LLM
    # llm will take in attributes we're looking for and score the code on said attributes
    # we will pick a few chunks of code that have the highest scores

    print("finding relevant code", flush=True)
    add_update(doc_ref, "Evaluating queries on relevant files")
    final_query_responses = await eval_queries(queries)
    response_obj = AnalyzeAccountResponse()
    response_obj.username = username
    for query_response in final_query_responses:
        response_obj.queries[query_response.query_id] = query_response

    # for each query, we'll send the best chunks to the frontend along with other metadata
    # done

    # delete repos
    add_update(doc_ref, "Preparing response")
    json_string = json.dumps(serialize_obj(response_obj), indent=4)
    print(json_string, flush=True)

    json_loaded = json.loads(json_string)

    new_json = uncook_json(json_loaded)

    doc_ref.update({
        "status": "complete",
        # append the "Done" message to the "updates" array
        "updates": firebase_admin.firestore.ArrayUnion(["Done analyzing!"]),
        "data": new_json,
    })

    delete_repos(successfully_cloned, username)

    # return

    # eval_repos = list(repos_to_download)

    # download_repos(eval_repos)

    # for query_id, query in queries.items():
    #     print("===========", flush=True)
    #     print(query_id, query.query, flush=True)

    # return new_json
    # return repo_and_scores
