'''
fetch_repos(user_username: str) -> list[GitRepository]
    return a list of GitRepository objects for the user

download_repos(repos: list[GitRepository], size_limit_mb: int = 100)
    download the repos to the server

fetch_files(repos: list[GitRepository], username: str) -> list[GitFile]
    return a list of GitFile objects for the user's repos
    GitFile objects contain number of commits and relevant code chunks

delete_repos(repos: list[GitRepository])
    delete the repos from the server
'''

import re
import shutil
import subprocess
import os
import aiohttp
from app.models.git_models import *
from app.models.analysis_models import *
from datetime import datetime
import requests
import firebase_admin

together_key = os.getenv("TOGETHER_KEY")


def add_update(doc_ref, update: str):
    doc_ref.update({
        "updates": firebase_admin.firestore.ArrayUnion([update])
    })


def create_repository_objects(query_outputs, user_username):
    repositories = []
    for repo_data in query_outputs:
        try:
            repo = GitRepository(repo_data['name'], repo_data['url'])
            # print(query_outputs)
            repo.description = repo_data['description'] if repo_data['description'] else None
            repo.languages = [lang['node']['name']
                              for lang in repo_data['languages']['edges']]
            repo.commits = []
            for commit in repo_data['defaultBranchRef']['target']['history']['edges']:
                if user_username not in commit['node']['author']['user']['login']:
                    continue
                sha = commit['node']['oid']
                message = commit['node']['message']
                date = commit['node']['committedDate']
                date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
                repo.commits.append(GitCommit(sha, message, date_obj))
            if not repo.commits:
                continue
            repo.last_modified = repo.commits[0].date
            repositories.append(repo)
        except Exception as e:
            print(f"Error creating repository {repo_data['name']} object: {e}")
    return repositories


# def get_github_user_id(username):
#     """Fetch GitHub user ID based on username."""
#     url = f"https://api.github.com/users/{username}"
#     headers = {'Accept': 'application/vnd.github.v3+json'}

#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()  # Raises an HTTPError if the status is 4XX or 5XX
#         user_data = response.json()
#         return user_data.get('id')
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching user data: {e}")
#         return None


