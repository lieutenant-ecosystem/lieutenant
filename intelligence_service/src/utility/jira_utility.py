import urllib
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel

from utility.common_utility import get_raw_http_data


def _get_headers(api_key: str) -> Dict[str, Any]:
    return {"Accept": "application/json", "Authorization": f"Basic {api_key}"}


class Comment(BaseModel):
    id: str
    author_name: str
    author_email_address: Optional[str] = None
    text: str
    created: datetime
    updated: datetime

    def __str__(self) -> str:
        return \
            f"""
---
## Author's Name
{self.author_name}

## Comment
{self.text}

## Created
{self.created}

## Updated
{self.updated}
---
"""

    @staticmethod
    def _get_from_raw_comment(data: Dict[str, Any]) -> "Comment":
        return Comment(
            id=data["id"],
            author_name=data["author"]["displayName"],
            author_email_address=data["author"]["emailAddress"] if "emailAddress" in data["author"] else None,
            text=data["body"],
            created=datetime.strptime(data["created"], '%Y-%m-%dT%H:%M:%S.%f%z'),
            updated=datetime.strptime(data["updated"], '%Y-%m-%dT%H:%M:%S.%f%z')
        )


class Issue(BaseModel):
    id: str
    type: str
    type_description: str
    assignee_name: Optional[str] = None
    assignee_email_address: Optional[str] = None
    creator_name: str
    creator_email_address: str
    status: str
    status_description: str
    security: str
    security_description: str
    description: Optional[str] = None
    release_note: Optional[str] = None
    impact_assessment: Optional[str] = None
    deployment_instructions: Optional[str] = None
    reproduction_steps: Optional[str] = None
    actual_result: Optional[str] = None
    cause: Optional[str] = None
    fix: Optional[str] = None
    developer_notes: Optional[str] = None
    comment_list: List[Comment] = []

    def __str__(self) -> str:
        comment_string: str = "\n".join([str(comment) for comment in self.comment_list])
        return \
            f"""
---
# Ticket Key
{self.id}

# Issue Type
{self.type}

# Issue Type's Description
{self.type_description}

# Assignee's Name
{self.assignee_name}

# Creator's Name
{self.creator_name} 

# Status
{self.status}

# Status Description
{self.status_description} 

# Security
{self.security}

# Security Description
{self.security_description}

# Description
{self.description}

# Release Note
{self.release_note}

# Impact Assesment
{self.impact_assessment}

# Deployment Instructions
{self.deployment_instructions}

# Reproduction Steps
{self.reproduction_steps}

# Actual (Current) Result
{self.actual_result}

# Cause
{self.cause} 

# Fix
{self.fix}

# Developer Notes
{self.developer_notes}

# Comments
{comment_string}
---
"""

    @staticmethod
    async def _get_all_issues_raw(jql: str, base_url: str, api_key: str) -> List[Dict[str, Any]]:
        encoded_jql: str = urllib.parse.quote(jql)
        url: str = f"{base_url}/search?jql={encoded_jql}"
        raw_data: Dict[str, Any] = await get_raw_http_data(url, _get_headers(api_key))
        return raw_data["issues"]

    @staticmethod
    async def get_from_issue_id(issue_id: str, base_url: str, api_key: str) -> "Issue":
        url: str = f"{base_url}/issue/{issue_id}"
        raw_data: Dict[str, Any] = await get_raw_http_data(url, _get_headers(api_key))

        return Issue(
            id=issue_id,
            type=raw_data["fields"]['issuetype']['name'],
            type_description=raw_data["fields"]['issuetype']['description'],
            assignee_name=raw_data["fields"]['assignee']['displayName'] if raw_data["fields"]['assignee'] else None,
            assignee_email_address=raw_data["fields"]['assignee']['emailAddress'] if raw_data["fields"][
                'assignee'] else None,
            creator_name=raw_data["fields"]['creator']['displayName'],
            creator_email_address=raw_data["fields"]['creator']['emailAddress'],
            status=raw_data["fields"]['status']['name'],
            status_description=raw_data["fields"]['status']['description'],
            security=raw_data["fields"]['security']['name'],
            security_description=raw_data["fields"]['security']['description'],
            description=raw_data["fields"]['description'],
            release_note=raw_data["fields"]['customfield_10710'],
            impact_assessment=raw_data["fields"]["customfield_12010"],
            deployment_instructions=raw_data["fields"]["customfield_11710"],
            reproduction_steps=raw_data["fields"]["customfield_12510"],
            actual_result=raw_data["fields"]["customfield_12511"],
            cause=raw_data["fields"]["customfield_12772"],
            fix=raw_data["fields"]["customfield_12773"],
            developer_notes=raw_data["fields"]["customfield_12774"],
            comment_list=[Comment._get_from_raw_comment(data) for data in raw_data["fields"]["comment"]["comments"]],
        )

    @staticmethod
    async def get_from_jql(jql: str, base_url: str, api_key: str) -> List["Issue"]:
        data_list: List[Dict[str, Any]] = await Issue._get_all_issues_raw(jql)

        return [await Issue.get_from_issue_id(data["key"], base_url, api_key) for data in data_list]
