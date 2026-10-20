select
    demand_date,
    balancing_authority,
    sum(actual_demand_mwh) as total_demand_mwh,
    max(actual_demand_mwh) as peak_demand_mwh,
    min(actual_demand_mwh) as min_demand_mwh,
    avg(actual_demand_mwh) as avg_demand_mwh,
    avg(abs_pct_error)     as mape,
    count(*)               as hours_observed
from {{ ref('fct_hourly_demand') }}
group by 1, 2