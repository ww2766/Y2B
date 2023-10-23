#!/bin/bash

unzip Open_Da1.zip
unzip Open_Da2.zip
unzip Open_Da3.zip 

cp -i Open_Data/Fonts/TW-Kai-*.ttf $HOME/.fonts
sudo fc-cache -fv
