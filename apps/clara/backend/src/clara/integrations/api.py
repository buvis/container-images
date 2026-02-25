import json
import uuid

from fastapi import APIRouter, Query, UploadFile
from fastapi.responses import Response

from clara.deps import Db, VaultAccess
from clara.integrations.csv_io import export_csv, import_csv
from clara.integrations.json_export import export_vault_json
from clara.integrations.vcard import export_vcard, import_vcard

router = APIRouter()


@router.post("/import/vcard", status_code=201)
async def import_vcard_endpoint(
    vault_id: uuid.UUID, file: UploadFile, db: Db, _access: VaultAccess
) -> dict[str, int]:
    data = (await file.read()).decode("utf-8")
    contacts = await import_vcard(db, vault_id, data)
    return {"imported": len(contacts)}


@router.post("/import/csv", status_code=201)
async def import_csv_endpoint(
    vault_id: uuid.UUID,
    file: UploadFile,
    db: Db,
    _access: VaultAccess,
    field_map: str | None = Query(None),
) -> dict[str, int]:
    data = (await file.read()).decode("utf-8")
    mapping = json.loads(field_map) if field_map else None
    contacts, _errors = await import_csv(db, vault_id, data, field_map=mapping)
    return {"imported": len(contacts)}


@router.get("/export/vcard")
async def export_vcard_endpoint(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> Response:
    vcard_data = await export_vcard(db, vault_id)
    return Response(
        content=vcard_data,
        media_type="text/vcard",
        headers={
            "Content-Disposition": 'attachment; filename="contacts.vcf"'
        },
    )


@router.get("/export/csv")
async def export_csv_endpoint(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> Response:
    csv_data = await export_csv(db, vault_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="contacts.csv"'
        },
    )


@router.get("/export/json")
async def export_json_endpoint(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> Response:
    vault_data = await export_vault_json(db, vault_id)
    return Response(
        content=json.dumps(vault_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="vault_export.json"'
        },
    )
