#!/bin/sh

# Version: 6.0.0 2019-10-29

. pcp-functions
. pcp-soundcard-functions  # reset needs soundcard functions too.

# Restore sparams variable value from pcp.cfg so it is not overwritten with default values
PARAM1="$SPARAMS1"
PARAM2="$SPARAMS2"
PARAM3="$SPARAMS3"
PARAM4="$SPARAMS4"
PARAM5="$SPARAMS5"

# Read original mmap value, so we only do something if value is changed
ORG_ALSA_PARAMS4=$(echo $ALSA_PARAMS | cut -d':' -f4 )

RESTART_REQUIRED=TRUE
unset REBOOT_REQUIRED

pcp_html_head "Write to pcp.cfg" "SBP" "15" "squeezelite.cgi"

pcp_banner
pcp_remove_query_string
pcp_httpd_query_string

#========================================================================================
# Reset configuration
#----------------------------------------------------------------------------------------
pcp_reset() {
	pcp_reset_config_to_defaults
}

#========================================================================================
# Restore configuration
#
# Note: Assumes a backup onto USB stick exists.
#----------------------------------------------------------------------------------------
pcp_restore() {
	pcp_mount_device sda1
	. /mnt/sda1/newpcp.cfg
	pcp_umount_device sda1
	pcp_save_to_config
}

#========================================================================================
# Update pcp.cfg to the latest version
#
# This will first create the latest version of pcp.cfg with default values, then,
# restore original values.
#----------------------------------------------------------------------------------------
pcp_update() {
	echo '<p class="info">[ INFO ] Copying pcp.cfg to /tmp...</p>'
	sudo cp $PCPCFG /tmp/pcp.cfg
	[ $? -ne 0 ] && echo '<p class="error">[ ERROR ] Error copying pcp.cfg to /tmp...</p>'
	echo '<p class="info">[ INFO ] Setting pcp.cfg to defaults...</p>'
	pcp_update_config_to_defaults
	echo '<p class="info">[ INFO ] Updating pcp.cfg with original values...</p>'
	. $PCPCFG
	. /tmp/pcp.cfg
	pcp_save_to_config
}

install_shutdown_monitor() {
	if [ ! -f $PACKAGEDIR/shutdown-monitor.tcz ]; then
		echo "Installing Shutdown Monitor"
		sudo -u tc pcp-load -r $PCP_REPO -w shutdown-monitor.tcz
		if -f $PACKAGEDIR/shutdown-monitor.tcz ]; then
			sudo -u tc pcp-load -i shutdown-monitor.tcz
			echo "shutdown-monitor.tcz" >> $ONBOOTLST
		fi
	else
		sed -i '/shutdown-monitor.tcz/d' $ONBOOTLST
		echo "shutdown-monitor.tcz" >> $ONBOOTLST
		sudo -u tc pcp-load -i shutdown-monitor.tcz
	fi
}

#========================================================================================
# Main
#----------------------------------------------------------------------------------------
pcp_table_top "Write to config"

