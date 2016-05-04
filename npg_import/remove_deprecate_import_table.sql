delete from ir_model_constraint where model in ( select id from ir_model where model in ('import.related.fields','import.m2o.substitutions','import.m2o.values'));
delete from ir_model_relation where model in ( select id from ir_model where model in ('import.related.fields','import.m2o.substitutions','import.m2o.values'));
delete from ir_model_fields where model_id in ( select id from ir_model where model in ('import.related.fields','import.m2o.substitutions','import.m2o.values'));;
delete from ir_model where model in ('import.related.fields','import.m2o.substitutions','import.m2o.values')
