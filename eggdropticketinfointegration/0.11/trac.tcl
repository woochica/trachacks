###############################################################################
##     This trac.tcl requires Eggdrop1.6.0 or higher                         ##
##                  (c) 2007 by mvanbaak                                     ##
##                                                                           ##
###############################################################################
##                                                                           ##
## INSTALL:                                                                  ##
## ========                                                                  ##
##   1- Copy trac.tcl in your dir scripts/                                   ##
##   2- Add trac.tcl in your eggdrop.conf:                                   ##
##        source scripts/trac.tcl                                            ##
##                                                                           ##
##   For each channel you want users to use !trac cmd                        ##
##   Just type in partyline: .chanset #channel +trac                         ##
##                                                                           ##
###############################################################################
# COOKIES ARE :
# =============
# TICKETNUMBER      = %ticketnum  |    BOLD           = %bold
# STATUS            = %status     |    UNDERLINE      = %uline
# PRIORITY          = %priority   |    COLORS         = %color#,#
# SUMMARY           = %summary    |    NEW LINE       = \n
# REPORTER          = %reporter   |-----------------------------
# TICKETURL         = %url        |    !! to reset color code !!
#                                 |    !! use %color w/o args !!

# example announce:
set announce(TRACIRC) "\[%status\] %ticketnum %bold\[%priority\]%bold %summary reported by %reporter %url"

#http connection timeout (milliseconds)
set trac_timeout "25000"

#flood-control
set queue_enabled 1
#max requests
set queue_size 5
#per ? seconds
set queue_time 120

# for a channel !trac request
# set to 1 = all results will be sent publicly to the channel
# set to 0 = all results will be sent as private notice
set pub_or_not 1

# use or not the trac debugger (1=enable debug  0=disable debug)
set TRAC_DEBUG 1

# set TRAC_ALTERNATIVE 0 = use the internal tcl http 2.3 package
# set TRAC_ALTERNATIVE 1 = use the external curl 6.0+
set TRAC_ALTERNATIVE 0

# set here the location path where find curl 6.0+
set binary(CURL) ""

# set trac main url
set tracurl "http://www.phpeclipse.com"
# set the url to the tickets
set tracsearchurl "http://www.phpeclipse.com/ticket/"

#################################################################
# DO NOT MODIFY BELOW HERE UNLESS YOU KNOW WHAT YOU ARE DOING!  #
#################################################################
if { $TRAC_ALTERNATIVE == 0 } { package require http 2.3 }
setudef flag trac

bind pub -|- !trac trac_proc

set instance 0
set warn_msg 0

