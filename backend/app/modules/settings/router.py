from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_role
from app.db import get_session
from app.modules.settings import service
from app.modules.settings.schemas import (
    DefaultsData,
    DeleteData,
    EntityPage,
    EntityResponse,
    HolidayCreate,
    LeaveTypeCreate,
    NamedEntityCreate,
    SettingsData,
    SettingsUpdate,
)

router = APIRouter(tags=["settings"])
_SETTINGS_READ = require_role("admin", "hr")
_SETTINGS_WRITE = require_role("admin")


def _page(rows: list[dict[str, Any]], page: int, page_size: int, total: int) -> EntityPage:
    return EntityPage(data=rows, meta={"page": page, "page_size": page_size, "total": total})


async def _list(
    entity: str,
    session: AsyncSession,
    page: int,
    page_size: int,
) -> EntityPage:
    rows, total = await service.list_entities(session, entity, page, page_size)
    return _page(rows, page, page_size, total)


async def _create(
    entity: str,
    values: dict[str, Any],
    session: AsyncSession,
    user: CurrentUser,
) -> EntityResponse:
    return EntityResponse(data=await service.create_entity(session, user.id, entity, values))


async def _update(
    entity: str,
    entity_id: UUID,
    values: dict[str, Any],
    session: AsyncSession,
    user: CurrentUser,
) -> EntityResponse:
    return EntityResponse(data=await service.update_entity(session, user.id, entity, entity_id, values))


async def _delete(
    entity: str,
    entity_id: UUID,
    session: AsyncSession,
    user: CurrentUser,
) -> EntityResponse:
    await service.delete_entity(session, user.id, entity, entity_id)
    return EntityResponse(data=DeleteData(id=entity_id, deleted=True))


@router.get("/settings", response_model=EntityResponse)
async def get_settings(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[CurrentUser, Depends(_SETTINGS_READ)],
) -> EntityResponse:
    return EntityResponse(data=SettingsData(**await service.get_settings(session)))


@router.put("/settings", response_model=EntityResponse)
async def update_settings(
    payload: SettingsUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    values = payload.model_dump()
    values["company_name"] = payload.company_name.strip()
    return EntityResponse(data=SettingsData(**await service.update_settings(session, user.id, values)))


@router.get("/departments", response_model=EntityPage)
async def list_departments(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[CurrentUser, Depends(_SETTINGS_READ)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> EntityPage:
    return await _list("departments", session, page, page_size)


@router.post("/departments", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: NamedEntityCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _create("departments", payload.model_dump(), session, user)


@router.put("/departments/{entity_id}", response_model=EntityResponse)
async def update_department(
    entity_id: UUID,
    payload: NamedEntityCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _update("departments", entity_id, payload.model_dump(), session, user)


@router.delete("/departments/{entity_id}", response_model=EntityResponse)
async def delete_department(
    entity_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _delete("departments", entity_id, session, user)


@router.get("/designations", response_model=EntityPage)
async def list_designations(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[CurrentUser, Depends(_SETTINGS_READ)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> EntityPage:
    return await _list("designations", session, page, page_size)


@router.post("/designations", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_designation(
    payload: NamedEntityCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _create("designations", payload.model_dump(), session, user)


@router.put("/designations/{entity_id}", response_model=EntityResponse)
async def update_designation(
    entity_id: UUID,
    payload: NamedEntityCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _update("designations", entity_id, payload.model_dump(), session, user)


@router.delete("/designations/{entity_id}", response_model=EntityResponse)
async def delete_designation(
    entity_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _delete("designations", entity_id, session, user)


@router.get("/leave-types", response_model=EntityPage)
async def list_leave_types(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[CurrentUser, Depends(_SETTINGS_READ)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> EntityPage:
    return await _list("leave_types", session, page, page_size)


@router.post("/leave-types", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_type(
    payload: LeaveTypeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _create("leave_types", payload.model_dump(), session, user)


@router.put("/leave-types/{entity_id}", response_model=EntityResponse)
async def update_leave_type(
    entity_id: UUID,
    payload: LeaveTypeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _update("leave_types", entity_id, payload.model_dump(), session, user)


@router.delete("/leave-types/{entity_id}", response_model=EntityResponse)
async def delete_leave_type(
    entity_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _delete("leave_types", entity_id, session, user)


@router.post("/leave-types/defaults", response_model=EntityResponse)
async def add_default_leave_types(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return EntityResponse(data=DefaultsData(added=await service.add_default_leave_types(session, user.id)))


@router.get("/holidays", response_model=EntityPage)
async def list_holidays(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[CurrentUser, Depends(_SETTINGS_READ)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> EntityPage:
    return await _list("holidays", session, page, page_size)


@router.post("/holidays", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    payload: HolidayCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _create("holidays", payload.model_dump(), session, user)


@router.put("/holidays/{entity_id}", response_model=EntityResponse)
async def update_holiday(
    entity_id: UUID,
    payload: HolidayCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _update("holidays", entity_id, payload.model_dump(), session, user)


@router.delete("/holidays/{entity_id}", response_model=EntityResponse)
async def delete_holiday(
    entity_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[CurrentUser, Depends(_SETTINGS_WRITE)],
) -> EntityResponse:
    return await _delete("holidays", entity_id, session, user)
