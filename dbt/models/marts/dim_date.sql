with dates as (

    select date_day
    from unnest(
        generate_date_array('2020-01-01', current_date(), interval 1 day)
    ) as date_day

)

select
    date_day,
    extract(year from date_day)      as year_num,
    extract(month from date_day)     as month_num,
    format_date('%B', date_day)      as month_name,
    extract(day from date_day)       as day_of_month,
    extract(dayofweek from date_day) as day_of_week_num,
    format_date('%A', date_day)      as day_name,
    extract(dayofweek from date_day) in (1, 7) as is_weekend,
    case
        when extract(month from date_day) in (12, 1, 2) then 'Winter'
        when extract(month from date_day) in (3, 4, 5)  then 'Spring'
        when extract(month from date_day) in (6, 7, 8)  then 'Summer'
        else 'Fall'
    end as season
from dates