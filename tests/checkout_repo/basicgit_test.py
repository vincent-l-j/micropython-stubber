import sys
import os
import pytest
import subprocess
from pathlib import Path
from pytest_mock import MockerFixture
from mock import MagicMock
from typing import List
from subprocess import CompletedProcess

# make sure that the source can be found
RootPath = Path(os.getcwd())
src_path = str(RootPath / "src")
if not src_path in sys.path:
    sys.path.append(src_path)

# pylint: disable=wrong-import-position,import-error
# Module Under Test
import stubber.basicgit as git


def common_tst(tag):
    # print(tag)
    assert isinstance(tag, str), "tag must be a string"
    if tag != "latest":
        assert tag.startswith("v"), "tags start with a v"
        assert len(tag) >= 2, "tags are longer than 2 chars"


def test_git_clone_shallow(tmp_path):
    result = git.clone("https://github.com/micropython/micropython.git", tmp_path / "micropython")
    assert result == True


def test_git_clone(tmp_path):
    result = git.clone("https://github.com/micropython/micropython.git", tmp_path / "micropython", shallow=False)
    assert result == True


def test_git_clone_fast(mocker: MockerFixture, tmp_path):

    result = CompletedProcess(
        args=[
            "git",
            "clone",
            "https://github.com/micropython/micropython.git",
            "C:\\\\Users\\\\josverl\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-josverl\\\\pytest-225\\\\test_git_clone0\\\\micropython",
        ],
        returncode=0,
    )

    mock: MagicMock = mocker.MagicMock(return_value=result)
    mocker.patch("stubber.basicgit.subprocess.run", mock)

    result = git.clone("https://github.com/micropython/micropython.git", tmp_path / "micropython", shallow=False)
    assert result == True


@pytest.mark.basicgit
# @pytest.mark.skip(reason="test discards uncomitted changes in top repo")
def test_get_tag_current():
    if not os.path.exists(".git"):
        pytest.skip("no git repo in current folder")
    else:
        # get tag of current repro
        tag = git.get_tag()
        common_tst(tag)


@pytest.mark.basicgit
def test_get_tag_latest():
    repo = Path("./micropython")
    if not (repo / ".git").exists():
        pytest.skip("no git repo in current folder")

    result = subprocess.run(["git", "switch", "main", "--force"], capture_output=True, check=True, cwd=repo.as_posix())

    assert result.stderr == 0
    # get tag of current repro
    tag = git.get_tag("./micropython")
    assert tag == "latest"


@pytest.mark.basicgit
def test_get_failure_throws():
    with pytest.raises(Exception):
        git.get_tag(".not")


@pytest.mark.basicgit
@pytest.mark.skip(reason="test discards uncomitted changes in top repo")
def test_pull_main(testrepo_micropython):
    "test and force update to most recent"
    repo_path = testrepo_micropython
    x = git.pull(repo_path, "main")
    # Should succeed.
    assert x


@pytest.mark.basicgit
def test_get_tag_submodule(testrepo_micropython: Path):
    # get version of submodule repro
    for testcase in [
        testrepo_micropython.as_posix(),
        str(testrepo_micropython),
        ".\\micropython",
    ]:
        tag = git.get_tag(testcase)
        common_tst(tag)


@pytest.mark.basicgit
@pytest.mark.skip(reason="test discards uncomitted changes in top repo")
def test_checkout_sibling(testrepo_micropython):
    repo_path = testrepo_micropython
    x = git.get_tag(repo_path)
    assert x

    for ver in ["v1.11", "v1.9.4", "v1.12"]:
        git.checkout_tag(ver, repo=repo_path)
        assert git.get_tag(repo_path) == ver

    git.checkout_tag(x, repo=repo_path)
    assert git.get_tag(repo_path) == x, "can restore to prior version"


def test_fetch():
    with pytest.raises(NotADirectoryError):
        git.fetch(repo=None)  # type: ignore

    git.fetch(repo=".")


def test_run_git_fails(mocker: MockerFixture):
    "test what happens if _run_git fails"

    def mock_run_git_1(cmd: List[str], repo=None, expect_stderr=False):
        return None

    mocker.patch("stubber.basicgit._run_git", mock_run_git_1)

    # fail to fetch
    r = git.fetch(repo=".")
    assert r == False

    # fail to get tag
    r = git.get_tag()
    assert r == None

    # fail to checkout tag
    r = git.checkout_tag("v1.10")
    assert r == False

    # fail to checkout commit
    r = git.checkout_commit(commit_hash="123")
    assert r == False

    # fail to switch tag
    r = git.switch_tag(tag="v1.10")
    assert r == False

    # fail to switch branch
    r = git.switch_branch(branch="foobar")
    assert r == False
