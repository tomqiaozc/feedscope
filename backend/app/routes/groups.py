from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.db.repos.group_member_repo import GroupMemberRepo
from app.db.repos.group_repo import GroupRepo
from app.schemas.groups import (
    BatchDeleteRequest,
    BatchMemberCreate,
    GroupCreate,
    GroupMemberCreate,
    GroupMemberOut,
    GroupOut,
    GroupUpdate,
)

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


def _group_out(g, member_count: int = 0) -> GroupOut:
    return GroupOut(
        id=g.id,
        name=g.name,
        description=g.description,
        member_count=member_count,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


def _member_out(m) -> GroupMemberOut:
    return GroupMemberOut(
        id=m.id,
        username=m.username,
        display_name=m.display_name,
        profile_image_url=m.profile_image_url,
        notes=m.notes,
        created_at=m.created_at,
    )


# ---- Group CRUD ----


@router.get("")
async def list_groups(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = GroupRepo(user_id, session)
    rows = await repo.list()
    return {
        "success": True,
        "data": [_group_out(r["group"], r["member_count"]) for r in rows],
    }


@router.post("", status_code=201)
async def create_group(
    body: GroupCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = GroupRepo(user_id, session)
    group = await repo.create(name=body.name, description=body.description)
    return {"success": True, "data": _group_out(group)}


@router.put("/{group_id}")
async def update_group(
    group_id: int,
    body: GroupUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = GroupRepo(user_id, session)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    group = await repo.update(group_id, **updates)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"success": True, "data": _group_out(group)}


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = GroupRepo(user_id, session)
    deleted = await repo.delete(group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"success": True}


# ---- Group Members ----


@router.get("/{group_id}/members")
async def list_group_members(
    group_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    member_repo = GroupMemberRepo(user_id, session)
    members = await member_repo.list(group_id)
    return {"success": True, "data": [_member_out(m) for m in members]}


@router.post("/{group_id}/members", status_code=201)
async def create_group_member(
    group_id: int,
    body: GroupMemberCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    # Verify group exists
    group_repo = GroupRepo(user_id, session)
    group = await group_repo.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member_repo = GroupMemberRepo(user_id, session)
    member = await member_repo.create(
        group_id=group_id,
        username=body.username,
        display_name=body.display_name,
        notes=body.notes,
    )
    return {"success": True, "data": _member_out(member)}


@router.post("/{group_id}/members/batch", status_code=201)
async def batch_create_group_members(
    group_id: int,
    body: BatchMemberCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    # Verify group exists
    group_repo = GroupRepo(user_id, session)
    group = await group_repo.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member_repo = GroupMemberRepo(user_id, session)
    members_data = [m.model_dump() for m in body.members]
    members = await member_repo.batch_create(group_id, members_data)
    return {"success": True, "data": [_member_out(m) for m in members]}


@router.delete("/{group_id}/members/batch")
async def batch_delete_group_members(
    group_id: int,
    body: BatchDeleteRequest,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    member_repo = GroupMemberRepo(user_id, session)
    deleted = await member_repo.batch_delete(group_id, body.member_ids)
    return {"success": True, "deleted": deleted}


@router.delete("/{group_id}/members/{member_id}")
async def delete_group_member(
    group_id: int,
    member_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    member_repo = GroupMemberRepo(user_id, session)
    member = await member_repo.get(member_id)
    if not member or member.group_id != group_id:
        raise HTTPException(status_code=404, detail="Member not found")
    await member_repo.delete(member_id)
    return {"success": True}
