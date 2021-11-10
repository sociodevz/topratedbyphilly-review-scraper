#!/bin/bash
while getopts csv:engine: flag
do
    case "${flag}" in
        csv) INPUT=${OPTARG};;
        engine) ENGINE=${OPTARG};;
    esac
done

OLDIFS=$IFS
IFS=','
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
while read id url
do
	echo "id : $id"
	echo "url : $url"
	echo "/var/www/html/topratedbyphilly/scraper/venv-scraper/bin/python /var/www/html/topratedbyphilly/scraper/scrape.py --module=images --engine=$ENGINE --image_save_path=/var/www/html/topratedbyphilly/scraper/tmp/images/$ENGINE/$id --url=$url"
done < $INPUT
IFS=$OLDIFS
