import calendar
import datetime
from datetime import timedelta

from src.project.statistics_service.repositories.statistic_repository import StatisticRepository


class StatisticService:
    def __init__(self, repository: StatisticRepository):
        self.repository = repository

    async def get_top(self, project_id: int):
        res = await self.repository.get_all(project_id)
        print(res)
        return res

    async def get_top_by_date(self, project_id: int, days: int):
        end_date = datetime.date.today()
        start_date = end_date - timedelta(days=days)
        res = await self.repository.get_with_day_limit(project_id, start_date, end_date)
        return res


    async def get_month_stat(self, project_id: int, month_num: int, year: int):
        start_date = datetime.date(year=year, month=month_num, day=1)
        last_day_of_month_num = calendar.monthrange(year, month_num)[1]
        end_date = datetime.date(year=start_date.year, month=start_date.month, day=last_day_of_month_num)
        res = await self.repository.get_current_month_stat(project_id, start_date, end_date)
        print(res)


    async def avg_tasks(self, project_id: int):
        res = await self.repository.get_avg_completed_tasks(project_id)
        print(res)