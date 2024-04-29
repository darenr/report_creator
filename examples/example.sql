create or replace view sh_customers_dim_view as
select a.cust_id, a.cust_last_name || ', ' || a.cust_first_name as customer_name,
  a.cust_city || ', ' || a.cust_state_province || ', ' || a.country_id as city_id,
  a.cust_city as city_name,
  a.cust_state_province || ', ' || a.country_id as state_province_id,
  a.cust_state_province as state_province_name,
  b.country_id, b.country_name, b.country_subregion as subregion, b.country_region as region
from sh.customers a, sh.countries b
where a.country_id = b.country_id;
order by a.cust_id desc;