async def fetch_repos(user_username):

    url = 'https://api.github.com/graphql'
    access_token = os.getenv("GITHUB_TOKEN")
    query = """
    {
      user(login: "%s") {
        repositories(first: 100) {
          nodes {
            name
            url
            description
            languages(first: 10) {
              edges {
                node {
                  name
                }
                size
              }
            }
            defaultBranchRef {
              name
              target {
                ... on Commit {
                  history(first: 100) {
                    pageInfo {
                      endCursor
                      hasNextPage
                    }
                    edges {
                      node {
                        oid
                        message
                        committedDate
                        author {
                          user {
                            login
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % (user_username)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json={'query': query}) as response:
            if response.status == 200:
                data = await response.json()
                repositories = data['data']['user']['repositories']['nodes']
                repos = create_repository_objects(repositories, user_username)
                return repos
            else:
                print('Failed to fetch repositories:', await response.text())
                return None


def download_repos(repos: list[GitRepository], queries: dict[str, CodeAnalysisQuery], username, doc_ref):

    os.chdir('/usr/src/app')  # Ensure we're in the right directory

    print("A", flush=True)
    clone_dir = f"/usr/cloned_repos/{username}_repos"
    print("B", flush=True)
    if not os.path.exists(clone_dir):
        os.makedirs(clone_dir)
        pass
    print("C", flush=True)

    # empty /usr/cloned_repos/username_repos
    subprocess.run(f"rm -rf {clone_dir}/*", shell=True)

    print("F", flush=True)

    successfull_clones = []

    for repo in repos:
        print("G", flush=True)
        user = repo.url.split('/')[-2]
        repo_path = os.path.join(clone_dir, user, repo.name)

        original_cwd = os.getcwd()  # Save the original working directory

        try:

            add_update(doc_ref, f"Cloning {repo.name}")

            # STEP 1: CLONE THE REPO
            clone_command = " ".join([
                "git clone",
                "--no-checkout",  # Don't checkout the files
                repo.url,
                repo_path
            ])

            subpro = subprocess.run(clone_command, check=True, shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if subpro.returncode != 0:
                print(f"Failed to clone {repo.name}", flush=True)
                continue
            else:
                print(f"Cloned {repo.name} successfully", flush=True)
                successfull_clones.append(repo)

            # save the local repo path to the repo object
            repo.local_path = repo_path

            # STEP 2: CHECKOUT THE RELEVANT FILES
            os.chdir(repo_path)  # Change working directory to the repo's path
            sparse_checkout_command = "git config core.sparseCheckout true"
            subprocess.run(sparse_checkout_command, check=True, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            file_extensions = set()
            tool_names = set()
            for query_id, query in queries.items():
                if repo.repo_id in query.relevant_repos:
                    file_extensions.update(query.extensions)
                    tool_names.update(query.tools)

            # Create the sparse-checkout file
            with open(".git/info/sparse-checkout", "w") as f:
                f.write("!node_modules/\n")  # Exclude node_modules directory
                for ext in file_extensions:
                    if (ext.startswith(".")):
                        f.write(f"*{ext}\n")
                    else:
                        f.write(f"*.{ext}\n")
                for tool in tool_names:
                    f.write(f"*{tool}*\n")

            # Run the checkout command
            checkout_command = "git read-tree -mu HEAD"
            subprocess.run(checkout_command, check=True, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {repo.name}: {e}", flush=True)

        os.chdir(original_cwd)  # Change back to the original working directory

    # run ls recursively to show the cloned repos
    ls_command = f"ls -R {clone_dir}"
    output = subprocess.run(ls_command, check=True, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(output.stdout.decode(), flush=True)

    return successfull_clones

    # for repo in repos:
    #     user = repo.url.split('/')[-2]
    #     repo_path = os.path.join(clone_dir, user, repo.name)

    #     # Delete the repo directory if it already exists
    #     if os.path.exists(repo_path):
    #         print(f"{repo.name} already exists.")
    #         continue

    #     github_token = os.getenv("GITHUB_TOKEN")
    #     if github_token:
    #         # Assuming the repo.url is in the format "https://github.com/user/repo"
    #         auth_url = repo.url.replace(
    #             "https://", f"https://x-access-token:{github_token}@")
    #     else:
    #         auth_url = repo.url  # Proceed without token if it's not available

    #     clone_command = f"git clone {auth_url} {repo_path}"

    #     try:
    #         subprocess.run(clone_command, check=True, shell=True,
    #                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    #         # Check the size of the cloned repo
    #         total_size = sum(os.path.getsize(os.path.join(dirpath, filename))
    #                          for dirpath, dirnames, filenames in os.walk(repo_path) for filename in filenames)
    #         total_size_mb = total_size / (1024 * 1024)  # Convert bytes to MB

    #         if total_size_mb > size_limit_mb:
    #             print(repo.name, "exceeds the size limit of", size_limit_mb,
    #                   "MB. Deleting the cloned repo...")
    #             shutil.rmtree(repo_path)
    #         else:
    #             print(f"Cloned {repo.name} successfully")

    #     except subprocess.CalledProcessError as e:
    #         print(f"Failed to clone {repo.name}: {e}")


def process_grep_output(output: str):
    pattern = re.compile(r'\S+ \(\S+ \S+ \S+ \S+ (\d+)\) (.*)')
    lines_written = []

    for line in output.strip().split('\n'):
        match = pattern.match(line)
        if match:
            line_number, code_line = match.groups()
            lines_written.append((int(line_number), code_line))

    code_chunks = []
    for i in range(len(lines_written)):
        if i == 0 or lines_written[i][0] != lines_written[i-1][0] + 1:
            code_chunks.append(lines_written[i][1])
        else:
            code_chunks[-1] += '\n' + lines_written[i][1]
    return code_chunks


def fetch_files(repos: list[GitRepository], username: str, doc_ref):
    clone_dir = f"/usr/cloned_repos/{username}_repos"
    res = []

    for repo in repos:
        add_update(doc_ref, f"Fetching files from {repo.name}")

        user = repo.url.split('/')[-2]
        repo_path = os.path.join(clone_dir, user, repo.name)
        os.chdir(repo_path)  # Change working directory to the repo's path

        git_command = f'git log --author="{username}" --pretty="" ' + \
            '--name-only | sort | uniq -c | sort -rn'

        files_contributed = []  # To store tuples of (file, num_occurrences)

        # Execute the command with subprocess.run
        result = subprocess.run(git_command, shell=True,
                                text=True, capture_output=True)
        if result.returncode == 0:
            output = result.stdout
            # Parsing the output
            for line in output.strip().split('\n'):
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    num_occurrences, file_name = int(parts[0]), parts[1]
                    new_file = GitFile(file_name, num_occurrences)
                    new_file.repo = repo
                    files_contributed.append(new_file)
        else:
            print(f"Error executing git command: {result.stderr}")
            continue  # Skip this repo and continue with the next

        # final_files = []
        for file in files_contributed:
            blame_command = f'git blame {file.path} | grep "{username}"'
            blame_result = subprocess.run(
                blame_command, shell=True, text=True, capture_output=True)
            if blame_result.returncode == 0:
                code_chunks = process_grep_output(blame_result.stdout)
                file.relevant_code = code_chunks
                repo.files[file.path] = file
            else:
                continue
                # file must have been deleted or renamed

        # repo.files = final_files

    os.chdir('/usr/src/app')  # Change back to the original working directory


def delete_repos(repos: list[GitRepository], username=None):
    clone_dir = f"/usr/cloned_repos/{username}_repos"
    for repo in repos:
        user = repo.url.split('/')[-2]
        repo_path = os.path.join(clone_dir, user, repo.name)
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            print(f"Deleted {repo.name}")
        else:
            print(f"attempted to delete {repo.name} but it does not exist")