case "$SUBMIT" in
	Save)
		if [ $MODE -ge $MODE_PLAYER ]; then
			ALSA_PARAMS=${ALSA_PARAMS1}:${ALSA_PARAMS2}:${ALSA_PARAMS3}:${ALSA_PARAMS4}:${ALSA_PARAMS5}
			[ $CLOSEOUT -eq 0 ] && CLOSEOUT=""
			[ $PRIORITY -eq 0 ] && PRIORITY=""
			[ $POWER_GPIO -eq 0 ] && POWER_GPIO=""
		fi
		[ $SQUEEZELITE = "no" ] && unset RESTART_REQUIRED
		echo '<p class="info">[ INFO ] Saving config file.</p>'
		pcp_save_to_config
		pcp_footer static >/tmp/footer.html
	;;
	Binary)
		SAVE=0
		case $SQBINARY in
			default)
				rm -f $TCEMNT/tce/squeezelite
				SAVE=1
			;;
			custom)
				if [ -f $TCEMNT/tce/squeezelite-custom ]; then
					rm -f $TCEMNT/tce/squeezelite; ln -s $TCEMNT/tce/squeezelite-custom $TCEMNT/tce/squeezelite
					SAVE=1
				else
					echo '<p class="error">[ ERROR ] Custom Squeezelite not found. Copy custom binary before setting this option.</p>'
				fi
			;;
		esac
		if [ $SAVE -eq 1 ]; then
			echo '<p class="info">[ INFO ] Saving config file.</p>'
			pcp_save_to_config
		fi
	;;
	Reset*)
		pcp_reset
	;;
	Restore*)
		pcp_restore
	;;
	Update*)
		pcp_update
	;;
	Highhz)
		unset RESTART_REQUIRED
		REBOOT_REQUIRED=1
		case $HIGHHZ in
			on)
				pcp_mount_bootpart_nohtml
				sed -i 's/v8_88/v8_96/' $CONFIGTXT
				pcp_umount_bootpart_nohtml
			;;
			off)
				pcp_mount_bootpart_nohtml
				sed -i 's/v8_96/v8_88/' $CONFIGTXT
				pcp_umount_bootpart_nohtml
			;;
		esac
		pcp_save_to_config
	;;
	Poweroff)
		unset RESTART_REQUIRED
		REBOOT_REQUIRED=1
		case $GPIOPOWEROFF in
			yes)
				pcp_mount_bootpart_nohtml
				sed -i '/dtoverlay=gpio-poweroff/d' $CONFIGTXT
				[ $GPIOPOWEROFF_HI = "yes" ] && ACTIVELOW="" || ACTIVELOW=",active_low=1"
				echo "dtoverlay=gpio-poweroff,gpiopin=${GPIOPOWEROFF_GPIO}${ACTIVELOW}" >> $CONFIGTXT
				pcp_umount_bootpart_nohtml
			;;
			no)
				pcp_mount_bootpart_nohtml
				sed -i '/dtoverlay=gpio-poweroff/d' $CONFIGTXT
				pcp_umount_bootpart_nohtml
			;;
		esac
		pcp_save_to_config
	;;
	Shutdown)
		unset RESTART_REQUIRED
		REBOOT_REQUIRED=1
		case $GPIOSHUTDOWN in
			yes)
				pcp_mount_bootpart_nohtml
				sed -i '/dtoverlay=gpio-shutdown/d' $CONFIGTXT
				[ $GPIOSHUTDOWN_HI = "yes" ] && ACTIVELOW="active_low=0" || ACTIVELOW="active_low=1"
				echo "dtoverlay=gpio-shutdown,gpio_pin=${GPIOSHUTDOWN_GPIO},${ACTIVELOW},gpio_pull=${GPIOSHUTDOWN_PU}" >> $CONFIGTXT
				pcp_umount_bootpart_nohtml
				install_shutdown_monitor
			;;
			no)
				pcp_mount_bootpart_nohtml
				sed -i '/dtoverlay=gpio-shutdown/d' $CONFIGTXT
				pcp_umount_bootpart_nohtml
				sed -i '/shutdown-monitor.tcz/d' $ONBOOTLST
			;;
		esac
		pcp_save_to_config
	;;
	Install-monitor)
		unset RESTART_REQUIRED
		install_shutdown_monitor
	;;
	*)
		echo '<p class="error">[ ERROR ] Invalid case argument.</p>'
	;;
esac

. $PCPCFG

if [ "$ALSAeq" = "yes" ] && [ "$OUTPUT" != "equal" ]; then
	STRING1='ALSA equalizer is enabled. In order to use it "equal" must be used in the OUTPUT box. Press [OK] to go back and change or [Cancel] to continue'
	SCRIPT1=squeezelite.cgi
	pcp_confirmation_required
fi

pcp_backup
pcp_table_middle
[ $RESTART_REQUIRED ] || pcp_redirect_button "Go Back" $FROM_PAGE 5
pcp_table_end
pcp_footer
pcp_copyright

sleep 1
[ $REBOOT_REQUIRED ] && pcp_reboot_required
[ $RESTART_REQUIRED ] && pcp_restart_required $FROM_PAGE

echo '</body>'
echo '</html>'