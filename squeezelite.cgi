#!/bin/sh

# Version: 6.0.0 2020-02-01

. pcp-functions
. pcp-rpi-functions
. pcp-soundcard-functions
. pcp-lms-functions

pcp_html_head "Squeezelite Settings" "SBP"

pcp_picoreplayers_toolbar
pcp_controls
pcp_banner
pcp_navigation

#========================================================================================
# Create Squeezelite command string
#----------------------------------------------------------------------------------------
STRING="${SQLT_BIN} "
[ x"" != x"$NAME" ]         && STRING="$STRING -n \"$NAME\""
[ x"" != x"$OUTPUT" ]       && STRING="$STRING -o $OUTPUT"
[ x"" != x"$ALSA_PARAMS" ]  && STRING="$STRING -a $ALSA_PARAMS"
[ x"" != x"$BUFFER_SIZE" ]  && STRING="$STRING -b $BUFFER_SIZE"
[ x"" != x"$_CODEC" ]       && STRING="$STRING -c $_CODEC"
[ x"" != x"$XCODEC" ]       && STRING="$STRING -e $XCODEC"
[ x"" != x"$PRIORITY" ]     && STRING="$STRING -p $PRIORITY"
[ x"" != x"$MAX_RATE" ]     && STRING="$STRING -r $MAX_RATE"
[ x"" != x"$UPSAMPLE" ]     && STRING="$STRING -R $UPSAMPLE"
[ x"" != x"$MAC_ADDRESS" ]  && STRING="$STRING -m $MAC_ADDRESS"
[ x"" != x"$SERVER_IP" ]    && STRING="$STRING -s $SERVER_IP"
[ x"" != x"$LOGLEVEL" ]     && STRING="$STRING -d $LOGLEVEL -f ${LOGDIR}/pcp_squeezelite.log"
[ x"" != x"$DSDOUT" ]       && STRING="$STRING -D $DSDOUT"
[ "$VISUALISER" = "yes" ]   && STRING="$STRING -v"
[ x"" != x"$CLOSEOUT" ]     && STRING="$STRING -C $CLOSEOUT"
[ x"" != x"$UNMUTE" ]       && STRING="$STRING -U $UNMUTE"
[ x"" != x"$ALSAVOLUME" ]   && STRING="$STRING -V $ALSAVOLUME"
[ "$IR_LIRC" = "yes" ] && [ "$JIVELITE" != "yes" ] && STRING="$STRING -i $IR_CONFIG"
[ x"" != x"$POWER_GPIO" ]   && STRING="$STRING -G $POWER_GPIO:$POWER_OUTPUT"
[ x"" != x"$POWER_SCRIPT" ] && STRING="$STRING -S $POWER_SCRIPT"
[ x"" != x"$OTHER" ]        && STRING="$STRING $OTHER"

#========================================================================================
# Missing squeezelite options
#----------------------------------------------------------------------------------------
#  -M <modelname>	Set the squeezelite player model name sent to the server (default: SqueezeLite)
#  -N <filename>	Store player name in filename to allow server defined name changes to be shared between servers (not supported with -n)
#  -P <filename>	Store the process id (PID) in filename
#  -W				Read wave and aiff format from header, ignore server parameters
#  -X 				Use linear volume adjustments instead of in terms of dB (only for hardware volume control)
#  -z 				Daemonize
#  -Z <rate>		Report rate to server in helo as the maximum sample rate we can support
#----------------------------------------------------------------------------------------

#========================================================================================
# Routines
#----------------------------------------------------------------------------------------
pcp_cards_controls() {
	echo '                    <p><b>You have the following audio cards/controls:</b></p>'
	echo '                    <ul>'

	CARDNO=0
	for CARD in $(cat /proc/asound/card[0-9]/id)
	do
		amixer -c $CARD scontrols | awk -F"'" '{printf "\047%s\047\n", $2}' |
		while read MCONTROL; do
			amixer -c $CARD sget $MCONTROL | grep -q "volume"
			[ $? -eq 0 ] && echo '                      <li>Card '$CARDNO': '$CARD' - Control: '$(echo $MCONTROL | cut -d"'" -f2)'</li>'
		done
		CARDNO=$((CARDNO + 1))
	done

	echo '                    </ul>'
}

pcp_submit_button() {

	HELP_URL="diag_logs.cgi?SELECTION=pcp_squeezelite_help.log&ACTION=Show"

	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td  class="column150">'
	echo '                  <input type="submit" name="SUBMIT" value="Save" title="Save &quot;Squeezelite settings&quot; to configuration file, and restart squeezelite." onclick="return(validate());">'
	echo '                  <input type="hidden" name="FROM_PAGE" value="squeezelite.cgi">'
	echo '                </td>'

	if [ $MODE -ge $MODE_PLAYER ]; then
		echo '                <td colspan="2">'
		echo '                  <p>Squeezelite command string&nbsp;&nbsp;'
		echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
		echo '                  </p>'
		echo '                  <div id="'$ID'" class="less">'
		echo '                    <p><b>Warning: </b>For advanced users only!</p>'
		echo '                    <p>'$STRING'</p>'
		echo '                    <p>For more information&#8212;see <a href="'$HELP_URL'">Squeezelite help</a>.</p>'
		echo '                  </div>'
		echo '                </td>'
	fi
	echo '              </tr>'
}
#----------------------------------------------------------------------------------------

