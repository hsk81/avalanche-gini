#!/usr/bin/env bash
# shellcheck disable=SC1090,SC2155,SC2214
###############################################################################
CMD_SCRIPT=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
###############################################################################
cd "$CMD_SCRIPT" || exit 1 ;

function cli {
    local -ag API_HOSTS=() ;
    while getopts ":a:s:h-:" OPT "$@"
    do
        if [ "$OPT" = "-" ] ; then
            OPT="${OPTARG%%=*}" ;
            OPTARG="${OPTARG#$OPT}" ;
            OPTARG="${OPTARG#=}" ;
        fi
        case "${OPT}" in
            a|api-host)
                local i; i="$(cli_next_index API_HOSTS)" ;
                API_HOSTS["$i"]="${OPTARG}" ;;
            h|help)
                cli_help && exit 0 ;;
            :|*)
                cli_help && exit 1 ;;
        esac
    done
    if [ -z "${API_HOSTS[*]}" ] ; then
        API_HOSTS[0]="https://api.avax.network" ;
    fi
    if [ -z "$SUBNET_ID" ] ; then
        SUBNET_ID="null" ;
    fi
    shift $((OPTIND-1)) ;
}

function cli_help {
    local usage ;
    usage="${BB}Usage:${NB} stakes.sh" ;
    usage+=" [-a|--api-host=\${API_HOST-https://api.avax.network}]*" ;
    usage+=" [-h|--help]" ;
    printf '%s\n' "$usage" ;
}

function cli_next_index {
    local -n array="$1" ;
    local empty_index=0 ;
    while true ; do
        if [ -z "${array["$empty_index"]}" ] ; then
            printf -- '%s' "$empty_index" ;
            return 0 ;
        else
            ((empty_index+=1)) ;
        fi
    done
}

###############################################################################
###############################################################################

function fetch {
    API_HOSTS="${API_HOSTS[*]}" "$CMD_SCRIPT/json/validators-fetch.sh" -g ;
}

function plot {
    source "$CMD_SCRIPT/bin/activate" \
	&& "$CMD_SCRIPT/stakes.py" -g \
	&& "$CMD_SCRIPT/stakes.py" ;
}

function commit {
    local DATE="$(date +'%Y-%m-%d')" ;
    git add "$CMD_SCRIPT/json/${DATE}" && \
    git add "$CMD_SCRIPT/image/${DATE}.svg" && \
    git add "$CMD_SCRIPT/image/${DATE}G.svg" && \
    git commit -m "AVAX: json/${DATE}" && \
    git push origin ;
}

function main {
    fetch && plot && commit ;
}

###############################################################################

cli "$@" && main ;

###############################################################################
###############################################################################
