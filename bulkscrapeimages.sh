#!/bin/bash
while getopts c:e: flag
do
    case "${flag}" in
        c) INPUT=${OPTARG};;
        e) ENGINE=${OPTARG};;
    esac
done

OLDIFS=$IFS
IFS=','
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
while read id url
do
	echo "id : $id"
	echo "url : $url"
	scrape_cmd="/var/www/html/topratedbyphilly/scraper/venv-scraper/bin/python scrape.py --module=images --engine=$ENGINE --image_save_path=/var/www/html/topratedbyphilly/scraper/tmp/images/$ENGINE/$id/ --url=$url"
	eval $scrape_cmd
done < $INPUT
IFS=$OLDIFS