#========================================================================================
# Determine which sound cards are available for the various RPi boards
# PROBLEM???: See routines below. If RPi model is unknown, RP_MODEL will be set twice???
#----------------------------------------------------------------------------------------
if [ $(pcp_rpi_is_hat) -ne 0 ]; then
	# RPi is P5-connetion no HAT model or unknown
	RP_MODEL=ALL_NO_HAT
fi

if [ $(pcp_rpi_is_hat) -eq 0 ]; then
	# RPi is 40 pin HAT model
	RP_MODEL=HAT_ALL
fi

# Mode is beta and all models will be shown
[ $MODE -ge $MODE_BETA -o $(pcp_rpi_model_unknown) -eq 0 ] && RP_MODEL=ALL

#========================================================================================
# Populate sound card drop-down options
#----------------------------------------------------------------------------------------
pcp_sound_card_dropdown

echo '<script>'
echo '  function load_defaults() {'
echo '    var sel = document.getElementById("audiocard");'
echo '    var card = sel.options[sel.selectedIndex].text;'
echo '    if (confirm("Load default Alsa parameters, when selecting " + card + "?\nNote: <Cancel> = No")) {'
echo '      document.setaudio.save_out.value="yes";'
echo '    } else {'
echo '      document.setaudio.save_out.value="no";'
echo '    }'
echo '  }'
echo '</script>'

pcp_debug_variables "html" RP_MODEL 

#========================================================================================
# Start Audio output table
#----------------------------------------------------------------------------------------
echo '<table class="bggrey">'
echo '  <tr>'
echo '    <td>'
echo '      <form name="setaudio" action="chooseoutput.cgi" method="get" id="setaudio">'
echo '        <div class="row">'
echo '          <fieldset>'
echo '            <legend>Audio output device settings</legend>'
echo '            <table class="bggrey percent100">'
#--------------------------------------Audio output-------------------------------
pcp_incr_id
pcp_start_row_shade
echo '              <tr class="'$ROWSHADE'">'
echo '                <td class="column150">'
echo '                  <input id="save_out" type="submit"'
echo '                         name="DEFAULTS"'
echo '                         value="Save"'
echo '                         title="Save &quot;Audio output&quot; to configuration file"'
[ $MODE -ge $MODE_DEVELOPER ] && echo '                         onclick=load_defaults();'
echo '                   >'
echo '                </td>'
echo '                <td class="column250">'
echo '                  <select class="large16" id="audiocard" name="AUDIO">'

cat /tmp/dropdown.cfg | grep $RP_MODEL | sed 's/notselected//' | awk -F: '{ print "<option value=\""$1"\" "$2">"$3"</option>"}'

echo '                  </select>'
echo '                </td>'
echo '                <td>'
echo '                  <p><b>Do this First:</b> Select Audio output, then press [ Save ]&nbsp;&nbsp;'
echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
echo '                  </p>'
echo '                  <div id="'$ID'" class="less">'
echo '                    <p>Set Audio output before changing Squeezelite settings below.</p>'
echo '                    <p><b>Note: </b>This will overwrite some default values of the Squeezelite settings below. You may need to reset them.</p>'
echo '                  </div>'
echo '                </td>'
echo '              </tr>'
pcp_selected_soundcontrol
if [ x"" != x"$CONTROL_PAGE" ]; then
	[ -f $REBOOT_PENDING ] && CNTRL_DISABLED="disabled" || CNTRL_DISABLED=""
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <input type="button" value="Card Control" onClick="location.href='\'''$CONTROL_PAGE''\''" '$CNTRL_DISABLED'>'
	echo '                </td>'
	echo '                <td colspan="2">'
	[ -f $REBOOT_PENDING ] &&
	echo '                  <p>Audio Hardware and Mixer settings are disabled until reboot&nbsp;&nbsp;'|| echo '                  <p>Audio Hardware and Mixer settings&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>Setup and card specific hardware or mixer options on this page.</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
fi
#----------------------------------------------------------------------------------------
echo '            </table>'
echo '          </fieldset>'
echo '        </div>'
echo '      </form>'
echo '    </td>'
echo '  </tr>'
#----------------------------------------------------------------------------------------

. $PCPCFG

#========================================================================================
# Start Squeezelite settings table
#----------------------------------------------------------------------------------------
echo '  <tr>'
echo '    <td>'
echo '      <form name="squeeze" action="writetoconfig.cgi" method="get">'
echo '        <div class="row">'
echo '          <fieldset>'
echo '            <legend>Change Squeezelite settings</legend>'
echo '            <table class="bggrey percent100">'
#----------------------------------------------------------------------------------------
pcp_submit_button
#--------------------------------------Name of your player-------------------------------
pcp_incr_id
pcp_toggle_row_shade
echo '              <tr class="'$ROWSHADE'">'
echo '                <td class="column150">'
echo '                  <p>Name of your player</p>'
echo '                </td>'
echo '                <td class="column210">'
echo '                  <input class="large15"'
echo '                         type="text"'
echo '                         name="NAME"'
echo '                         value="'$NAME'"'
echo '                         required'
echo '                         title="Invalid characters: $ &amp; ` / &quot;"'
echo '                         pattern="[^$&`/\x22]+"'
echo '                  >'
echo '                </td>'
echo '                <td>'
echo '                  <p>Specify the piCorePlayer name (-n)&nbsp;&nbsp;'
echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
echo '                  </p>'
echo '                  <div id="'$ID'" class="less">'
echo '                    <p>&lt;name&gt;</p>'
echo '                    <p>This is the player name that will be used by LMS, it will appear in the web interface and apps.'
echo '                       It is recommended that you use standard alphanumeric characters for maximum compatibility.</p>'
echo '                    <p><b>Examples:</b></p>'
echo '                    <ul>'
echo '                      <li>piCorePlayer2</li>'
echo '                      <li>Main Stereo</li>'
echo '                      <li>Bed Room</li>'
echo '                    </ul>'
echo '                    <p><b>Invalid characters:</b> $ & ` / &quot;</p>'
echo '                  </div>'
echo '                </td>'
echo '              </tr>'
#----------------------------------------------------------------------------------------