proc htmlcodes {tempfile} {
    set mapfile [string map {" ' & & [ ( \ / ] ) { ( } ) £ Â£ ¨ Å¡ © Â© « Â« ­ Â­ ® Â® } $tempfile]
    set mapfile [string map {´ Å½ · Â· ¹ Â¹ » Â» ¼ Å ½ Å ¾ Å¸ À Ã Á Ã Â Ã } $mapfile]
    set mapfile [string map {Ã Ã Ä Ã Å Ã Æ Ã Ç Ã È Ã É Ã Ê Ã Ë Ã Ì Ã Í Ã Î Ã Ï Ã Ð Ã Ñ Ã Ò Ã Ó Ã Ô Ã Õ Ã Ö Ã } $mapfile]
    set mapfile [string map {× Ã Ø Ã Ù Ã Ú Ã Û Ã Ü Ã Ý Ã Þ Ã ß Ã à Ã  á Ã¡ â Ã¢ ã Ã£ ä Ã¤ å Ã¥ æ Ã¦ ç Ã§ è Ã¨ é Ã© ê Ãª } $mapfile]
    set mapfile [string map {ë Ã« ì Ã¬ í Ã­ î Ã® ï Ã¯ ð Ã° ñ Ã± ò Ã² ó Ã³ ô Ã´ õ Ãµ ö Ã¶ ÷ Ã· ø Ã¸ ù Ã¹ ú Ãº û Ã» ü Ã¼ ý Ã½ þ Ã¾ } $mapfile]
    set mapfile [string map {  "" & "&"} $mapfile]
    return $mapfile
}

proc channel_check_trac { chan } {
    foreach setting [channel info $chan] {
        if {[regexp -- {^[\+-]} $setting]} {
            if {![string compare "+trac" $setting]} {
                set permission 1
                break
            } else {
                set permission 0
            }
        }
    }
    return $permission
}

proc replacevar {strin what withwhat} {
    set output $strin
    set replacement $withwhat
    set cutpos 0
    while { [string first $what $output] != -1 } {
        set cutstart [expr [string first $what $output] - 1]
        set cutstop  [expr $cutstart + [string length $what] + 1]
        set output [string range $output 0 $cutstart]$replacement[string range $output $cutstop end]
    }
    return $output
}

proc findnth {strin what count} {
     set ret 0
     for {set x 0} {$x < $count} {incr x} {
         set ret [string first $what $strin [expr $ret + 1]]
     }
     return $ret
}

proc trac_proc { nick uhost handle chan arg } {
    global cast_linelimit instance queue_size queue_time queue_enabled trac_timeout TRAC_DEBUG pub_or_not announce random warn_msg binary TRAC_ALTERNATIVE tracurl tracsearchurl
    # channel_check permission
    set permission_result [channel_check_trac $chan]
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG permission_result == $permission_result" }
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG instance == $instance" }
    if { $permission_result == 0} { return }
    # public or private
    if {$pub_or_not == 1 } { set toput "PRIVMSG $chan" } else { set toput "NOTICE $nick" }
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG toput_result == $toput" }
    # if no arg passed, show help
    if {$arg == ""} {
        if { $TRAC_ALTERNATIVE == 0 } { set using "Http 2.3+" } else { set using "Curl 6.0+" }
        if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG no arg passed, show help" }
        puthelp "$toput :trac info script \002v0.0.1\002 by mvanbaak using \002$using\002"
        puthelp "$toput :\002Syntax: !trac <ticket number>\002  exemple: !trac 13"
        return
    }

    #flood-control
    if { $queue_enabled == 1 } {
       #flooded?
       if { $instance >= $queue_size } {
          if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG flood detected" }
          if { $warn_msg == 0 } {
             set warn_msg 1
             putquick "$toput :Flood-Control: Request for \"$arg\" from user \"$nick\" will not be answered."
             putquick "$toput :Flood-Control: Maximum of $queue_size requests every $queue_time seconds."
             utimer 120 wmsg
          }
          return
       }
       incr instance
       if { $TRAC_DEBUG == 1 } { putlog "TRAC_DEBUG new instance == $instance" }
       utimer [set queue_time] decr_inst
    }

    # initial search
    set searchString [string map {\  %20 & %26 , %2C . %20} $arg]
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG searchString: \"$searchString\"" }
    if { $TRAC_ALTERNATIVE == 0 } {
        set page [::http::config -useragent "MSIE 6.0"]
        if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG ${tracsearchurl}$searchString" }
        set page [::http::geturl ${tracsearchurl}$searchString -timeout $trac_timeout]
        if { [::http::status $page] == "timeout" } {
            puthelp "$toput :\002Connection to ${tracurl} timed out while doing initial search.\002"
            ::http::Finish $page
            return
        }
        set html [::http::data $page]
        ::http::Finish $page
    } else {
        catch { exec $binary(CURL) "${tracsearchurl}$searchString" } html
    }

    set output $announce(TRACIRC)


    # collect output
    set ticketnum "N/A" ; set priority "N/A" ; set summary "N/A"
    set status "N/A" ; set name "N/A"

    ## get ticetnum
    if [regexp {Ticket (.*?) <span} $html dummy ticketnum] {
        set pos [expr [string last # $ticketnum] + 1]
        set ticketnum [string range $ticketnum $pos end]
	regsub -all {[ \r\t\n]+} $ticketnum "" ticketnum
        set ticketnum [htmlcodes $ticketnum]
    }
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG ticketnum == $ticketnum" }
    ## get status
    if [regexp {<span class="status">(.*?)</span>} $html dummy status] {
        set pos [expr [string last > $status] + 1]
        set status [string range $status $pos end]
        set status [htmlcodes $status]
        set status [string map {( ""} $status]
        set status [string map {) ""} $status]
    }
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG status == $status" }
    ## get summary
    if [regexp {<h2 class="summary searchable">(.*?)</h2>} $html dummy summary] {
        set pos [expr [string last > $summary] + 1]
        set summary [string range $summary $pos end]
        set summary [htmlcodes $summary]
    }
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG summary == $summary" }
    ## get priority
    if [regexp {<td headers="h_priority">(.*?)</td>} $html dummy priority] {
        set pos [expr [string last > $priority] +1 ]
        set priority [string range $priority $pos end]
	regsub -all {[ \r\t\n]+} $priority "" priority
        set priority [htmlcodes $priority]
    }
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG priority == $priority" }
    ## get reporter
    if [regexp {<td headers="h_reporter" class="searchable">(.*?)</td>} $html dummy reporter] {
        set pos [expr [string last > $reporter] +1 ]
        set reporter [string range $reporter $pos end]
        string trim $reporter
        set reporter [htmlcodes $reporter]
    }
    if {$TRAC_DEBUG == 1} { putlog "TRAC_DEBUG reporter == $reporter" }

    ## output results

    set output [replacevar $output "%bold" "\002"]
    set output [replacevar $output "%color" "\003"]
    set output [replacevar $output "%uline" "\037"]
    set output [replacevar $output "%ticketnum" $ticketnum]
    set output [replacevar $output "%status" $status]
    set output [replacevar $output "%summary" $summary]
    set output [replacevar $output "%priority" $priority]
    set output [replacevar $output "%reporter" $reporter]
    set output [replacevar $output "%url" ${tracsearchurl}$searchString]
    foreach line [split $output "\n"] {
        puthelp "$toput :$line"
    }

}

proc decr_inst { } {
     global TRAC_DEBUG instance
     if { $instance > 0 } { incr instance -1 }
     if { $TRAC_DEBUG == 1 } { putlog "TRAC_DEBUG instance decreased by timer to: $instance" }
}

proc wmsg { } {
     global warn_msg
     set warn_msg 0
}
putlog "TRAC info version 0.0.2 loaded"
