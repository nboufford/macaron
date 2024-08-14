# Copyright (c) 2024 - 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

"""This module contains methods for extracting repository and commit metadata from provenance files."""
import logging
import urllib.parse

from packageurl import PackageURL
from pydriller import Git

from macaron.errors import ProvenanceError
from macaron.json_tools import JsonType, json_extract
from macaron.repo_finder.commit_finder import (
    AbstractPurlType,
    determine_abstract_purl_type,
    extract_commit_from_version,
)
from macaron.repo_finder.repo_finder import to_domain_from_known_purl_types
from macaron.slsa_analyzer.provenance.intoto import InTotoPayload, InTotoV1Payload, InTotoV01Payload

logger: logging.Logger = logging.getLogger(__name__)


SLSA_V01_DIGEST_SET_GIT_ALGORITHMS = ["sha1"]
SLSA_V02_DIGEST_SET_GIT_ALGORITHMS = ["sha1"]
SLSA_V1_DIGEST_SET_GIT_ALGORITHMS = ["sha1", "gitCommit"]


def extract_repo_and_commit_from_provenance(payload: InTotoPayload) -> tuple[str | None, str | None]:
    """Extract the repository and commit metadata from the passed provenance payload.

    Parameters
    ----------
    payload: InTotoPayload
        The payload to extract from.

    Returns
    -------
    tuple[str, str]
        The repository URL and commit hash if found, a pair of empty strings otherwise.

    Raises
    ------
    ProvenanceError
        If the extraction process fails for any reason.
    """
    predicate_type = payload.statement.get("predicateType")
    if isinstance(payload, InTotoV1Payload):
        if predicate_type == "https://slsa.dev/provenance/v1":
            return _extract_from_slsa_v1(payload)
    elif isinstance(payload, InTotoV01Payload):
        if predicate_type == "https://slsa.dev/provenance/v0.2":
            return _extract_from_slsa_v02(payload)
        if predicate_type == "https://slsa.dev/provenance/v0.1":
            return _extract_from_slsa_v01(payload)
        if predicate_type == "https://witness.testifysec.com/attestation-collection/v0.1":
            return _extract_from_witness_provenance(payload)

    msg = (
        f"Extraction from provenance not supported for versions: "
        f"predicate_type {predicate_type}, in-toto {str(type(payload))}."
    )
    logger.debug(msg)
    raise ProvenanceError(msg)


def _extract_from_slsa_v01(payload: InTotoV01Payload) -> tuple[str | None, str | None]:
    """Extract the repository and commit metadata from the slsa v01 provenance payload."""
    predicate: dict[str, JsonType] | None = payload.statement.get("predicate")
    if not predicate:
        return None, None

    # The repository URL and commit are stored inside an entry in the list of predicate -> materials.
    # In predicate -> recipe -> definedInMaterial we find the list index that points to the correct entry.
    list_index = json_extract(predicate, ["recipe", "definedInMaterial"], int)
    if not list_index:
        return None, None

    material = json_extract(predicate, ["materials", list_index], dict)
    if not material:
        logger.debug("Indexed material list entry is invalid.")
        return None, None

    repo = None
    uri = json_extract(material, ["uri"], str)
    if uri:
        repo = _clean_spdx(uri)

    digest_set = json_extract(material, ["digest"], dict)
    if not digest_set:
        return repo, None
    commit = _extract_commit_from_digest_set(digest_set, SLSA_V01_DIGEST_SET_GIT_ALGORITHMS)

    return repo, commit or None


def _extract_from_slsa_v02(payload: InTotoV01Payload) -> tuple[str | None, str | None]:
    """Extract the repository and commit metadata from the slsa v02 provenance payload."""
    predicate: dict[str, JsonType] | None = payload.statement.get("predicate")
    if not predicate:
        logger.debug("No predicate in payload statement.")
        return None, None

    # The repository URL and commit are stored within the predicate -> invocation -> configSource object.
    # See https://slsa.dev/spec/v0.2/provenance
    repo = None
    uri = json_extract(predicate, ["invocation", "configSource", "uri"], str)
    if uri:
        repo = _clean_spdx(uri)

    digest_set = json_extract(predicate, ["invocation", "configSource", "digest"], dict)
    if not digest_set:
        return repo, None
    commit = _extract_commit_from_digest_set(digest_set, SLSA_V02_DIGEST_SET_GIT_ALGORITHMS)

    return repo, commit or None


