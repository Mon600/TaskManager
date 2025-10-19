from fastapi import APIRouter

from src.shared.dependencies.service_deps import stat_service

router = APIRouter(prefix='/statistic', tags=['statistic'])

@router.get("/{project_id}/all")
async def get_stat(project_id: int, service: stat_service):
    res = await service.get_top(project_id)
    return  res


@router.get("/{project_id}/top-by-days")
async def get_stat(project_id: int,days: int, service: stat_service):
    res = await service.get_top_by_date(project_id, days)
    print(res)
    return  res


@router.get('/{project_id}/month_top')
async def month_top(project_id: int, month: int, year: int, service: stat_service):
    await service.get_month_stat(project_id, month, year)


@router.get('/{project_id}/avg_tasks')
async def avg_tasks(project_id: int, service: stat_service):
    await service.avg_tasks(project_id)