SELECT a.fitfile_name,
       DATE(a.created) as created,

       MAX(sv_distance.float_value) as distance,

       AVG(sv_power.int_value / a.user_weight_kg) as mean_normalized_power,
       STDDEV(sv_power.int_value / a.user_weight_kg) as std_normalized_power,
       MAX(sv_power.int_value / a.user_weight_kg) as max_normalized_power,

       AVG(sv_speed.float_value) as mean_speed,
       STDDEV(sv_speed.float_value) as std_speed,
       MAX(sv_speed.float_value) as max_speed
FROM samples s
         INNER JOIN sample_values sv_power on s.id = sv_power.sample_id AND sv_power.field_id = (
             SELECT id FROM fields
             WHERE field_name = 'Power'
         )
         INNER JOIN sample_values sv_speed on s.id = sv_speed.sample_id AND sv_speed.field_id = (
             SELECT id FROM fields
             WHERE field_name = 'enhanced_speed'
         )
         INNER JOIN sample_values sv_distance on s.id = sv_distance.sample_id AND sv_distance.field_id = (
             SELECT id FROM fields
             WHERE field_name = 'distance'
         )
         INNER JOIN activities a on s.activity_id = a.id
WHERE a.user_weight_kg > 0 AND sv_power.int_value > 0 AND sv_speed.float_value > 0
      AND (NOW() - a.created) < '90 days'::interval
GROUP BY s.activity_id, a.created, created, a.fitfile_name
ORDER BY a.created;
