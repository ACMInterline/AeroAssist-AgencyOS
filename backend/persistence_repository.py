from __future__ import annotations

from typing import Any, Iterable, Mapping

from database import Database
from persistence_query import (
    CollectionOwnershipType,
    PaginationMetadata,
    PaginationRequest,
    QueryPage,
    QueryValidationError,
    SortRequest,
    decode_cursor,
    encode_cursor,
    get_collection_ownership,
    monotonic_ms,
    record_query_diagnostic,
    validate_filters,
    validate_projection,
)


class PersistenceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def find_agency_records(
        self,
        *,
        collection_name: str,
        agency_id: str,
        filters: Mapping[str, Any] | None = None,
        sort_field: str | None = None,
        sort_direction: str | int | None = None,
        pagination: PaginationRequest | None = None,
        projection: Iterable[str] | None = None,
        correlation_id: str | None = None,
    ) -> QueryPage:
        if not agency_id:
            raise QueryValidationError("agency_id is required for tenant-scoped queries.")
        ownership = get_collection_ownership(collection_name)
        if ownership.tenant_field is None or ownership.ownership not in {
            CollectionOwnershipType.AGENCY_OWNED,
            CollectionOwnershipType.IMMUTABLE_SNAPSHOT,
            CollectionOwnershipType.AUDIT_SECURITY,
            CollectionOwnershipType.OPERATIONAL_EPHEMERAL,
            CollectionOwnershipType.MIXED_PROJECTION,
        }:
            raise QueryValidationError("Agency query helper cannot access a platform/global collection.")
        clean_filters = validate_filters(filters, ownership, reserved_fields=(ownership.tenant_field,))
        clean_filters[ownership.tenant_field] = agency_id
        return await self._find(
            collection_name=collection_name,
            tenant=agency_id,
            tenant_scoped=True,
            filters=clean_filters,
            sort_field=sort_field,
            sort_direction=sort_direction,
            pagination=pagination,
            projection=projection,
            correlation_id=correlation_id,
        )

    async def find_platform_records(
        self,
        *,
        collection_name: str,
        filters: Mapping[str, Any] | None = None,
        agency_id: str | None = None,
        sort_field: str | None = None,
        sort_direction: str | int | None = None,
        pagination: PaginationRequest | None = None,
        projection: Iterable[str] | None = None,
        correlation_id: str | None = None,
    ) -> QueryPage:
        ownership = get_collection_ownership(collection_name)
        clean_filters = validate_filters(filters, ownership, reserved_fields=((ownership.tenant_field,) if ownership.tenant_field else ()))
        if agency_id is not None:
            if not ownership.tenant_field:
                raise QueryValidationError("Global collections do not accept agency predicates.")
            clean_filters[ownership.tenant_field] = agency_id
        return await self._find(
            collection_name=collection_name,
            tenant=agency_id,
            tenant_scoped=agency_id is not None,
            filters=clean_filters,
            sort_field=sort_field,
            sort_direction=sort_direction,
            pagination=pagination,
            projection=projection,
            correlation_id=correlation_id,
        )

    async def find_global_records(
        self,
        *,
        collection_name: str,
        filters: Mapping[str, Any] | None = None,
        sort_field: str | None = None,
        sort_direction: str | int | None = None,
        pagination: PaginationRequest | None = None,
        projection: Iterable[str] | None = None,
        correlation_id: str | None = None,
    ) -> QueryPage:
        ownership = get_collection_ownership(collection_name)
        if ownership.ownership not in {CollectionOwnershipType.PLATFORM_GLOBAL, CollectionOwnershipType.REFERENCE_DATA}:
            raise QueryValidationError("Global query helper cannot access tenant-owned or mixed collections.")
        return await self.find_platform_records(
            collection_name=collection_name,
            filters=filters,
            sort_field=sort_field,
            sort_direction=sort_direction,
            pagination=pagination,
            projection=projection,
            correlation_id=correlation_id,
        )

    async def find_mixed_records(
        self,
        *,
        collection_name: str,
        agency_id: str,
        filters: Mapping[str, Any] | None = None,
        identity_field: str = "id",
        include_historical: bool = False,
        pagination: PaginationRequest | None = None,
    ) -> QueryPage:
        ownership = get_collection_ownership(collection_name)
        if ownership.ownership is not CollectionOwnershipType.MIXED_PROJECTION:
            raise QueryValidationError("Mixed projection helper requires a mixed-projection collection.")
        page_request = pagination or PaginationRequest.build()
        agency_page = await self.find_agency_records(
            collection_name=collection_name,
            agency_id=agency_id,
            filters=filters,
            pagination=PaginationRequest.build(limit=page_request.limit, offset=0),
        )
        global_filters = validate_filters(filters, ownership, reserved_fields=(ownership.tenant_field,))
        global_filters[ownership.tenant_field] = None
        global_page = await self._find(
            collection_name=collection_name,
            tenant=None,
            tenant_scoped=False,
            filters=global_filters,
            sort_field=None,
            sort_direction=None,
            pagination=PaginationRequest.build(limit=page_request.limit, offset=0),
            projection=None,
            correlation_id=None,
        )
        merged: dict[Any, dict[str, Any]] = {}
        for item in global_page.items:
            if item.get(ownership.tenant_field) in {None, ""} and (include_historical or not item.get("historical_only")):
                merged[item.get(identity_field)] = item
        for item in agency_page.items:
            merged[item.get(identity_field)] = item
        items = list(merged.values())[page_request.offset : page_request.offset + page_request.limit]
        return QueryPage(
            items=items,
            pagination=PaginationMetadata(
                limit=page_request.limit,
                offset=page_request.offset,
                returned=len(items),
                has_more=len(merged) > page_request.offset + len(items),
                next_cursor=None,
                total=len(merged) if page_request.include_total else None,
            ),
        )

    async def count_agency_records(
        self,
        *,
        collection_name: str,
        agency_id: str,
        filters: Mapping[str, Any] | None = None,
    ) -> int:
        if not agency_id:
            raise QueryValidationError("agency_id is required for tenant-scoped counts.")
        ownership = get_collection_ownership(collection_name)
        if not ownership.tenant_field:
            raise QueryValidationError("Tenant count helper cannot access a global collection.")
        clean_filters = validate_filters(filters, ownership, reserved_fields=(ownership.tenant_field,))
        clean_filters[ownership.tenant_field] = agency_id
        return await self.db.collection(collection_name).count(clean_filters)

    async def _find(
        self,
        *,
        collection_name: str,
        tenant: str | None,
        tenant_scoped: bool,
        filters: dict[str, Any],
        sort_field: str | None,
        sort_direction: str | int | None,
        pagination: PaginationRequest | None,
        projection: Iterable[str] | None,
        correlation_id: str | None,
    ) -> QueryPage:
        ownership = get_collection_ownership(collection_name)
        page_request = pagination or PaginationRequest.build()
        sort = SortRequest.build(sort_field, sort_direction, ownership)
        offset = page_request.offset
        if page_request.cursor:
            if page_request.offset:
                raise QueryValidationError("offset and cursor cannot be combined.")
            offset = decode_cursor(page_request.cursor, collection=collection_name, tenant=tenant, sort=sort)
        clean_projection = validate_projection(projection, ownership.allowed_filter_fields | ownership.allowed_sort_fields) if projection is not None else None
        started = monotonic_ms()
        rows = await self.db.collection(collection_name).find_many(
            filters or None,
            sort=sort.mongo_spec(),
            limit=page_request.limit + 1,
            offset=offset,
            projection=clean_projection,
        )
        has_more = len(rows) > page_request.limit
        items = rows[: page_request.limit]
        total = await self.db.collection(collection_name).count(filters or None) if page_request.include_total else None
        next_cursor = None
        if has_more:
            next_cursor = encode_cursor(
                collection=collection_name,
                tenant=tenant,
                offset=offset + len(items),
                sort=sort,
            )
        record_query_diagnostic(
            collection_category=ownership.ownership.value,
            operation="find_many",
            duration_ms=monotonic_ms() - started,
            returned_count=len(items),
            requested_limit=page_request.limit,
            tenant_scoped=tenant_scoped,
            query_class=f"{collection_name}:{sort.field}:{sort.direction}",
            correlation_id=correlation_id,
        )
        return QueryPage(
            items=items,
            pagination=PaginationMetadata(
                limit=page_request.limit,
                offset=offset,
                returned=len(items),
                has_more=has_more,
                next_cursor=next_cursor,
                total=total,
            ),
        )
