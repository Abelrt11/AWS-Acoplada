import boto3
from botocore.exceptions import ClientError
from typing import Optional, List
from datetime import datetime
from .repository import IContactRepository
from .models import Contact, ContactCreate, ContactUpdate
from .config import DB_TABLE, AWS_REGION

class DynamoContactRepository(IContactRepository):
    def __init__(self):
        self._resource = boto3.resource("dynamodb", region_name=AWS_REGION)
        self._table = self._resource.Table(DB_TABLE)

    def initialize(self) -> None:
        client = boto3.client("dynamodb", region_name=AWS_REGION)
        try:
            client.describe_table(TableName=DB_TABLE)
        except client.exceptions.ResourceNotFoundException:
            raise RuntimeError(
                f"DynamoDB table '{DB_TABLE}' not found in region {AWS_REGION}. "
                "Deploy 'deploy/dynamodb.yml' or set DB_TABLE env var."
            )

    def create(self, data: ContactCreate) -> Contact:
        contact = Contact.new(data.name, data.email, data.tag)
        if self.exists_email(contact.email):
            raise ValueError("email_already_exists")
        self._table.put_item(Item=contact.model_dump())
        return contact

    def get(self, id: str) -> Optional[Contact]:
        resp = self._table.get_item(Key={"id": id})
        item = resp.get("Item")
        return Contact(**item) if item else None

    def list(self, tag: Optional[str] = None) -> List[Contact]:
        if tag:
            resp = self._table.query(
                IndexName="tag-index",
                KeyConditionExpression=boto3.dynamodb.conditions.Key("tag").eq(tag),
            )
            items = resp.get("Items", [])
        else:
            items = []
            scan_kwargs = {}
            while True:
                resp = self._table.scan(**scan_kwargs)
                items.extend(resp.get("Items", []))
                lek = resp.get("LastEvaluatedKey")
                if not lek:
                    break
                scan_kwargs["ExclusiveStartKey"] = lek
        items.sort(key=lambda x: x.get("name","").lower())
        return [Contact(**it) for it in items]

    def update(self, id: str, data: ContactUpdate) -> Optional[Contact]:
        existing = self.get(id)
        if not existing:
            return None
        new_email = data.email if data.email is not None else existing.email
        if self.exists_email(new_email, exclude_id=id):
            raise ValueError("email_already_exists")
        updated = existing.model_copy(update={k: v for k, v in data.model_dump(exclude_unset=True).items()})
        updated.updated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        self._table.put_item(Item=updated.model_dump())
        return updated

    def delete(self, id: str) -> bool:
        resp = self._table.delete_item(Key={"id": id}, ReturnValues="ALL_OLD")
        return "Attributes" in resp

    def exists_email(self, email: str, exclude_id: Optional[str] = None) -> bool:
        scan_kwargs = {"FilterExpression": boto3.dynamodb.conditions.Attr("email").eq(email)}
        while True:
            resp = self._table.scan(**scan_kwargs)
            for it in resp.get("Items", []):
                if exclude_id and it.get("id") == exclude_id:
                    continue
                return True
            lek = resp.get("LastEvaluatedKey")
            if not lek:
                break
            scan_kwargs["ExclusiveStartKey"] = lek
        return False