def _extract_from_slsa_v1(payload: InTotoV1Payload) -> tuple[str | None, str | None]:
    """Extract the repository and commit metadata from the slsa v1 provenance payload."""
    predicate: dict[str, JsonType] | None = payload.statement.get("predicate")
    if not predicate:
        logger.debug("No predicate in payload statement.")
        return None, None

    build_def = json_extract(predicate, ["buildDefinition"], dict)
    if not build_def:
        return None, None

    build_type = json_extract(build_def, ["buildType"], str)
    if not build_type:
        return None, None

    # Extract the repository URL.
    match build_type:
        case "https://slsa-framework.github.io/gcb-buildtypes/triggered-build/v1":
            repo = json_extract(build_def, ["externalParameters", "sourceToBuild", "repository"], str)
            if not repo:
                repo = json_extract(build_def, ["externalParameters", "configSource", "repository"], str)
        case "https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1":
            repo = json_extract(build_def, ["externalParameters", "workflow", "repository"], str)
        case "https://github.com/oracle/macaron/tree/main/src/macaron/resources/provenance-buildtypes/oci/v1":
            repo = json_extract(build_def, ["externalParameters", "source"], str)
        case _:
            logger.debug("Unsupported build type for SLSA v1: %s", build_type)
            return None, None

    if not repo:
        logger.debug("Repo URL not found in SLSA v1 payload.")
        return None, None

    # Extract the commit hash.
    commit = None
    if build_type == "https://github.com/oracle/macaron/tree/main/src/macaron/resources/provenance-buildtypes/oci/v1":
        commit = json_extract(build_def, ["internalParameters", "buildEnvVar", "BLD_COMMIT_HASH"], str)
    else:
        deps = json_extract(build_def, ["resolvedDependencies"], list)
        if not deps:
            return repo, None
        for dep in deps:
            if not isinstance(dep, dict):
                continue
            uri = json_extract(dep, ["uri"], str)
            if not uri:
                continue
            url = _clean_spdx(uri)
            if url != repo:
                continue
            digest_set = json_extract(dep, ["digest"], dict)
            if not digest_set:
                continue
            commit = _extract_commit_from_digest_set(digest_set, SLSA_V1_DIGEST_SET_GIT_ALGORITHMS)

    return repo, commit or None


def _extract_from_witness_provenance(payload: InTotoV01Payload) -> tuple[str | None, str | None]:
    """Extract the repository and commit metadata from the witness provenance file found at the passed path.

    To successfully return the commit and repository URL, the payload must respectively contain a Git attestation, and
    either a GitHub or GitLab attestation.

    Parameters
    ----------
    payload: InTotoPayload
        The payload to extract from.

    Returns
    -------
    tuple[str, str]
        The repository URL and commit hash if found, a pair of empty strings otherwise.
    """
    predicate: dict[str, JsonType] | None = payload.statement.get("predicate")
    if not predicate:
        logger.debug("No predicate in payload statement.")
        return None, None

    attestations = json_extract(predicate, ["attestations"], list)
    if not attestations:
        return None, None

    repo = None
    commit = None
    for entry in attestations:
        if not isinstance(entry, dict):
            continue
        entry_type = entry.get("type")
        if not entry_type:
            continue
        if entry_type.startswith("https://witness.dev/attestations/git/"):
            commit = json_extract(entry, ["attestation", "commithash"], str)
        elif entry_type.startswith("https://witness.dev/attestations/gitlab/") or entry_type.startswith(
            "https://witness.dev/attestations/github/"
        ):
            repo = json_extract(entry, ["attestation", "projecturl"], str)

    return repo or None, commit or None