#--------------------------------------Output settings-----------------------------------
case "$ALSAeq" in
	yes) READONLY="readonly" ;;
	*)   READONLY="" ;;
esac

pcp_incr_id
pcp_toggle_row_shade
echo '              <tr class="'$ROWSHADE'">'
echo '                <td class="column150">'
echo '                  <p>Output setting</p>'
echo '                </td>'
echo '                <td class="column210">'
echo '                  <input id="input'$ID'"'
echo '                         class="large15"'
echo '                         type="text"'
echo '                         name="OUTPUT"'
echo '                         value="'$OUTPUT'"'
echo '                         '$READONLY
echo '                         title="Select from list of output devices"'
echo '                         pattern="[a-zA-Z0-9:,=]*"'
echo '                  >'
echo '                </td>'
echo '                <td>'

if [ "$ALSAeq" = "yes" ]; then
	echo '                  <a hidden id="equal">equal</a>'
	echo '                  <p><b>Note:</b> ALSA equalizer: Output must be set to "equal".  Click <a href=# onclick="pcp_copy_click_to_input('\'input${ID}\',\'equal\'')">HERE</a> if not.</p>'
else
	echo '                  <p>Specify the output device (-o)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;output device&gt;</p>'
	echo '                    <ul>'
	echo '                      <li>Default: default</li>'
	echo '                      <li>- = output to stdout</li>'
	echo '                    </ul>'
	echo '                    <p>Available output devices (click to use):</p>'
	echo '                    <p>  hw: devices are normally the best choice, but try and decide for yourself:</p>'
	echo '                    <ul>'

	OPTION=1
	OUT_DEVICES=$(aplay -L | grep -v '^  ' | grep -E -v 'dmix|dsnoop')
	for OD in $OUT_DEVICES; do
		echo '                      <li class="pointer" title="Click to use" onclick="pcp_copy_click_to_input('\'input${ID}\',\'option${OPTION}\'')">'
		echo '                        <span id="option'${OPTION}'">'$OD'</span></li>'
		OPTION=$((OPTION + 1))
	done

	echo '                    </ul>'
	echo '                    <p><b>Note:</b></p>'
	echo '                    <ul>'
	echo '                      <li>Some hardware requires the use of "hw", rather than "sysdefault" i.e. hw:CARD=DAC</li>'
	echo '                      <li>Sometimes clearing this field completely may help. This forces the default ALSA setting to be used.</li>'
	echo '                      <li>Using ALSA equalizer will set the output to "equal".</li>'
	echo '                    </ul>'
	echo '                  </div>'
fi

echo '                </td>'
echo '              </tr>'
#----------------------------------------------------------------------------------------

