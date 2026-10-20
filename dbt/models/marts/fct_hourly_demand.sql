with pivoted as (

    select
        demand_hour,
        balancing_authority,
        max(case when type_code = 'D'  then demand_mwh end) as actual_demand_mwh,
        max(case when type_code = 'DF' then demand_mwh end) as forecast_demand_mwh
    from {{ ref('stg_eia_demand') }}
    group by 1, 2

)

select
    demand_hour,
    date(demand_hour)              as demand_date,
    extract(hour from demand_hour) as hour_of_day,
    balancing_authority,
    actual_demand_mwh,
    forecast_demand_mwh,
    forecast_demand_mwh - actual_demand_mwh      as forecast_error_mwh,
    abs(forecast_demand_mwh - actual_demand_mwh) as abs_forecast_error_mwh,
    safe_divide(
        abs(forecast_demand_mwh - actual_demand_mwh),
        actual_demand_mwh
    ) as abs_pct_error
from pivoted
where actual_demand_mwh is not null