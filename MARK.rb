<source>
  @type tail
  path /path/to/logfile
  pos_file /path/to/position/file
  read_from_head true
  tag mytag
  format /^(?<timestamp>[^,]+),(?<field1>[^,]+),(?<field2>[^,]+),(?<field3>[^,]+),(?<field4>[^,]+),(?<field5>[^,]+),(?<field6>[^,]+),(?<field7>[^,]+),(?<field8>[^,]+),(?<field9>[^,]+),(?<field10>[^,]+),(?<field11>[^,]+)$/
  time_format %Y-%m-%d %H:%M:%S
</source>

<match mytag>
  @type rewrite_tag_filter
  <rule>
    key timestamp
    pattern /^(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})\s(?<hour>\d{2}):(?<minute>\d{2}):(?<second>\d{2}),(?<millisecond>\d{2})$/
    reserve true
  </rule>
  <rule>
    key fields
    remove_keys timestamp
    enable_ruby
    <record>
      log_json ${fields.to_json}
    </record>
  </rule>
  tag mytag_json
</match>

<match mytag_json>
  @type mongodb
  database mydb
  collection mycollection
  host myhost
  port myport
  user myuser
  password mypassword
  include_tag_key true
  tag_key tag
  replace_dot_in_key_with __
  utc true
  <buffer>
    flush_interval 10s
  </buffer>
</match>
