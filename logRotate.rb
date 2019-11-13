include_recipe "mongo-bootstrapo"

# run on your own this: logrotate -vf /etc/logrotate.d/mongodb
#
logrotate "mongodb" do
  paths "#{node[:mongodb][:logpath]}/*.log"
  period node[:mongodb][:logrotate][:period]
  keep node[:mongodb][:logrotate][:keep]
end
