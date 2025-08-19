from fastapi import APIRouter

from src.shared.dependencies.service_deps import audit_service
from src.shared.dependencies.user_deps import current_user
from src.shared.schemas.FilterSchemas import FiltersDep

router = APIRouter(prefix='/history', tags=['History'])

@router.get('/{project_id}/all')
async def get_all_history(user: current_user,
                          project_id: int,
                          service: audit_service):
    result = await service.get_audit(project_id)
    return result


@router.get('/{project_id}/filter')
async def get_filtered_history(user: current_user,
                               project_id: int,
                               service: audit_service,
                               filters: FiltersDep):
    result = await service.get_filtered_audit(project_id, filters)
    return result
