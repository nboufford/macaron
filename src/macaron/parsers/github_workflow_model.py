# Copyright (c) 2024 - 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.
# pylint: skip-file
# flake8: noqa


# generated by datamodel-codegen:
#   filename:  https://raw.githubusercontent.com/SchemaStore/schemastore/a1689388470d1997f2e5ebd8b430e99587b8d354/src/schemas/json/github-workflow.json
#   timestamp: 2024-05-10T03:46:22+00:00
# Some manual modifications made, noted as MODIFIED in comments below

from __future__ import annotations

from typing import Any, Literal, NotRequired, Optional, TypedDict, Union


class Inputs(TypedDict):
    description: NotRequired[str]
    deprecationMessage: NotRequired[str]
    required: NotRequired[bool]
    type: Literal["boolean", "number", "string"]
    default: NotRequired[bool | float | str]


class Secrets(TypedDict):
    description: NotRequired[str]
    required: bool


class WorkflowCall(TypedDict):
    inputs: NotRequired[dict[str, Inputs]]
    secrets: NotRequired[dict[str, Secrets]]


class Inputs1(TypedDict):
    description: str
    deprecationMessage: NotRequired[str]
    required: NotRequired[bool]
    default: NotRequired[Any]
    type: NotRequired[Literal["string", "choice", "boolean", "number", "environment"]]
    options: NotRequired[list[str]]


class WorkflowDispatch(TypedDict):
    inputs: NotRequired[dict[str, Inputs1]]


class ScheduleItem(TypedDict):
    cron: NotRequired[str]


Architecture = Literal["ARM32", "x64", "x86"]

# MODIFIED: quoted "Configuration" to fix circular reference
Configuration = Union[str, float, bool, dict[str, "Configuration"], list["Configuration"]]
# END MODIFIED


class Credentials(TypedDict):
    username: NotRequired[str]
    password: NotRequired[str]


Volume = str


PermissionsLevel = Literal["read", "write", "none"]


class Environment(TypedDict):
    name: str
    url: NotRequired[str]


Event = Literal[
    "branch_protection_rule",
    "check_run",
    "check_suite",
    "create",
    "delete",
    "deployment",
    "deployment_status",
    "discussion",
    "discussion_comment",
    "fork",
    "gollum",
    "issue_comment",
    "issues",
    "label",
    "merge_group",
    "milestone",
    "page_build",
    "project",
    "project_card",
    "project_column",
    "public",
    "pull_request",
    "pull_request_review",
    "pull_request_review_comment",
    "pull_request_target",
    "push",
    "registry_package",
    "release",
    "status",
    "watch",
    "workflow_call",
    "workflow_dispatch",
    "workflow_run",
    "repository_dispatch",
]


EventObject = Optional[dict[str, Any]]


ExpressionSyntax = str


StringContainingExpressionSyntax = str


Glob = str


Globs = list[Glob]


Machine = Literal["linux", "macos", "windows"]


Name = str


Path = Globs


Shell = Union[str, Literal["bash", "pwsh", "python", "sh", "cmd", "powershell"]]


Types = list


WorkingDirectory = str


JobNeeds = Union[list[Name], Name]


Matrix = Union[
    # MODIFIED: was
    #   dict[str, Union[ExpressionSyntax, list[dict[str, Configuration]]]], ExpressionSyntax
    #   which appears to be incorrect, seems it should be "Configuration" rather than "dict[str, Configuration]"
    #   appears to be a datamodel-codegen issue, because workflow files that pass jsonschema validation end up with
    #   a matrix value incompatible with the above type
    dict[str, Union[ExpressionSyntax, list[Configuration]]],
    ExpressionSyntax,
    # END MODIFIED
]


Strategy = TypedDict(
    "Strategy",
    {
        "matrix": Matrix,
        "fail-fast": NotRequired[Union[bool, str]],
        "max-parallel": NotRequired[Union[float, str]],
    },
)


class RunsOn(TypedDict):
    group: NotRequired[str]
    labels: NotRequired[str | list[str]]


class Step1(TypedDict):
    uses: str


class Step2(TypedDict):
    run: str


Branch = Globs


Concurrency = TypedDict(
    "Concurrency",
    {
        "group": str,
        "cancel-in-progress": NotRequired[Union[bool, ExpressionSyntax]],
    },
)


Run = TypedDict(
    "Run",
    {
        "shell": NotRequired[Shell],
        "working-directory": NotRequired[WorkingDirectory],
    },
)


class Defaults(TypedDict):
    run: NotRequired[Run]


PermissionsEvent = TypedDict(
    "PermissionsEvent",
    {
        "actions": NotRequired[PermissionsLevel],
        "attestations": NotRequired[PermissionsLevel],
        "checks": NotRequired[PermissionsLevel],
        "contents": NotRequired[PermissionsLevel],
        "deployments": NotRequired[PermissionsLevel],
        "discussions": NotRequired[PermissionsLevel],
        "id-token": NotRequired[PermissionsLevel],
        "issues": NotRequired[PermissionsLevel],
        "packages": NotRequired[PermissionsLevel],
        "pages": NotRequired[PermissionsLevel],
        "pull-requests": NotRequired[PermissionsLevel],
        "repository-projects": NotRequired[PermissionsLevel],
        "security-events": NotRequired[PermissionsLevel],
        "statuses": NotRequired[PermissionsLevel],
    },
)


Env = Union[dict[str, Union[str, float, bool]], StringContainingExpressionSyntax]


Ref1 = TypedDict(
    "Ref1",
    {
        "branches": NotRequired[Branch],
        "branches-ignore": NotRequired[Branch],
        "tags": NotRequired[Branch],
        "tags-ignore": NotRequired[Branch],
        "paths": NotRequired[Path],
        "paths-ignore": NotRequired[Path],
    },
)


