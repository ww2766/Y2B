#!/bin/bash

unzip Open_Da1.zip
unzip Open_Da2.zip
unzip Open_Da3.zip 

# if ~/.fonts dir not exist, then create it.
if [ ! -d "$HOME/.fonts" ] ; then
    mkdir $HOME/.fonts
    echo -e "create ~/.fonts/ \n"
fi
cp -i Open_Data/Fonts/alimamafa*.ttf $HOME/.fonts
sudo fc-cache -fv
