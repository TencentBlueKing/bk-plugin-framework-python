#!/bin/bash
# DO NOT MODIFY THIS SECTION !!!
echo "do migrate"
python bin/manage.py migrate --no-input

echo "[Sync] BEGIN ====================="

# 使用智能同步命令，仅在接口定义发生变化时才同步到API网关
# 该命令会自动：
# 1. 生成 definition.yaml 和 resources.yaml
# 2. 计算文件哈希值并与上次同步的哈希值对比
# 3. 仅在哈希值变化时执行 sync_drf_apigateway
# 4. 获取 API 网关公钥
#
# 如需强制同步，可添加 --force 参数：
# python bin/manage.py sync_apigateway_if_changed --force

python bin/manage.py sync_apigateway_if_changed
if [ $? -ne 0 ]
then
    echo "sync_apigateway_if_changed fail"
    exit 1
fi

echo "[Sync] DONE ====================="
# DO NOT MODIFY THIS SECTION !!!