Ref = Ref1


Step3 = TypedDict(
    "Step3",
    {
        "id": NotRequired[str],
        "if": NotRequired[Union[bool, float, str]],
        "name": NotRequired[str],
        # MODIFIED: mutually-exclusive 'uses' and 'runs' is better expressed without including it as optional in the common parts
        #        'uses': NotRequired[str],
        #        'run': NotRequired[str],
        # END MODIFIED
        "working-directory": NotRequired[WorkingDirectory],
        "shell": NotRequired[Shell],
        "with": NotRequired[Env],
        "env": NotRequired[Env],
        "continue-on-error": NotRequired[Union[bool, ExpressionSyntax]],
        "timeout-minutes": NotRequired[Union[float, ExpressionSyntax]],
    },
)


class Step4(Step1, Step3):
    pass


class Step5(Step2, Step3):
    pass


Step = Union[Step4, Step5]


class On(TypedDict):
    branch_protection_rule: NotRequired[EventObject]
    check_run: NotRequired[EventObject]
    check_suite: NotRequired[EventObject]
    create: NotRequired[EventObject]
    delete: NotRequired[EventObject]
    deployment: NotRequired[EventObject]
    deployment_status: NotRequired[EventObject]
    discussion: NotRequired[EventObject]
    discussion_comment: NotRequired[EventObject]
    fork: NotRequired[EventObject]
    gollum: NotRequired[EventObject]
    issue_comment: NotRequired[EventObject]
    issues: NotRequired[EventObject]
    label: NotRequired[EventObject]
    merge_group: NotRequired[EventObject]
    milestone: NotRequired[EventObject]
    page_build: NotRequired[EventObject]
    project: NotRequired[EventObject]
    project_card: NotRequired[EventObject]
    project_column: NotRequired[EventObject]
    public: NotRequired[EventObject]
    pull_request: NotRequired[Ref]
    pull_request_review: NotRequired[EventObject]
    pull_request_review_comment: NotRequired[EventObject]
    pull_request_target: NotRequired[Ref]
    push: NotRequired[Ref]
    registry_package: NotRequired[EventObject]
    release: NotRequired[EventObject]
    status: NotRequired[EventObject]
    watch: NotRequired[EventObject]
    workflow_call: NotRequired[WorkflowCall]
    workflow_dispatch: NotRequired[WorkflowDispatch]
    workflow_run: NotRequired[EventObject]
    repository_dispatch: NotRequired[EventObject]
    schedule: NotRequired[list[ScheduleItem]]


class Container(TypedDict):
    image: str
    credentials: NotRequired[Credentials]
    env: NotRequired[Env]
    ports: NotRequired[list[float | str]]
    volumes: NotRequired[list[Volume]]
    options: NotRequired[str]


Permissions = Union[Literal["read-all", "write-all"], PermissionsEvent]


ReusableWorkflowCallJob = TypedDict(
    "ReusableWorkflowCallJob",
    {
        "name": NotRequired[str],
        "needs": NotRequired[JobNeeds],
        "permissions": NotRequired[Permissions],
        "if": NotRequired[Union[bool, float, str]],
        "uses": str,
        "with": NotRequired[Env],
        "secrets": NotRequired[Union[Env, Literal["inherit"]]],
        "strategy": NotRequired[Strategy],
        "concurrency": NotRequired[Union[str, Concurrency]],
    },
)


NormalJob = TypedDict(
    "NormalJob",
    {
        "name": NotRequired[str],
        "needs": NotRequired[JobNeeds],
        "permissions": NotRequired[Permissions],
        "runs-on": Union[str, list, RunsOn, StringContainingExpressionSyntax, ExpressionSyntax],
        "environment": NotRequired[Union[str, Environment]],
        "outputs": NotRequired[dict[str, str]],
        "env": NotRequired[Env],
        "defaults": NotRequired[Defaults],
        "if": NotRequired[Union[bool, float, str]],
        "steps": NotRequired[list[Step]],
        "timeout-minutes": NotRequired[Union[float, ExpressionSyntax]],
        "strategy": NotRequired[Strategy],
        "continue-on-error": NotRequired[Union[bool, ExpressionSyntax]],
        "container": NotRequired[Union[str, Container]],
        "services": NotRequired[dict[str, Container]],
        "concurrency": NotRequired[Union[str, Concurrency]],
    },
)


Workflow = TypedDict(
    "Workflow",
    {
        "name": NotRequired[str],
        "on": Union[Event, list[Event], On],
        "env": NotRequired[Env],
        "defaults": NotRequired[Defaults],
        "concurrency": NotRequired[Union[str, Concurrency]],
        "jobs": dict[str, Union[NormalJob, ReusableWorkflowCallJob]],
        "run-name": NotRequired[str],
        "permissions": NotRequired[Permissions],
    },
)


from dataclasses import dataclass

# MODIFIED: Extensions to add convenience types and cast operators
from typing import Generic, TypeGuard, TypeVar

Job = NormalJob | ReusableWorkflowCallJob
RunStep = Step5
ActionStep = Step4

T = TypeVar("T")


@dataclass
class Identified(Generic[T]):
    id: str
    obj: T


def is_normal_job(job: Job) -> TypeGuard[NormalJob]:
    return "uses" not in job


def is_reusable_workflow_call_job(job: Job) -> TypeGuard[ReusableWorkflowCallJob]:
    return "uses" in job


def is_run_step(step: Step) -> TypeGuard[RunStep]:
    return "run" in step


def is_action_step(step: Step) -> TypeGuard[ActionStep]:
    return "uses" in step


# END MODIFIED