def _extract_commit_from_digest_set(digest_set: dict[str, JsonType], valid_algorithms: list[str]) -> str:
    """Extract the commit from the passed DigestSet.

    The DigestSet is an in-toto object that maps algorithm types to commit hashes (digests).
    """
    if len(digest_set.keys()) > 1:
        logger.debug("DigestSet contains multiple algorithms: %s", digest_set.keys())

    for key in digest_set:
        if key in valid_algorithms:
            value = digest_set.get(key)
            if isinstance(value, str):
                return value
    logger.debug("No valid digest in digest set: %s not in %s", digest_set.keys(), valid_algorithms)
    return ""


def _clean_spdx(uri: str) -> str:
    """Clean the passed SPDX URI and return the normalised URL it represents.

    A SPDX URI has the form: git+https://example.com@refs/heads/main
    """
    url, _, _ = uri.lstrip("git+").rpartition("@")
    return url


def check_if_input_repo_provenance_conflict(
    repo_path_input: str | None,
    provenance_repo_url: str | None,
) -> bool:
    """Test if the input repo and commit match the contents of the provenance.

    Parameters
    ----------
    repo_path_input: str | None
        The repo URL from input.
    provenance_repo_url: str | None
        The repo URL from provenance.

    Returns
    -------
    bool
        True if there is a conflict between the inputs, False otherwise, or if the comparison cannot be performed.
    """
    # Check the provenance repo against the input repo.
    if repo_path_input and provenance_repo_url and repo_path_input != provenance_repo_url:
        logger.debug(
            "The repository URL from input does not match what exists in the provenance. "
            "Input Repo: %s, Provenance Repo: %s.",
            repo_path_input,
            provenance_repo_url,
        )
        return True

    return False


def check_if_input_purl_provenance_conflict(
    git_obj: Git,
    repo_path_input: bool,
    digest_input: bool,
    provenance_repo_url: str | None,
    provenance_commit_digest: str | None,
    purl: PackageURL,
) -> bool:
    """Test if the input repository type PURL's repo and commit match the contents of the provenance.

    Parameters
    ----------
    git_obj: Git
        The Git object.
    repo_path_input: bool
        True if there is a repo as input.
    digest_input: str
        True if there is a commit as input.
    provenance_repo_url: str | None
        The repo url from provenance.
    provenance_commit_digest: str | None
        The commit digest from provenance.
    purl: PackageURL
        The input repository PURL.

    Returns
    -------
    bool
        True if there is a conflict between the inputs, False otherwise, or if the comparison cannot be performed.
    """
    if determine_abstract_purl_type(purl) != AbstractPurlType.REPOSITORY:
        return False

    # Check the PURL repo against the provenance.
    if not repo_path_input and provenance_repo_url:
        if not check_if_repository_purl_and_url_match(provenance_repo_url, purl):
            logger.debug(
                "The repo url passed via purl input does not match what exists in the provenance. "
                "Purl: %s, Provenance: %s.",
                purl,
                provenance_repo_url,
            )
            return True

    # Check the PURL commit against the provenance.
    if not digest_input and provenance_commit_digest and purl.version:
        purl_commit = extract_commit_from_version(git_obj, purl.version)
        if purl_commit and purl_commit != provenance_commit_digest:
            logger.debug(
                "The commit digest passed via purl input does not match what exists in the "
                "provenance. Purl Commit: %s, Provenance Commit: %s.",
                purl_commit,
                provenance_commit_digest,
            )
            return True

    return False


def check_if_repository_purl_and_url_match(url: str, repo_purl: PackageURL) -> bool:
    """Compare a repository PURL and URL for equality.

    Parameters
    ----------
    url: str
        The URL.
    repo_purl: PackageURL
        A PURL that is of the repository abstract type. E.g. GitHub.

    Returns
    -------
    bool
        True if the two inputs match in terms of URL netloc/domain and path.
    """
    expanded_purl_type = to_domain_from_known_purl_types(repo_purl.type)
    parsed_url = urllib.parse.urlparse(url)
    purl_path = repo_purl.name
    if repo_purl.namespace:
        purl_path = f"{repo_purl.namespace}/{purl_path}"
    # Note that the urllib method includes the "/" before path while the PURL method does not.
    return f"{parsed_url.hostname}{parsed_url.path}".lower() == f"{expanded_purl_type or repo_purl.type}/{purl_path}"
