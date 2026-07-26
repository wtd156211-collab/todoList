from pydantic import BaseModel, Field


class AttachmentCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(alias="mimeType")
    size_bytes: int = Field(alias="sizeBytes", gt=0)


class UploadPolicyResponse(BaseModel):
    attachment_id: str = Field(alias="attachmentId")
    object_key: str = Field(alias="objectKey")
    host: str
    form_data: dict[str, str] = Field(alias="formData")
