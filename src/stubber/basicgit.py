"""
simple Git module, where needed via powershell
"""
from typing import Union
import subprocess
import os
from pathlib import Path
from typing import Union, List, Optional


def _run_git(
    cmd: List[str],
    repo: Optional[str] = None,
    expect_stderr=False,
    capture_output=True,
):
    "run a external (git) command in the repo's folder and deal with some of the errors"
    try:
        if repo:
            repo = repo.replace("\\", "/")
            result = subprocess.run(cmd, capture_output=capture_output, check=True, cwd=os.path.abspath(repo))
        else:
            result = subprocess.run(cmd, capture_output=capture_output, check=True)
    except subprocess.CalledProcessError as e:
        # add some logging for github actions
        print("Exception on process, rc=", e.returncode, "output=", e.output)
        return None
    if result.stderr != b"":
        if not expect_stderr:
            raise Exception(result.stderr.decode("utf-8"))
        if capture_output:
            print(result.stderr.decode("utf-8"))

    if result.returncode < 0:
        raise Exception(result.stderr.decode("utf-8"))
    return result


def clone(remote_repo: str, path: Path, shallow=False) -> bool:
    "git clone --depth 0 <remote> <directory>"
    cmd = ["git", "clone"]
    if shallow:
        cmd += ["--depth", "1"]
    cmd += [remote_repo, str(path)]
    result = _run_git(cmd, expect_stderr=True, capture_output=False)
    if result:
        return result.returncode == 0
    else:
        return False


def get_tag(repo: Optional[str] = None, abbreviate: bool = True) -> Union[str, None]:
    """
    get the most recent git version tag of a local repo
    repo should be in the form of : repo = "./micropython"

    returns the tag or None
    """
    if not repo:
        repo = "."
    repo = repo.replace("\\", "/")

    result = _run_git(["git", "describe"], repo=repo, expect_stderr=True)
    if not result:
        return None
    tag: str = result.stdout.decode("utf-8")
    tag = tag.replace("\r", "").replace("\n", "")
    if abbreviate and "-" in tag:
        # this may or not be the latest on the main branch
        # result = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo=repo, expect_stderr=True)
        result = _run_git(["git", "status", "--branch"], repo=repo, expect_stderr=True)
        if result:
            lines = result.stdout.decode("utf-8").replace("\r", "").split("\n")
            if lines[0].startswith("On branch"):
                if lines[0].endswith("master"):
                    tag = "latest"
                elif lines[0].endswith("fix_lib_documentation"):
                    tag = "fix_lib_documentation"
    return tag


def checkout_tag(tag: str, repo: Optional[str] = None) -> bool:
    """
    checkout a specific git tag
    """
    cmd = ["git", "checkout", "tags/" + tag, "--quiet", "--force"]
    result = _run_git(cmd, repo=repo, expect_stderr=True)
    if not result:
        return False
    # actually a good result
    print(result.stderr.decode("utf-8"))
    return True


def checkout_commit(commit_hash: str, repo: Optional[str] = None) -> bool:
    """
    Checkout a specific commit
    """
    cmd = ["git", "checkout", commit_hash, "--quiet", "--force"]
    result = _run_git(cmd, repo=repo, expect_stderr=True)
    if not result:
        return False
    # actually a good result
    print(result.stderr.decode("utf-8"))
    return True


def switch_tag(tag: str, repo: Optional[str] = None) -> bool:
    """
    get the most recent git version tag of a local repo"
    repo should be in the form of : path/.git
    repo = '../micropython/.git'
    returns the tag or None
    """
    cmd = ["git", "switch", "--detach", tag, "--quiet", "--force"]
    result = _run_git(cmd, repo=repo, expect_stderr=True)
    if not result:
        return False
    # actually a good result
    print(result.stderr.decode("utf-8"))
    return True


def switch_branch(branch: str, repo: Optional[str] = None) -> bool:
    """
    get the most recent git version tag of a local repo"
    repo should be in the form of : path/.git
    repo = '../micropython/.git'
    returns the tag or None
    """
    cmd = ["git", "switch", branch, "--quiet", "--force"]
    result = _run_git(cmd, repo=repo, expect_stderr=True)
    if not result:
        return False
    # actually a good result
    print(result.stderr.decode("utf-8"))
    return True


def fetch(repo: str) -> bool:
    """
    fetches a repo
    repo should be in the form of : path/.git
    repo = '../micropython/.git'
    returns True on success
    """
    if not repo:
        raise NotADirectoryError
    repo = repo.replace("\\", "/")
    cmd = ["git", "fetch origin"]
    result = _run_git(cmd, repo=repo)
    if not result:
        return False
    return result.returncode == 0


def pull(repo: str, branch="main") -> bool:
    """
    pull a repo origin into main
    repo should be in the form of : path/.git
    repo = '../micropython/.git'
    returns True on success
    """
    if not repo:
        raise NotADirectoryError
    repo = repo.replace("\\", "/")
    # first checkout HEAD
    cmd = ["git", "checkout", "main", "--quiet", "--force"]
    result = _run_git(cmd, repo=repo, expect_stderr=True)
    if not result:
        print("error during git checkout main", result)
        return False

    cmd = ["git", "pull", "origin", branch, "--quiet"]
    result = _run_git(cmd, repo=repo, expect_stderr=True)
    if not result:
        print("error durign pull", result)
        return False
    return result.returncode == 0
