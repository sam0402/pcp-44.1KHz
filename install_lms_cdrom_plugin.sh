#!/bin/busybox ash

. /etc/init.d/tc-functions
. /var/www/cgi-bin/pcp-functions

useBusybox
TARGET=`cat /etc/sysconfig/backup_device`
cd /mnt/$TARGET
echo cdrom-KERNEL.tcz >>onboot.lst
cd optional
wget https://raw.githubusercontent.com/sam0402/pcp-44.1KHz/master/cdrom-5.13.1-pcpEVL_44k.tcz
wget https://raw.githubusercontent.com/sam0402/pcp-44.1KHz/master/cdrom-5.13.1-pcpEVL_44k.tcz.md5.txt
wget https://raw.githubusercontent.com/sam0402/pcp-44.1KHz/master/cdrom-5.13.1-pcpEVL_48k.tcz
wget https://raw.githubusercontent.com/sam0402/pcp-44.1KHz/master/cdrom-5.13.1-pcpEVL_48k.tcz.md5.txt
tce-load -w -i pcp-cdda2wav.tcz
cd /mnt/$TARGET/slimserver/prefs/plugin/
wget -O - https://raw.githubusercontent.com/bpa-code/bpaplugins/master/CDplayer-linux-v111.ZIP | unzip -
