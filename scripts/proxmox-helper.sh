#!/usr/bin/env bash

# WhisperS2T Proxmox Helper Script
# Based on community-scripts/ProxmoxVE patterns
# Author: GaboCapo
# License: MIT
# Source: https://github.com/GaboCapo/whisper-appliance

APP="WhisperS2T"
var_tags="${var_tags:-ai;speech;transcription;whisper}"
var_cpu="${var_cpu:-2}"
var_ram="${var_ram:-4096}"
var_disk="${var_disk:-20}"
var_os="${var_os:-ubuntu}"
var_version="${var_version:-22.04}"
var_unprivileged="${var_unprivileged:-1}"

# Colors and formatting
BL='\033[36m'
RD='\033[0;31m'
CM='\033[0;36m'
GN='\033[1;92m'
DGN='\033[32m'
CL='\033[m'
YW='\033[33m'
HOLD='-'
SPINNER_PID=""

# Basic functions
function msg_info() {
    echo -e "${BL}[INFO]${CL} $1"
}

function msg_ok() {
    echo -e "${GN}[OK]${CL} $1"
}

function msg_error() {
    echo -e "${RD}[ERROR]${CL} $1"
}

function header_info() {
    cat <<"EOF"
 __        ___     _                  ____ ____  _____ 
 \ \      / / |__ (_)___ _ __   ___ _ / ___|___ \|_   _|
  \ \ /\ / /| '_ \| / __| '_ \ / _ \ '_\___ \ __) | | |  
   \ V  V / | | | | \__ \ |_) |  __/ |  ___) / __/  | |  
    \_/\_/  |_| |_|_|___/ .__/ \___|_| |____/_____| |_|  
                        |_|                              

EOF
    echo -e "${CM}${APP} LXC Container Setup${CL}"
    echo -e "${BL}This will create a new ${APP} LXC Container${CL}"
}

function check_root() {
    if [[ $EUID -ne 0 ]]; then
        msg_error "This script must be run as root"
        exit 1
    fi
}

function check_pve() {
    if ! pveversion >/dev/null 2>&1; then
        msg_error "This script must be run on Proxmox VE"
        exit 1
    fi
}

function default_settings() {
    CT_TYPE="1"
    PW=""
    CT_ID=""
    HN="$NSAPP"
    DISK_SIZE="$var_disk"
    CORE_COUNT="$var_cpu"
    RAM_SIZE="$var_ram"
    NET="dhcp"
    GATE=""
    APT_CACHER=""
    APT_CACHER_IP=""
    DISABLEIP6="no"
    MTU=""
    SD=""
    NS=""
    MAC=""
    VLAN=""
    SSH="yes"
    VERB="no"
    echo_default
}

function echo_default() {
    echo -e "${DGN}Using Container Type: ${CM}$CT_TYPE${CL}"
    echo -e "${DGN}Using Container ID: ${CM}$CT_ID${CL}"
    echo -e "${DGN}Using Hostname: ${CM}$HN${CL}"
    echo -e "${DGN}Using Disk Size: ${CM}$DISK_SIZE GB${CL}"
    echo -e "${DGN}Using CPU Cores: ${CM}$CORE_COUNT${CL}"
    echo -e "${DGN}Using RAM: ${CM}$RAM_SIZE MB${CL}"
    echo -e "${DGN}Using Network: ${CM}$NET${CL}"
    echo -e "${DGN}Using SSH: ${CM}$SSH${CL}"
}