#--------------------------------------ALSA settings-------------------------------------
pcp_squeezelite_alsa() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p>ALSA setting</p>'
	echo '                </td>'
	echo '                <td class="column240">'

	                        ALSA_PARAMS1=$(echo $ALSA_PARAMS | cut -d: -f1 )		# b = buffer time in ms or size in bytes
	                        ALSA_PARAMS2=$(echo $ALSA_PARAMS | cut -d: -f2 )		# p = period count or size in bytes
	                        ALSA_PARAMS3=$(echo $ALSA_PARAMS | cut -d: -f3 )		# f = sample format (16|24|24_3|32)
	                        ALSA_PARAMS4=$(echo $ALSA_PARAMS | cut -d: -f4 )		# m = use mmap (0|1)
	                        ALSA_PARAMS5=$(echo $ALSA_PARAMS | cut -d: -f5 )		# d = opens ALSA twice

	echo '                  <input class="small4"'
	echo '                         type="text"'
	echo '                         name="ALSA_PARAMS1"'
	echo '                         value="'$ALSA_PARAMS1'"'
	echo '                         title="buffer time"'
	echo '                         pattern="\d*"'
	echo '                  >'
	echo '                  <input class="small3"'
	echo '                         type="text"'
	echo '                         name="ALSA_PARAMS2"'
	echo '                         value="'$ALSA_PARAMS2'"'
	echo '                         title="period count"'
	echo '                         pattern="\d*"'
	echo '                  >'
	echo '                  <input class="small3"'
	echo '                         type="text"'
	echo '                         name="ALSA_PARAMS3"'
	echo '                         value="'$ALSA_PARAMS3'"'
	echo '                         title="sample format ( 16 | 24 | 24_3 | 32 )"'
	echo '                         pattern="16|24_3|24|32"'
	echo '                  >'
	echo '                  <input class="small1"'
	echo '                         type="text"'
	echo '                         name="ALSA_PARAMS4"'
	echo '                         value="'$ALSA_PARAMS4'"'
	echo '                         title="mmap ( 0 | 1 )"'
	echo '                         pattern="[0-1]"'
	echo '                  >'
	echo '                  <input class="small1"'
	echo '                         type="text"'
	echo '                         name="ALSA_PARAMS5"'
	echo '                         value="'$ALSA_PARAMS5'"'
	echo '                         title="ALSA twice (d)"'
	echo '                         pattern="[d]"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Specify the ALSA params to open output device (-a)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;b&gt;:&lt;p&gt;:&lt;f&gt;:&lt;m&gt;:&lt;d&gt;</p>'
	echo '                    <ul>'
	echo '                      <li>b = buffer time in ms or size in bytes</li>'
	echo '                      <li>p = period count or size in bytes</li>'
	echo '                      <li>f = sample format (16|24|24_3|32)</li>'
	echo '                      <li>m = use mmap (0|1)</li>'
	echo '                      <li>d = opens ALSA twice (undocumented) i.e. ::::d</li>'
	echo '                    </ul>'
	echo '                    <p><b>Note:</b></p>'
	echo '                    <p>Buffer value &lt; 500 treated as buffer time in ms, otherwise size in bytes.</p>'
	echo '                    <p>Period value &lt; 50 treated as period count, otherwise size in bytes.</p>'
	echo '                    <p>mmap = memory map<p>'
	echo '                    <p><b>Sample format:</b><p>'
	echo '                    <ul>'
	echo '                      <li>16 = Signed 16 bit Little Endian</li>'
	echo '                      <li>24 = Signed 24 bit Little Endian using low 3 bytes in 32 bit word</li>'
	echo '                      <li>24_3 = Signed 24 bit Little Endian in 3 bytes format</li>'
	echo '                      <li>32 = Signed 32 bit Big Endian</li>'
	echo '                    </ul>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'

	if [ $DEBUG -eq 1 ]; then
		echo '<!-- Start of debug info -->'
		echo '              <tr class="'$ROWSHADE'">'
		echo '                <td class="column150">'
		echo '                </td>'
		echo '                <td class="column210">'
		echo '                  <input class="large15" type="text" name="ALSA_PARAMS" value="'$ALSA_PARAMS'" readonly>'
		echo '                </td>'
		echo '                <td>'
		echo '                </td>'
		echo '              </tr>'
		echo '<!-- END of debug info -->'
	fi
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_alsa
#----------------------------------------------------------------------------------------

#--------------------------------------Buffer size settings------------------------------
pcp_squeezelite_buffer() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p>Buffer size settings</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="BUFFER_SIZE"'
	echo '                         value="'$BUFFER_SIZE'"'
	echo '                         title="buffer size"'
	echo '                         pattern="\d+:\d+"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Specify internal Stream and Output buffer sizes in Kb (-b)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;stream&gt;:&lt;output&gt;</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_buffer
#----------------------------------------------------------------------------------------

#--------------------------------------Codec settings------------------------------------
pcp_squeezelite_codec() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p>Restrict codec setting</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="_CODEC"'
	echo '                         value="'$_CODEC'"'
	echo '                         title="Restrict codec. Valid: dsd,flac,pcm,mp3,ogg,aac,wma,alac,mad,mpg"'
	echo '                         pattern="[dsd|flac|pcm|mp3|ogg|aac|wma|alac|mad|mpg]+(,[dsd|flac|pcm|mp3|ogg|aac|wma|alac|mad|mpg]+)*"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Restrict codecs to those specified, otherwise load all available codecs (-c)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;codec1,codec2&gt;</p>'
	echo '                    <p>Known codecs:</p>'
	echo '                    <ul>'
	echo '                      <li>flac</li>'
	echo '                      <li>pcm</li>'
	echo '                      <li>mp3</li>'
	echo '                      <li>ogg</li>'
	echo '                      <li>aac</li>'
	echo '                      <li>wma</li>'
	echo '                      <li>alac</li>'
	echo '                      <li>dsd</li>'
	echo '                      <li>mad, mpg for specific mp3 codec.</li>'
	echo '                    </ul>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_codec
#----------------------------------------------------------------------------------------

#--------------------------------------Exclude Codec settings----------------------------
pcp_squeezelite_xcodec() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p>Exclude codec setting</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="XCODEC"'
	echo '                         value="'$XCODEC'"'
	echo '                         title="Exclude codec. Valid: dsd,flac,pcm,mp3,ogg,aac,wma,alac,mad,mpg"'
	echo '                         pattern="[dsd|flac|pcm|mp3|ogg|aac|wma|alac|mad|mpg]+(,[dsd|flac|pcm|mp3|ogg|aac|wma|alac|mad|mpg]+)*"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Explicitly exclude native support for one or more codecs (-e)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;codec1,codec2&gt;</p>'
	echo '                    <p>Known codecs:</p>'
	echo '                    <ul>'
	echo '                      <li>flac</li>'
	echo '                      <li>pcm</li>'
	echo '                      <li>mp3</li>'
	echo '                      <li>ogg</li>'
	echo '                      <li>aac</li>'
	echo '                      <li>wma</li>'
	echo '                      <li>alac</li>'
	echo '                      <li>dsd</li>'
	echo '                      <li>mad, mpg for specific mp3 codec</li>'
	echo '                    </ul>'
	echo '                    <p><b>Example: </b>dsd</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_xcodec
#----------------------------------------------------------------------------------------

