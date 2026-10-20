with source as (

    select * from {{ source('raw_energy', 'eia_demand_raw') }}

),

ranked as (

    select
        period                as demand_hour,
        respondent            as balancing_authority,
        respondent_name       as balancing_authority_name,
        type_code,
        type_name,
        value                 as demand_mwh,
        ingested_at,
        row_number() over (
            partition by period, respondent, type_code
            order by ingested_at desc
        ) as row_num
    from source
    where value is not null

)

select
    demand_hour,
    balancing_authority,
    balancing_authority_name,
    type_code,
    type_name,
    demand_mwh,
    ingested_at
from ranked
where row_num = 1