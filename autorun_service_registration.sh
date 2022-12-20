ef_conf_path=/etc/systemd/system/ef_count_autorun.service
# ef_conf_path=./efmtest.conf
current_path=`pwd`

echo ""
sudo rm -f ${ef_conf_path} &&
echo "[Unit]
Description=ef_count_autorun

[Service]
ExecStart=${current_path}/run_ef_count.sh
WorkingDirectory=${current_path}
User = intflow

[Install]
WantedBy=multi-user.target" | sudo tee -a ${ef_conf_path}
echo ""

sudo systemctl daemon-reload
sudo systemctl enable ef_count_autorun.service
# sudo systemctl start ef_count_autorun.service

echo "Done"
