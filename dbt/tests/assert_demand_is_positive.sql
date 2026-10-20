select
    demand_hour,
    actual_demand_mwh
from {{ ref('fct_hourly_demand') }}
where actual_demand_mwh <= 0