#!/bin/bash


while getopts 'f:' flag; do
  case "${flag}" in
    f) flags="${OPTARG}" ;;
    *) print_usage
       exit 1 ;;
  esac
done
unzip Open_Da1.zip
unzip Open_Da1.zip
unzip Open_Da1.zip 

if [ -d "Open_Data/" ] ; then
		cp -i Open_Data/Fonts/TW-Kai-*.ttf $HOME/.fonts
	else
		cp -i data/TW-Kai-*.ttf $HOME/.fonts
	fi
 sudo fc-cache -fv