#--------------------------------------Priority setting----------------------------------
pcp_squeezelite_priority() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Priority setting</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="number"'
	echo '                         name="PRIORITY"'
	echo '                         value="'$PRIORITY'"'
	echo '                         min="0"'
	echo '                         max="99"'
	echo '                         title="Priority ( 0 - 99 )"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Set real time priority of output thread (-p)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;priority&gt;</p>'
	echo '                    <p>Range: 0-99</p>'
	echo '                    <p>Default: 45</p>'
	echo '                    <p>Select 0 to let Squeezelite determine the priority.</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_priority
#----------------------------------------------------------------------------------------

#--------------------------------------Max sample rate-----------------------------------
pcp_squeezelite_max_sample() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Max sample rate</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="MAX_RATE"'
	echo '                         value="'$MAX_RATE'"'
	echo '                         title="Max sample rate"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Sample rates supported, allows output to be off when Squeezelite is started (-r)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;rates&gt;[:&lt;delay&gt;]</p>'
	echo '                    <ul>'
	echo '                      <li>rates = &lt;maxrate&gt;|&lt;minrate&gt;-&lt;maxrate&gt;|&lt;rate1&gt;,&lt;rate2&gt;,&lt;rate3&gt;</li>'
	echo '                      <li>delay = optional delay switching rates in ms</li>'
	echo '                    </ul>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_max_sample
#----------------------------------------------------------------------------------------

#--------------------------------------Upsample settings---------------------------------
pcp_squeezelite_upsample_settings() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Upsample setting</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="UPSAMPLE"'
	echo '                         value="'$UPSAMPLE'"'
	echo '                         title="Upsample settings"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Resampling parameters (-R)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;recipe&gt;:&lt;flags&gt;:&lt;attenuation&gt;:&lt;precision&gt;:<br />'
	echo '                       &lt;passband_end&gt;:&lt;stopband_start&gt;:&lt;phase_response&gt;</p>'
	echo '                    <ul>'
	echo '                      <li>recipe = (v|h|m|l|q)(L|I|M)(s) [E|X]'
	echo '                        <ul>'
	echo '                          <li>E = exception - resample only if native rate not supported</li>'
	echo '                          <li>X = async - resample to max rate for device, otherwise to max sync rate</li>'
	echo '                        </ul>'
	echo '                      </li>'
	echo '                      <li>flags = num in hex</li>'
	echo '                      <li>attenuation = attenuation in dB to apply (default is -1db if not explicitly set)</li>'
	echo '                      <li>precision = number of bits precision (HQ = 20. VHQ = 28)</li>'
	echo '                      <li>passband_end = number in percent (0dB pt. bandwidth to preserve. nyquist = 100%)</li>'
	echo '                      <li>stopband_start = number in percent (Aliasing/imaging control. > passband_end)</li>'
	echo '                      <li>phase_response = 0-100 (0 = minimum / 50 = linear / 100 = maximum)</li>'
	echo '                    </ul>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_upsample_settings
#----------------------------------------------------------------------------------------

#--------------------------------------MAC address---------------------------------------
pcp_squeezelite_mac_address() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">MAC address</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="MAC_ADDRESS"'
	echo '                         value="'$MAC_ADDRESS'"'
	echo '                         title="MAC address"'
	echo '                         pattern="([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Set MAC address (-m)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;mac addr&gt;</p>'
	echo '                    <p>Format: ab:cd:ef:12:34:56</p>'
	echo '                    <p>This is used if you want to use a fake MAC address or you want to overwrite the default MAC address determined by Squeezelite.'
	echo '                       Usually you will not need to set a MAC address.</p>'
	echo '                    <p>By default Squeezelite will use one of the following MAC addresses:</p>'
	echo '                    <ul>'
	echo '                      <li>Physical MAC address: '$(pcp_eth0_mac_address)'</li>'
	echo '                      <li>Wireless MAC address: '$(pcp_wlan0_mac_address)'</li>'
	echo '                    </ul>'
	echo '                    <p><b>Note: </b>Squeezelite will ignore MAC addresses from the range 00:04:20:**:**:**</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_mac_address
#----------------------------------------------------------------------------------------

#--------------------------------------Squeezelite server IP-----------------------------
pcp_squeezelite_server_ip() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">LMS IP</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="SERVER_IP"'
	echo '                         value="'$SERVER_IP'"'
	echo '                         title="Logitech Media Server (LMS) IP"'
	echo '                         pattern="\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\:\d{1,5})?"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Connect to the specified LMS, otherwise autodiscovery will find the server (-s)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;server&gt;[:&lt;port&gt;]</p>'
	echo '                    <p>Default port: 3483</p>'
	echo '                    <p class="error"><b>Note:</b> Do not include the port number unless you have changed the default LMS port number.</p>'
	                          if [ "$LMSERVER" = "no" ]; then
	echo   '                    <p>Current LMS IP is:</p>'
	echo   '                    <ul>'
	echo   '                      <li>'$(pcp_lmsip)'</li>'
	echo   '                    </ul>'
	                          else
	echo   '                    <p>You have LMS enabled, if you also want to listen to music from this LMS on this pCP then use:</p>'
	echo   '                    <ul>'
	echo   '                      <li><b>127.0.0.1</b> in the LMS IP field</li>'
	echo   '                    </ul>'
	                          fi
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_server_ip
#----------------------------------------------------------------------------------------

