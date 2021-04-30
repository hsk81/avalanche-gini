#!/usr/bin/env bash
# shellcheck disable=SC1090,SC2155,SC2214
###############################################################################
CMD_SCRIPT=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
###############################################################################

function cli {
    local -ag API_HOSTS=() ;
    while getopts ":a:s:hg-:" OPT "$@"
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
            s|subnet-id)
                SUBNET_ID="${OPTARG}" ;;
            g|geoip)
                GEOIP_FLAG="1" ;;
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
    usage="${BB}Usage:${NB} validators.sh" ;
    usage+=" [-a|--api-host=\${API_HOST-https://api.avax.network}]*" ;
    usage+=" [-s|--subnet-id=\${SUBNET_ID-null}]" ;
    usage+=" [-g|--geoip]" ;
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

function peers {
    for API_HOST in "${API_HOSTS[@]}" ; do
        curl --url "$API_HOST/ext/info" --compressed --no-progress-meter \
        --header 'Content-Type: application/json' \
        --header 'Accept: application/json' \
        --header 'Connection: keep-alive' \
        --data '{
            "method":"info.peers", "params":{},
            "jsonrpc":"2.0", "id":0
        }' ;
    done ;
}

function peers_map {
    jq -c '.result.peers|map({id:.nodeID,ip,version})' ;
}

function peers_merge {
    jq -c --slurp 'add|unique|sort_by(.id)' ;
}

function peers_geoip {
    if [ -n "$GEOIP_FLAG" ] ; then
        jq -c '.[]' | while read -r INFO; do
            local GEO=$(geoip "$(echo "$INFO" | jq -cr '.ip|split(":")[0]')") ;
            >&2 printf "%s %-21s => %s\n" geoip "$(echo "$INFO" | jq -cr '.ip')" \
                "$(echo "$GEO" | jq -c '.city.name+", "+.country.code+" ["+.asnum.name+"]"')" ;
            echo "$INFO" | jq -c '. += {geo:'"$GEO"'}' ;
        done | jq -cs ;
    else
        jq -c ;
    fi
}

function geoip {
    local GEO=$(geoiplookup "${1}") ;
    local GEO_CO=$(echo "$GEO" | grep Country | cut -d':' -f2 | sed -e 's/^[ \t]*//') ;
    local GEO_CI=$(echo "$GEO" | grep City    | cut -d':' -f2 | sed -e 's/^[ \t]*//') ;
    local GEO_AS=$(echo "$GEO" | grep ASNum   | cut -d':' -f2 | sed -e 's/^[ \t]*//') ;
    GEO_CO=$(echo '"'"${GEO_CO}"'"' | jq -c 'split(", ")') ;
    GEO_CI=$(echo '"'"${GEO_CI}"'"' | jq -c 'split(", ")') ;
    GEO_AS=$(echo '"'"${GEO_AS}"'"' | jq -c 'split(" ")' | jq -c '[.[0],(.[1:]|join(" "))]') ;
    GEO_CO=$(echo "${GEO_CO}" | jq -c '{
        "code":.[0],"name":.[1]
    }') ;
    GEO_CI=$(echo "${GEO_CI}" | jq -c '{
        "state":.[1],"name":.[3],"latitude":.[5]|tonumber,"longitude":.[6]|tonumber
    }') ;
    GEO_AS=$(echo "${GEO_AS}" | jq -c '{
        "code":.[0],"name":.[1]
    }') ;
    echo '{"asnum":'"$GEO_AS"',"city":'"$GEO_CI"',"country":'"$GEO_CO"'}' ;
}

###############################################################################
###############################################################################

function validators {
    curl --url "${1}/ext/P" --compressed --no-progress-meter \
    --header 'Content-Type: application/json' \
    --header 'Accept: application/json' \
    --header 'Connection: keep-alive' \
    --data '{
        "method":"platform.getCurrentValidators",
        "params":{"subnetID":'"${2}"'},
        "jsonrpc":"2.0", "id":0
    }' ;
}

function validators_map {
    jq -c '.result.validators|map({
        id:.nodeID,
        rewardAddresses:.rewardOwner.addresses|sort,
        weight:.stakeAmount|tonumber,
        delegatedWeight:(.delegators|try map(.stakeAmount|tonumber) catch [0]|add),
        startTime, endTime
    })|map(. += {
        totalWeight:(.weight+.delegatedWeight)
    })|sort_by(.totalWeight)|reverse' ;
}

###############################################################################
###############################################################################

function join {
    jq -f "$CMD_SCRIPT/join-by-id.jq" -n \
        --slurpfile f1 <(jq -c .[] "${1}") \
        --slurpfile f2 <(jq -c .[] "${2}") | \
    jq -c --slurp 'sort_by(.totalWeight)|reverse' ;
}

###############################################################################
###############################################################################

function main {
    local API_HOST="${API_HOSTS[0]}" ;
    local DATE="$(date +'%Y-%m-%d')" ;
    mkdir -p "$CMD_SCRIPT/$DATE" ;
    ##
    ## fetch { peers } > peers.json:
    ##
    local PEERS="$DATE/peers.json" ;
    echo -e "# fetch { peers } from:api-endpoint=$API_HOST" \> "$PEERS" ;
    peers "$API_HOST" | peers_map | peers_merge | peers_geoip > "$CMD_SCRIPT/$PEERS" ;
    ##
    ## fetch { validators } > validators.json:
    ##
    local VALS="$DATE/validators.json" ;
    echo -e "# fetch { validators } from:api-endpoint=$API_HOST" \> "$VALS" ;
    validators "$API_HOST" "$SUBNET_ID" | validators_map > "$CMD_SCRIPT/$VALS" ;
    ##
    ## join { peers, validators } by:id > validators-ext.json:
    ##
    local VALS_EXT="$DATE/validators-ext.json" ;
    echo -e "# join { peers, validators } by:id" \> "$VALS_EXT" ;
    join "$CMD_SCRIPT/$PEERS" "$CMD_SCRIPT/$VALS" > "$CMD_SCRIPT/$VALS_EXT" ;
    ##
    ## clean-up
    ##
    rm "$CMD_SCRIPT/$PEERS" ;
}

###############################################################################

cli "$@" && main ;

###############################################################################
###############################################################################
