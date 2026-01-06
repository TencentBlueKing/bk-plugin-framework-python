#!/bin/bash
# DO NOT MODIFY THIS SECTION !!!
echo "do migrate"
python bin/manage.py migrate --no-input

echo "[Sync] BEGIN ====================="
echo "[Sync] generate definition.yaml"
python bin/manage.py generate_definition_yaml
if [ $? -ne 0 ]
then
	echo "run generate_definition_yaml fail, please run this command on your development env to find out the reason"
	exit 1
fi


if [ -f /app/definition.yaml ]
then
    echo "[Sync] the /app/definition.yaml content:"
	cat /app/definition.yaml
	echo "===================="
fi


echo "[Sync] generate resources.yaml"
python bin/manage.py generate_resources_yaml
if [ $? -ne 0 ]
then
	echo "run generate_resources_yaml fail, please run this command on your development env to find out the reason"
	exit 1
fi

if [ -f /app/resources.yaml ]
then
	echo "[Sync] the /app/resources.yaml content:"
	cat /app/resources.yaml
	echo "===================="
fi

echo "[Sync] sync to apigateway"
python bin/manage.py sync_drf_apigateway
if [ $? -ne 0 ]
then
	echo "run sync_drf_apigateway fail"
	exit 1
fi

echo "[Sync] fetch the public key"
python bin/manage.py fetch_apigw_public_key
if [ $? -ne 0 ]
then
	echo "run fetch_apigw_public_key fail"
	exit 1
fi

echo "[Sync] DONE ====================="
# DO NOT MODIFY THIS SECTION !!!