#--------------------------------------Log level setting---------------------------------
pcp_squeezelite_log_level() {
	case "$LOGLEVEL" in
		all=info)         LOGLEVEL1="selected" ;;
		all=debug)        LOGLEVEL2="selected" ;;
		all=sdebug)       LOGLEVEL3="selected" ;;
		slimproto=info)   LOGLEVEL4="selected" ;;
		slimproto=debug)  LOGLEVEL5="selected" ;;
		slimproto=sdebug) LOGLEVEL6="selected" ;;
		stream=info)      LOGLEVEL7="selected" ;;
		stream=debug)     LOGLEVEL8="selected" ;;
		stream=sdebug)    LOGLEVEL9="selected" ;;
		decode=info)      LOGLEVEL10="selected" ;;
		decode=debug)     LOGLEVEL11="selected" ;;
		decode=sdebug)    LOGLEVEL12="selected" ;;
		output=info)      LOGLEVEL13="selected" ;;
		output=debug)     LOGLEVEL14="selected" ;;
		output=sdebug)    LOGLEVEL15="selected" ;;
		ir=info)          LOGLEVEL16="selected" ;;
		ir=debug)         LOGLEVEL17="selected" ;;
		ir=sdebug)        LOGLEVEL18="selected" ;;
		*)                LOGLEVEL0="selected" ;;
	esac

	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Log level setting</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <select class="large16" name="LOGLEVEL" title="Log level setting">'
	echo '                    <option value="" '$LOGLEVEL0'>none</option>'
	echo '                    <option value="all=info" '$LOGLEVEL1'>all=info</option>'
	echo '                    <option value="all=debug" '$LOGLEVEL2'>all=debug</option>'
	echo '                    <option value="all=sdebug" '$LOGLEVEL3'>all=sdebug</option>'
	echo '                    <option value="slimproto=info" '$LOGLEVEL4'>slimproto=info</option>'
	echo '                    <option value="slimproto=debug" '$LOGLEVEL5'>slimproto=debug</option>'
	echo '                    <option value="slimproto=sdebug" '$LOGLEVEL6'>slimproto=sdebug</option>'
	echo '                    <option value="stream=info" '$LOGLEVEL7'>stream=info</option>'
	echo '                    <option value="stream=debug" '$LOGLEVEL8'>stream=debug</option>'
	echo '                    <option value="stream=sdebug" '$LOGLEVEL9'>stream=sdebug</option>'
	echo '                    <option value="decode=info" '$LOGLEVEL10'>decode=info</option>'
	echo '                    <option value="decode=debug" '$LOGLEVEL11'>decode=debug</option>'
	echo '                    <option value="decode=sdebug" '$LOGLEVEL12'>decode=sdebug</option>'
	echo '                    <option value="output=info" '$LOGLEVEL13'>output=info</option>'
	echo '                    <option value="output=debug" '$LOGLEVEL14'>output=debug</option>'
	echo '                    <option value="output=sdebug" '$LOGLEVEL15'>output=sdebug</option>'
	echo '                    <option value="ir=info" '$LOGLEVEL16'>ir=info</option>'
	echo '                    <option value="ir=debug" '$LOGLEVEL17'>ir=debug</option>'
	echo '                    <option value="ir=sdebug" '$LOGLEVEL18'>ir=sdebug</option>'
	echo '                  </select>'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Set logging level (-d)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;log&gt;=&lt;level&gt;</p>'
	echo '                    <ul>'
	echo '                      <li>log: all|slimproto|stream|decode|output|ir</li>'
	echo '                      <li>level: info|debug|sdebug</li>'
	echo '                    </ul>'
	echo '                    <p><b>Note:</b> Log file is /var/log/pcp_squeezelite.log</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_log_level
#----------------------------------------------------------------------------------------

#------------------------------------Device supports DSD/DoP-----------------------------
pcp_squeezelite_dop() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Device supports DSD/DoP</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="DSDOUT"'
	echo '                         value="'$DSDOUT'"'
	echo '                         title="delay:format"'
	echo '                         pattern="^\d+((:dop)|(:u8)|(:u16le)|(:u16be)|(:u32le)|(:u32be))?"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Output device supports native DSD (-D)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;delay&gt;:&lt;format&gt;</p>'
	echo '                    <p>delay = optional delay switching between PCM and DoP in ms.</p>'
	echo '                    <p>format = dop (default if not specified), u8, u16le, u16be, u32le or u32be.</p>'
	echo '                    <p><b>Note: </b>LMS requires the DoP patch applied.</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $(pcp_squeezelite_build_option DSD) -eq 0 -a $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_dop || DSDOUT=""
#----------------------------------------------------------------------------------------

#--------------------------------------Close output setting------------------------------
pcp_squeezelite_close_output() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Close output setting</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="number"'
	echo '                         name="CLOSEOUT"'
	echo '                         value="'$CLOSEOUT'"'
	echo '                         title="Close output delay"'
	echo '                         min="0"'
	echo '                         max="1000"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Set idle time before Squeezelite closes output (-C)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;timeout&gt;</p>'
	echo '                    <p>Value in seconds.</p>'
	echo '                    <p>Close output device when idle after timeout seconds, default is to keep it open while player is on.</p>'
	echo '                    <p>Select 0 to keep it open while player is on.</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_close_output
#----------------------------------------------------------------------------------------

