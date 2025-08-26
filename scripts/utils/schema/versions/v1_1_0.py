"""Schema v1.1.0 - Adds stable IDs and _meta headers.

Key changes from v1.0.0:
- All entities get stable `id` fields
- Root objects get `_meta` with version, timestamps, checksums
- Backward compatible with existing data
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import json
import uuid


@dataclass
class MetaHeader:
    """Metadata header for versioned documents."""
    
    version: str = "1.1.0"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    checksum: Optional[str] = None
    schema_url: str = "https://courses.jeffsthings.com/schemas/v1.1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "version": self.version,
            "created_at": self.created_at or datetime.utcnow().isoformat(),
            "updated_at": self.updated_at or datetime.utcnow().isoformat(),
            "checksum": self.checksum,
            "schema_url": self.schema_url
        }


@dataclass
class BaseEntity:
    """Base class for all entities with stable IDs."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def ensure_id(self) -> None:
        """Ensure entity has a stable ID."""
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class CourseScheduleWeek(BaseEntity):
    """Week in a course schedule."""
    
    week: int
    topic: str
    readings: List[str] = field(default_factory=list)
    assignments: List[str] = field(default_factory=list)
    assessments: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class CourseMetadata(BaseEntity):
    """Course metadata with stable ID."""
    
    code: str
    name: str
    title: Optional[str] = None
    credits: int = 3
    format: str = "Online Asynchronous"
    _meta: Optional[Dict[str, Any]] = None
    
    def add_meta(self) -> None:
        """Add metadata header."""
        if not self._meta:
            self._meta = MetaHeader().to_dict()


class SchemaValidator:
    """Validates and upgrades documents to v1.1.0."""
    
    @staticmethod
    def calculate_checksum(data: Dict[str, Any]) -> str:
        """Calculate SHA256 checksum of data."""
        # Remove _meta for checksum calculation
        clean_data = {k: v for k, v in data.items() if k != "_meta"}
        json_str = json.dumps(clean_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    @staticmethod
    def add_stable_id(obj: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Add stable ID to object if missing."""
        if "id" not in obj:
            if prefix and any(key in obj for key in ["week", "code", "name", "title"]):
                # Generate deterministic ID from content
                content = prefix + str(obj.get("week", "")) + obj.get("code", "") + obj.get("name", "")
                obj["id"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, content))
            else:
                obj["id"] = str(uuid.uuid4())
        return obj
    
    @staticmethod
    def upgrade_document(doc: Dict[str, Any], doc_type: str = "course") -> Dict[str, Any]:
        """Upgrade document to v1.1.0 schema."""
        # Add _meta header if missing
        if "_meta" not in doc:
            doc["_meta"] = MetaHeader().to_dict()
        
        # Add stable IDs based on document type
        if doc_type == "schedule" and "weeks" in doc:
            course_code = doc.get("course_code", "unknown")
            for week_data in doc["weeks"]:
                SchemaValidator.add_stable_id(week_data, f"{course_code}-week-")
        
        elif doc_type == "syllabus" and "sections" in doc:
            for section in doc["sections"]:
                SchemaValidator.add_stable_id(section, "section-")
        
        # Add root ID
        SchemaValidator.add_stable_id(doc, f"{doc_type}-")
        
        # Update checksum
        doc["_meta"]["checksum"] = SchemaValidator.calculate_checksum(doc)
        
        return doc
    
    @staticmethod
    def validate(doc: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate document against v1.1.0 schema."""
        errors = []
        
        # Check for _meta
        if "_meta" not in doc:
            errors.append("Missing _meta header")
        else:
            meta = doc["_meta"]
            if "version" not in meta:
                errors.append("Missing version in _meta")
            elif not meta["version"].startswith("1.1"):
                errors.append(f"Incompatible version: {meta['version']}")
        
        # Check for ID
        if "id" not in doc:
            errors.append("Missing root ID")
        
        return len(errors) == 0, errors


# Schema version registry
SCHEMA_VERSION = "1.1.0"
SCHEMA_VALIDATOR = SchemaValidator