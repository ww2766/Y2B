#!/bin/bash

unzip Open_Da1.zip
unzip Open_Da2.zip
unzip Open_Da3.zip 

if [ -d "Open_Data/" ] ; then
		cp -i Open_Data/Fonts/TW-Kai-*.ttf $HOME/.fonts
	else
		cp -i data/TW-Kai-*.ttf $HOME/.fonts
	fi
 sudo fc-cache -fv