#--------------------------------------Unmute ALSA control-------------------------------
pcp_squeezelite_unmute() {
	case "$UNMUTE" in
		PCM) UNMUTEYES="checked" ;;
		*) UNMUTENO="checked" ;;
	esac

	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Unmute ALSA control</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="UNMUTE"'
	echo '                         value="'$UNMUTE'"'
	echo '                         title="Unmute ALSA control"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Set ALSA control to unmute and set to full volume (-U)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;control&gt;</p>'
	echo '                    <p>Unmute ALSA control and set to full volume.</p>'
	echo '                    <p><b>Note:</b> Not supported with -V option.</p>'
	pcp_cards_controls
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_unmute
#----------------------------------------------------------------------------------------

#--------------------------------------ALSA volume control-------------------------------
pcp_squeezelite_volume() {
	case "$ALSAVOLUME" in
		PCM) ALSAVOLUMEYES="checked" ;;
		*) ALSAVOLUMENO="checked" ;;
	esac

	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">ALSA volume control</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="ALSAVOLUME"'
	echo '                         value="'$ALSAVOLUME'"'
	echo '                         title="ALSA volume control"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Set ALSA control for volume adjustment (-V)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;control&gt;</p>'
	echo '                    <p>Use ALSA control for volume adjustment otherwise use software volume adjustment.</p>'
	echo '                    <p>Select and use the appropiate name of the possible controls from the list below.</p>'
	echo '                    <p><b>Note:</b> Not supported with -U option.</p>'
	pcp_cards_controls
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER -a "$CARD" != "RPiCirrus" ] && pcp_squeezelite_volume
#----------------------------------------------------------------------------------------

#--------------------------------------Power On/Off GPIO---------------------------------
pcp_squeezelite_power_gpio() {
	if [ -n "$POWER_GPIO" ]; then
		case "$POWER_OUTPUT" in
			H) POH="checked" ;;
			L) POL="checked" ;;
		esac
	fi

	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Power On/Off GPIO</p>'
	echo '                </td>'
	echo '                <td class="column220">'
	echo '                  <p>'
	echo '                    <input class="large15"'
	echo '                           type="number"'
	echo '                           name="POWER_GPIO"'
	echo '                           value="'$POWER_GPIO'"'
	echo '                           title="Power On/Off GPIO"'
	echo '                           min="0"'
	echo '                           max="40"'
	echo '                    >'
	echo '                  </p>'
	echo '                  <input id="pow1" type="radio" name="POWER_OUTPUT" value="H" title="Set GPIO active high" '$POH'>'
	echo '                  <label for="pow1">Active High&nbsp;&nbsp;</label>'
	echo '                  <input id="pow2" type="radio" name="POWER_OUTPUT" value="L" '$POL'>'
	echo '                  <label for="pow2">Active Low</label>'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Power On/Off GPIO (-G)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;gpio&gt;:&lt;H|L&gt;</p>'
	echo '                    <p>Squeezelite will toggle this GPIO when the Power On/Off button is pressed.</p>'
	echo '                    <p>H or L to tell Squeezlite if the output should be active High or Low.</p>'
	echo '                    <p>Select 0 to tell Squeezlite not to toggle any GPIO.</p>'
	echo '                    <p class="error"><b>WARNING:</b></p>'
	echo '                    <p class="error">Use caution when connecting to GPIOs. PERMANENT damage can occur.</p>'
	echo '                    <p class="error">If using mains voltages ensure you are FULLY QUALIFIED. DEATH can occur.</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && [ $(pcp_squeezelite_build_option GPIO ) -eq 0 ] && pcp_squeezelite_power_gpio
#----------------------------------------------------------------------------------------

#--------------------------------------Power On/Off Script-------------------------------
pcp_squeezelite_power_script() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Power On/Off Script</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="POWER_SCRIPT"'
	echo '                         value="'$POWER_SCRIPT'"'
	echo '                         title="Power On/Off script"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Power On/Off Script (-S)&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>&lt;/path/script.sh&gt;</p>'
	echo '                    <p>Squeezelite will run this script when the Power On/Off button is pressed.</p>'
	echo '                    <p class="error"><b>WARNING:</b></p>'
	echo '                    <p class="error">Use caution when connecting to GPIOs. PERMANENT damage can occur.</p>'
	echo '                    <p class="error">If using mains voltages ensure you are FULLY QUALIFIED. DEATH can occur.</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && [ $(pcp_squeezelite_build_option GPIO) -eq 0 ] && pcp_squeezelite_power_script
#----------------------------------------------------------------------------------------

