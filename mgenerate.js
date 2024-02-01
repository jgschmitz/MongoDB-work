mgeneratejs '{"_id": "$oid", "tsf_id": "$oid", "datetime": {"$date": {"min": "2021-01-01", "max": "2022-01-01"}}, 
"message": {"$string": {"length": 300, "char": "abcdefghijklmnopqrstuvwxyz"}}, "level": null, "line_number": {"$number": 
{"integer": true, "min": 0, "max": 100}}, "log_file": "$file", "created_at": {"$date": {"min": "2023-01-01", "max": "2024-01-01"}}}' -n 100 > generated_data.json
