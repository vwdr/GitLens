from fastapi import APIRouter
from app.utils.github import *
from app.utils.analysis import *
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/testing/{username}")
async def test(url):
    print(url)
    # repos = [ 
    #          GitRepository('study-samurai', 'https://github.com/sophiasharif/study-samurai'),
    #          GitRepository('HIST5', 'https://github.com/sophiasharif/HIST5'),
    #          GitRepository('sprout', 'https://github.com/sophiasharif/sprout')]
    # # files = fetch_files(repos, "sophiasharif")
    # print("LENGTH:", len(files))
    # download_repos(repos)

    # repos = await fetch_repos("SonavAgarwal")
    # print(repos)
    # print("downloading repos...", flush=True)
    # download_repos(repos)
    # print("fetching files...")
    # fetch_files(repos, "sophiasharif")
    # for repo in repos:
    #     print("REPO ", repo.name)
    #     print("Number of files edited: ", len(repo.files))

    # delete_repos(repos)
    return JSONResponse(content={"message": "Testing endpoint reached"})




# repos = [GitRepository('HIST5', 'https://github.com/sophiasharif/HIST5'),
#          GitRepository('study-samurai', 'https://github.com/sophiasharif/study-samurai')]
# download_repos(repos)

# files = fetch_files(repos, "sophiasharif")
# print(files)


# user_repos = fetch_repos("sophiasharif")
# for repo in user_repos:
#     print("REPO ", repo.name)
#     print(repo.url)
#     print(repo.description)
#     print(repo.languages)
#     print(repo.commits)
#     print(repo.last_modified)