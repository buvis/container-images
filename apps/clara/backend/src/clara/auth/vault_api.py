import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from clara.auth.models import User, Vault, VaultMembership, VaultSettings
from clara.auth.schemas import (
    MemberInvite,
    MemberRead,
    MemberUpdate,
    VaultCreate,
    VaultRead,
    VaultSettingsRead,
    VaultSettingsUpdate,
    VaultUpdate,
)
from clara.deps import CurrentUser, Db, require_role

router = APIRouter()


@router.get("", response_model=list[VaultRead])
async def list_vaults(user: CurrentUser, db: Db) -> list[VaultRead]:
    stmt = (
        select(Vault)
        .join(VaultMembership)
        .where(VaultMembership.user_id == user.id)
    )
    result = await db.execute(stmt)
    return [VaultRead.model_validate(v) for v in result.scalars().all()]


@router.post("", response_model=VaultRead, status_code=201)
async def create_vault(body: VaultCreate, user: CurrentUser, db: Db) -> VaultRead:
    vault = Vault(name=body.name, owner_user_id=user.id)
    db.add(vault)
    await db.flush()
    membership = VaultMembership(
        user_id=user.id, vault_id=vault.id, role="owner"
    )
    db.add(membership)
    settings = VaultSettings(vault_id=vault.id)
    db.add(settings)
    await db.flush()
    return VaultRead.model_validate(vault)


@router.get("/{vault_id}", response_model=VaultRead)
async def get_vault(vault_id: uuid.UUID, user: CurrentUser, db: Db) -> VaultRead:
    stmt = (
        select(Vault)
        .join(VaultMembership)
        .where(VaultMembership.user_id == user.id)
        .where(Vault.id == vault_id)
    )
    vault = (await db.execute(stmt)).scalar_one_or_none()
    if vault is None:
        raise HTTPException(status_code=404, detail="Vault not found")
    return VaultRead.model_validate(vault)


@router.patch("/{vault_id}", response_model=VaultRead)
async def update_vault(
    vault_id: uuid.UUID,
    body: VaultUpdate,
    db: Db,
    _: VaultMembership = require_role("owner"),
) -> VaultRead:
    vault = await db.get(Vault, vault_id)
    if vault is None:
        raise HTTPException(status_code=404, detail="Vault not found")
    if body.name is not None:
        vault.name = body.name
    await db.flush()
    return VaultRead.model_validate(vault)


@router.delete("/{vault_id}", status_code=204)
async def delete_vault(
    vault_id: uuid.UUID,
    db: Db,
    _: VaultMembership = require_role("owner"),
) -> None:
    vault = await db.get(Vault, vault_id)
    if vault is None:
        raise HTTPException(status_code=404, detail="Vault not found")
    await db.delete(vault)
    await db.flush()


# --- Member management ---


@router.get("/{vault_id}/members", response_model=list[MemberRead])
async def list_members(
    vault_id: uuid.UUID,
    db: Db,
    _: VaultMembership = require_role("owner", "admin", "member"),
) -> list[MemberRead]:
    stmt = (
        select(VaultMembership)
        .where(VaultMembership.vault_id == vault_id)
        .options()
    )
    result = await db.execute(stmt)
    members = result.scalars().all()
    out = []
    for m in members:
        user = await db.get(User, m.user_id)
        if user:
            out.append(
                MemberRead(
                    user_id=m.user_id,
                    email=user.email,
                    name=user.name,
                    role=m.role,
                    joined_at=m.created_at,
                )
            )
    return out


@router.post("/{vault_id}/members", response_model=MemberRead, status_code=201)
async def invite_member(
    vault_id: uuid.UUID,
    body: MemberInvite,
    db: Db,
    _: VaultMembership = require_role("owner", "admin"),
) -> MemberRead:
    user = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    existing = (
        await db.execute(
            select(VaultMembership).where(
                VaultMembership.user_id == user.id,
                VaultMembership.vault_id == vault_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Already a member")
    membership = VaultMembership(
        user_id=user.id, vault_id=vault_id, role=body.role
    )
    db.add(membership)
    await db.flush()
    return MemberRead(
        user_id=user.id,
        email=user.email,
        name=user.name,
        role=membership.role,
        joined_at=membership.created_at,
    )


@router.patch("/{vault_id}/members/{user_id}", response_model=MemberRead)
async def update_member_role(
    vault_id: uuid.UUID,
    user_id: uuid.UUID,
    body: MemberUpdate,
    db: Db,
    _: VaultMembership = require_role("owner", "admin"),
) -> MemberRead:
    stmt = select(VaultMembership).where(
        VaultMembership.user_id == user_id,
        VaultMembership.vault_id == vault_id,
    )
    membership = (await db.execute(stmt)).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=404, detail="Member not found")
    # Prevent demoting sole owner
    if membership.role == "owner" and body.role != "owner":
        owner_count = (
            await db.execute(
                select(VaultMembership).where(
                    VaultMembership.vault_id == vault_id,
                    VaultMembership.role == "owner",
                )
            )
        ).scalars().all()
        if len(owner_count) <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote sole owner")
    membership.role = body.role
    await db.flush()
    user = await db.get(User, user_id)
    return MemberRead(
        user_id=user_id,
        email=user.email if user else "",
        name=user.name if user else "",
        role=membership.role,
        joined_at=membership.created_at,
    )


@router.delete("/{vault_id}/members/{user_id}", status_code=204)
async def remove_member(
    vault_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Db,
    _: VaultMembership = require_role("owner", "admin"),
) -> None:
    stmt = select(VaultMembership).where(
        VaultMembership.user_id == user_id,
        VaultMembership.vault_id == vault_id,
    )
    membership = (await db.execute(stmt)).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=404, detail="Member not found")
    # Cannot remove sole owner
    if membership.role == "owner":
        owner_count = (
            await db.execute(
                select(VaultMembership).where(
                    VaultMembership.vault_id == vault_id,
                    VaultMembership.role == "owner",
                )
            )
        ).scalars().all()
        if len(owner_count) <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove sole owner")
    await db.delete(membership)
    await db.flush()


# --- Vault settings ---


@router.get("/{vault_id}/settings", response_model=VaultSettingsRead)
async def get_vault_settings(
    vault_id: uuid.UUID,
    db: Db,
    _: VaultMembership = require_role("owner", "admin"),
) -> VaultSettingsRead:
    stmt = select(VaultSettings).where(VaultSettings.vault_id == vault_id)
    settings = (await db.execute(stmt)).scalar_one_or_none()
    if settings is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    return VaultSettingsRead.model_validate(settings)


@router.patch("/{vault_id}/settings", response_model=VaultSettingsRead)
async def update_vault_settings(
    vault_id: uuid.UUID,
    body: VaultSettingsUpdate,
    db: Db,
    _: VaultMembership = require_role("owner", "admin"),
) -> VaultSettingsRead:
    stmt = select(VaultSettings).where(VaultSettings.vault_id == vault_id)
    settings = (await db.execute(stmt)).scalar_one_or_none()
    if settings is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.flush()
    return VaultSettingsRead.model_validate(settings)
