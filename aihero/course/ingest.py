"""Download and parse markdown from a GitHub repository zip archive."""

import io
import zipfile

import frontmatter
import requests

_DEFAULT_REFS = ("main", "master")


def read_repo_data(repo_owner: str, repo_name: str, refs: tuple[str, ...] | None = None):
    """
    Download and parse all markdown files from a GitHub repository.

    Tries each ref in order (default: main, then master) until a zip download succeeds.

    Returns:
        List of dicts: front matter fields, 'content' (body), and 'filename' (path in zip).
    """
    prefix = "https://codeload.github.com"
    refs = refs or _DEFAULT_REFS
    resp = None
    last_status = None
    for ref in refs:
        url = f"{prefix}/{repo_owner}/{repo_name}/zip/refs/heads/{ref}"
        r = requests.get(url, timeout=120)
        last_status = r.status_code
        if r.status_code == 200:
            resp = r
            break
    if resp is None:
        raise RuntimeError(
            f"Failed to download repository {repo_owner}/{repo_name}: HTTP {last_status}"
        )

    repository_data: list[dict] = []
    zf = zipfile.ZipFile(io.BytesIO(resp.content))

    for file_info in zf.infolist():
        filename = file_info.filename
        lower = filename.lower()
        if not (lower.endswith(".md") or lower.endswith(".mdx")):
            continue
        try:
            with zf.open(file_info) as f_in:
                raw = f_in.read().decode("utf-8", errors="ignore")
                post = frontmatter.loads(raw)
                data = post.to_dict()
                if "content" not in data and post.content is not None:
                    data["content"] = post.content
                data["filename"] = filename
                repository_data.append(data)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    zf.close()
    return repository_data