#--------------------------------------Various input-------------------------------------
pcp_squeezelite_various_input() {
	pcp_incr_id
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <p class="row">Various Options</p>'
	echo '                </td>'
	echo '                <td class="column210">'
	echo '                  <input class="large15"'
	echo '                         type="text"'
	echo '                         name="OTHER"'
	echo '                         value="'$OTHER'"'
	echo '                         title="Add your other input"'
	echo '                  >'
	echo '                </td>'
	echo '                <td>'
	echo '                  <p>Add another option&nbsp;&nbsp;'
	echo '                    <a id="'$ID'a" class="moreless" href=# onclick="return more('\'''$ID''\'')">more></a>'
	echo '                  </p>'
	echo '                  <div id="'$ID'" class="less">'
	echo '                    <p>Use this field to add options that are supported by Squeezelite but unavailable in the piCorePlayer web interface.</p>'
	echo '                    <p><b>Note: </b>Ensure to include the correct switch first, i.e. -n or -o etc</p>'
	echo '                    <p><b>Example: </b>-W -X -Z</p>'
	echo '                  </div>'
	echo '                </td>'
	echo '              </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_various_input
#----------------------------------------------------------------------------------------
pcp_submit_button
#----------------------------------------------------------------------------------------
echo '            </table>'
echo '          </fieldset>'
echo '        </div>'
echo '      </form>'
echo '    </td>'
echo '  </tr>'
#----------------------------------------------------------------------------------------

#========================================================================================
# Javascript for form validation
#----------------------------------------------------------------------------------------
echo '<script>'
echo 'function validate() {'
echo '    if (document.squeeze.POWER_SCRIPT.value != "" && document.squeeze.POWER_GPIO.value != ""){'
echo '      alert("Power GPIO and Power Script must not be\ndefined at the same time.");'
echo '      return false;'
echo '    }'
echo '    return ( true );'
echo '}'
echo '</script>'

#========================================================================================
# Select Squeezelite binary.  Support custom versions of squeezelite.
#----------------------------------------------------------------------------------------
pcp_squeezelite_binary() {
	DEFyes=""
	CUSTOMyes=""
	# Check to make sure this is really a symlink before we allow setting via web
	[ -f $TCEMNT/tce/squeezelite -a "$(readlink $TCEMNT/tce/squeezelite)" = "" ] && DISABLE="disabled" || DISABLE=""
	case $SQBINARY in
		pcm) PCMyes="checked"; break;;
		dsd) DSDyes="checked"; break;;
		custom) CUSTOMyes="checked"; break;;
		*) DEFyes="checked";;
	esac

	echo '  <tr>'
	echo '    <td>'
	echo '      <form name="binary" action="writetoconfig.cgi" method="get">'
	echo '        <div class="row">'
	echo '          <fieldset>'
	echo '            <legend>Set Squeezelite Binary</legend>'
	echo '            <table class="bggrey percent100">'
	COL1="75"
	COL2="210"
	COL3="380"
	pcp_incr_id
	pcp_start_row_shade
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column'$COL1' center">'
	echo '                  <p><b>Enabled</b></p>'
	echo '                </td>'
	echo '                <td class="column'$COL2'">'
	echo '                  <p><b>Binary</b></p>'
	echo '                </td>'
	echo '                <td class="column'$COL3'">'
	echo '                  <p>Select your Squeezelite Binary&nbsp;&nbsp;</p>'
	echo '                </td>'
	echo '              </tr>'
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column'$COL1' center">'
	echo '                  <p>'
	echo '                    <input id="sqreg" type="radio" name="SQBINARY" value="default" '$DEFyes'>'
	echo '                    <label for="sqreg">&#8202;</label>'
	echo '                  <p>'
	echo '                </td>'
	echo '                <td class="column'$COL2'">'
	echo '                  <p>Default</p>'
	echo '                </td>'
	echo '                <td class="column'$COL1' center">'
	echo '                  <p>'
	echo '                    <input id="sqpcm" type="radio" name="SQBINARY" value="pcm" '$PCMyes'>'
	echo '                    <label for="sqpcm">&#8202;</label>'
	echo '                  <p>'
	echo '                </td>'
	echo '                <td class="column'$COL2'">'
	echo '                  <p>PCM&nbsp;Only</p>'
	echo '                </td>'
	echo '                <td class="column'$COL1' center">'
	echo '                  <p>'
	echo '                    <input id="sqdsd" type="radio" name="SQBINARY" value="dsd" '$DSDyes'>'
	echo '                    <label for="sqdsd">&#8202;</label>'
	echo '                  <p>'
	echo '                </td>'
	echo '                <td class="column'$COL2'">'
	echo '                  <p>PCM+DSD</p>'
	echo '                </td>'
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column'$COL1' center">'
	echo '                  <p>'
	echo '                   <input id="sqcust" type="radio" name="SQBINARY" value="custom" '$CUSTOMyes'>'
	echo '                   <label for="sqcust">&#8202;</label>'
	echo '                  <p>'
	echo '                </td>'
	echo '                <td class="column'$COL2'">'
	echo '                  <p>Custom Squeezelite</p>'
	echo '                </td>'
	echo '                <td class="column'$COL3'">'
	echo '                  <p>Save your file as '$TCEMNT'/tce/squeezelite-custom</p>'
	echo '                </td>'
	echo '              </tr>'
	#--------------------------------------Submit button---------------------------------
	pcp_toggle_row_shade
	echo '              <tr class="'$ROWSHADE'">'
	echo '                <td class="column150">'
	echo '                  <button type="submit" name="SUBMIT" value="Binary" title="Save &quot;Squeezelite Binary&quot; to configuration file" '$DISABLE'>Set Binary</button>'
	echo '                  <input type="hidden" name="FROM_PAGE" value="squeezelite.cgi">'
	echo '                </td>'
	echo '                <td colspan="2">'
	[ $DISABLE != "" ] &&
	echo '                  <p>There is a custom binary installed in the wrong location. (See custom setting above).</p>'
	echo '                </td>'
	echo '              </tr>'
	#------------------------------------------------------------------------------------
	echo '            </table>'
	echo '          </fieldset>'
	echo '        </div>'
	echo '      </form>'
	echo '    </td>'
	echo '  </tr>'
}
[ $MODE -ge $MODE_PLAYER ] && pcp_squeezelite_binary
#----------------------------------------------------------------------------------------
echo '</table>'

pcp_footer
pcp_mode
pcp_copyright

echo '</body>'
echo '</html>'
exit