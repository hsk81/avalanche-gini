#!/usr/bin/env bash
# shellcheck disable=SC1090,SC2214
###############################################################################
CMD_SCRIPT=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
###############################################################################

function cli {
    while getopts ":hm:M:g-:" OPT "$@"
    do
        if [ "$OPT" = "-" ] ; then
            OPT="${OPTARG%%=*}" ;
            OPTARG="${OPTARG#$OPT}" ;
            OPTARG="${OPTARG#=}" ;
        fi
        case "${OPT}" in
            m|min-n)
                MIN_N="${OPTARG}" ;;
            M|max-n)
                MAX_N="${OPTARG}" ;;
            g|group-by-address)
                GROUP_BY_ADDRESS="1" ;;
            h|help)
                cli_help && exit 0 ;;
            :|*)
                cli_help && exit 1 ;;
        esac
    done
    if [ -z "$MIN_N" ] ; then
        MIN_N="0" ;
    fi
    shift $((OPTIND-1)) ;
}

function cli_help {
    local usage ;
    usage="${BB}Usage:${NB} validators-list.sh" ;
    usage+=" [-m|--min-n=\${MIN_N-0}]" ;
    usage+=" [-M|--max-n=\${MAX_N}]" ;
    usage+=" [-g|--group-by-address]" ;
    usage+=" [-h|--help]" ;
    printf '%s\n' "$usage" ;
}

###############################################################################
###############################################################################

function main {
    if [ -n "$GROUP_BY_ADDRESS" ] ; then
        jq 'group_by(.rewardAddresses)|map({
            rewardAddresses:(reduce .[] as $item ([]; . + $item.rewardAddresses)),
            version:(reduce .[] as $item ([]; . + [$item.version])),
            id:(reduce .[] as $item ([]; . + [$item.id])),
            geo:(reduce .[] as $item ([]; . + [$item.geo])),
            totalWeight:(reduce .[] as $item (0; . + $item.totalWeight)),
            startTime:(reduce .[] as $item ([]; . + [$item.startTime])),
            endTime:(reduce .[] as $item ([]; . + [$item.endTime])),
            location:(reduce .[] as $item ([]; . + [{
                country:($item.geo.country.code),
                city:($item.geo.city.name),
                as:($item.geo.asnum.name)
            }])|unique|sort_by((.country|explode|map(-.)),.city))
        })' | \
        jq 'sort_by(.totalWeight)|reverse|.['"${MIN_N-0}"':'"${MAX_N}"']' | \
        jq 'map((.totalWeight|tostring)
            +";"+(.version|sort|.[0])
            +";"+(.location|map(.country+("/"+.city|sub("/N/A";""))+" ["+(.as|split(" ")[:2]|join(" "))+"]")|join(", "))
            +";"+(.geo[0].country.code)
            +";"+(.geo[0].city.name|sub("N/A";"NA"))
            +";"+(.geo[0].city.latitude|tostring)
            +";"+(.geo[0].city.longitude|tostring)
            +";"+(.geo[0].asnum.code)
            +";"+(.geo[0].asnum.name)
            +";"+(.startTime[0]|tostring)
            +";"+(.endTime[0]|tostring)
            +";"+(.rewardAddresses[0])
            +";"+(.id|sort|join(", "))
            +";")|.[]' -r ;
    else
        jq 'map(. += {
            location:([{
                country:(.geo.country.code),
                city:(.geo.city.name),
                as:(.geo.asnum.name)
            }])
        })' | \
        jq 'sort_by(.totalWeight)|reverse|.['"${MIN_N-0}"':'"${MAX_N}"']' | \
        jq 'map((.totalWeight|tostring)
            +";"+(.location|map(.country+("/"+.city|sub("/N/A";""))+" ["+(.as|split(" ")[:2]|join(" "))+"]")|join(", "))
            +";"+(.geo.country.code)
            +";"+(.geo.city.name|sub("N/A";"NA"))
            +";"+(.geo.city.latitude|tostring)
            +";"+(.geo.city.longitude|tostring)
            +";"+(.geo.asnum.code)
            +";"+(.geo.asnum.name)
            +";"+(.startTime|tostring)
            +";"+(.endTime|tostring)
            +";"+(.rewardAddresses[0])
            +";"+(.id)
            +";")|.[]' -r ;
    fi
}

###############################################################################

cli "$@" && main ;

###############################################################################
###############################################################################