function advanced_settings() {
    while true; do
        if CT_ID=$(whiptail --backtitle "Proxmox VE Helper Scripts" --inputbox "Set Container ID" 8 58 "" --title "CONTAINER ID" 3>&1 1>&2 2>&3); then
            if [ -z "$CT_ID" ]; then
                CT_ID="$NEXTID"
                echo -e "${DGN}Container ID: ${CM}$CT_ID${CL}"
            else
                if pct status "$CT_ID" >/dev/null 2>&1; then
                    echo -e "${RD}ID $CT_ID is already in use${CL}"
                    sleep 2
                    continue
                fi
                echo -e "${DGN}Container ID: ${CM}$CT_ID${CL}"
            fi
            break
        else
            exit
        fi
    done

    if HN=$(whiptail --backtitle "Proxmox VE Helper Scripts" --inputbox "Set Hostname" 8 58 "$NSAPP" --title "HOSTNAME" 3>&1 1>&2 2>&3); then
        if [ -z "$HN" ]; then
            HN="$NSAPP"
        fi
        echo -e "${DGN}Hostname: ${CM}$HN${CL}"
    else
        exit
    fi

    if DISK_SIZE=$(whiptail --backtitle "Proxmox VE Helper Scripts" --inputbox "Set Disk Size in GB" 8 58 "$var_disk" --title "DISK SIZE" 3>&1 1>&2 2>&3); then
        if [ -z "$DISK_SIZE" ]; then
            DISK_SIZE="$var_disk"
        fi
        if ! [[ $DISK_SIZE =~ ^[0-9]+$ ]]; then
            msg_error "Disk size must be a number"
            exit
        fi
        echo -e "${DGN}Disk Size: ${CM}$DISK_SIZE GB${CL}"
    else
        exit
    fi

    if CORE_COUNT=$(whiptail --backtitle "Proxmox VE Helper Scripts" --inputbox "Set CPU Cores" 8 58 "$var_cpu" --title "CPU CORES" 3>&1 1>&2 2>&3); then
        if [ -z "$CORE_COUNT" ]; then
            CORE_COUNT="$var_cpu"
        fi
        echo -e "${DGN}CPU Cores: ${CM}$CORE_COUNT${CL}"
    else
        exit
    fi

    if RAM_SIZE=$(whiptail --backtitle "Proxmox VE Helper Scripts" --inputbox "Set RAM in MB" 8 58 "$var_ram" --title "RAM" 3>&1 1>&2 2>&3); then
        if [ -z "$RAM_SIZE" ]; then
            RAM_SIZE="$var_ram"
        fi
        echo -e "${DGN}RAM: ${CM}$RAM_SIZE MB${CL}"
    else
        exit
    fi

    if (whiptail --backtitle "Proxmox VE Helper Scripts" --title "SSH" --yesno "Enable SSH?" 10 58); then
        SSH="yes"
    else
        SSH="no"
    fi
    echo -e "${DGN}SSH: ${CM}$SSH${CL}"
}

function install_script() {
    CTID=$CT_ID
    if [ "$VERB" == "yes" ]; then set -x; fi
    if [ "$CT_TYPE" == "1" ]; then
        FEATURES="nesting=1,keyctl=1"
    else
        FEATURES="nesting=1"
    fi
    
    TEMP_DIR=$(mktemp -d)
    pushd $TEMP_DIR >/dev/null
    
    export tz="$timezone"
    export SSH_ROOT="$SSH"
    export CTID
    export PCT_OSTYPE="$var_os"
    export PCT_OSVERSION="$var_version"
    export PCT_DISK_SIZE="$DISK_SIZE"
    export PCT_OPTIONS="
    -features $FEATURES
    -hostname $HN
    -tags $var_tags
    -net0 name=eth0,bridge=vmbr0,ip=$NET$GATE$MAC$VLAN
    -cores $CORE_COUNT
    -memory $RAM_SIZE
    -unprivileged $CT_TYPE
    $SD
    $NS
    $APT_CACHER
    $DISABLEIP6
    "
    
    bash -c "$(wget -qLO - https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-install.sh)" || exit
    
    if [ "$CT_TYPE" == "0" ]; then
        PCT_OPTIONS="-template"
    fi
    
    popd >/dev/null
    
    msg_info "Started LXC Container"
    pct start $CTID
    msg_ok "Started LXC Container"
    
    lxc-attach -n $CTID -- bash -c "$(wget -qLO - https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/install-container.sh)" || exit
}

function update_script() {
    header_info
    msg_info "Updating $APP LXC"
    
    if [[ ! -f /opt/whisper-appliance/auto-update.sh ]]; then
        msg_error "No ${APP} Installation Found!"
        exit
    fi
    
    msg_info "Updating WhisperS2T to latest version"
    cd /opt/whisper-appliance
    
    if [[ -f ./auto-update.sh ]]; then
        bash ./auto-update.sh apply
    else
        git pull origin main
        systemctl restart whisper-appliance
    fi
    
    msg_ok "Updated ${APP}"
    
    IP=$(hostname -I | awk '{print $1}')
    msg_ok "Updated Successfully"
    msg_ok "WhisperS2T is reachable by going to the following URL: ${CM}http://$IP:5000${CL}"
}

# Script variables
NSAPP=$(echo "${APP,,}" | tr -d ' ')
var_install="${NSAPP}-install"
timezone=$(cat /etc/timezone)

# Main execution
clear
check_root
check_pve
header_info

# Get next available CT ID
NEXTID=$(pvesh get /cluster/nextid)
CT_ID=$NEXTID

if (whiptail --backtitle "Proxmox VE Helper Scripts" --title "SETTINGS" --yesno "Use Default Settings?" --no-button Advanced 10 58); then
    default_settings
else
    advanced_settings
fi

if (whiptail --backtitle "Proxmox VE Helper Scripts" --title "READY" --yesno "Ready to create ${APP} LXC?" 10 58); then
    msg_info "Creating LXC Container"
    install_script
    IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')
    msg_ok "LXC Container '$CTID' was successfully created, and its IP address is ${CM}$IP${CL}."
    msg_ok "WhisperS2T is reachable by going to the following URL: ${CM}http://$IP:5000${CL}"
else
    clear
    msg_error "User exited script \n"
    exit
fi